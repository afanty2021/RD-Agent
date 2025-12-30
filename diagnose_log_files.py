#!/usr/bin/env python3
"""
深度诊断 log 目录中的向量文件
"""

import os
import pickle
from pathlib import Path
import sys

def check_file_embedding_dim(file_path):
    """检查单个文件的向量维度"""
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)

        # 检查各种可能的数据结构
        if hasattr(data, 'vector_df'):
            df = data.vector_df
            if not df.empty and 'embedding' in df.columns:
                emb = df['embedding'].iloc[0]
                return len(emb) if hasattr(emb, '__len__') else None

        elif hasattr(data, 'graph') and hasattr(data.graph, 'vector_base'):
            vb = data.graph.vector_base
            if hasattr(vb, 'vector_df') and not vb.vector_df.empty:
                emb = vb.vector_df['embedding'].iloc[0]
                return len(emb) if hasattr(emb, '__len__') else None

        elif isinstance(data, dict):
            if 'vector_df' in data:
                df = data['vector_df']
                if not df.empty and 'embedding' in df.columns:
                    emb = df['embedding'].iloc[0]
                    return len(emb) if hasattr(emb, '__len__') else None
            elif 'embeddings' in data:
                embeddings = data['embeddings']
                if embeddings and isinstance(embeddings, list):
                    return len(embeddings[0]) if hasattr(embeddings[0], '__len__') else None

        return None
    except Exception as e:
        return None

def main():
    print("=" * 60)
    print("🔍 深度诊断 Log 目录中的向量文件")
    print("=" * 60)

    log_dir = Path("./log")
    if not log_dir.exists():
        print("❌ log 目录不存在")
        return

    # 找到所有 .pkl 文件
    pkl_files = list(log_dir.rglob("*.pkl"))
    print(f"\n📁 找到 {len(pkl_files)} 个 .pkl 文件")

    if not pkl_files:
        print("ℹ️  没有找到 .pkl 文件")
        return

    # 按修改时间排序，检查最近的文件
    sorted_files = sorted(pkl_files, key=lambda x: x.stat().st_mtime, reverse=True)

    print("\n🔍 检查最近修改的 10 个文件:")

    dim_count = {}
    problem_files = []

    for i, file_path in enumerate(sorted_files[:10], 1):
        print(f"\n{i}. {file_path.relative_to(log_dir)}")

        # 文件大小
        size_kb = file_path.stat().st_size / 1024
        print(f"   大小: {size_kb:.2f} KB")

        # 检查向量维度
        dim = check_file_embedding_dim(file_path)
        if dim:
            print(f"   📊 向量维度: {dim}")
            dim_count[dim] = dim_count.get(dim, 0) + 1

            if dim != 1024:
                print(f"   ⚠️  维度不是 1024 (BGE-M3)")
                problem_files.append(file_path)
        else:
            print(f"   ℹ️  未找到向量数据")

    # 总结
    print("\n" + "=" * 60)
    print("📊 诊断结果")
    print("=" * 60)

    if dim_count:
        print("\n发现的向量维度:")
        for dim, count in sorted(dim_count.items()):
            print(f"  {dim} 维: {count} 个文件")

        if any(d != 1024 for d in dim_count.keys()):
            print("\n❌ 问题: 发现非 1024 维向量！")
            print("\n💡 建议操作:")
            print("   1. 运行清理脚本: bash fix_embedding_dimension.sh")
            print("   2. 或手动删除问题目录")
        else:
            print("\n✅ 所有向量都是 1024 维 (BGE-M3)")
    else:
        print("\nℹ️  未找到向量数据")

    # 统计各目录的文件数
    print("\n📂 各会话目录的文件数:")
    session_dirs = sorted([d for d in log_dir.iterdir() if d.is_dir()], key=lambda x: x.stat().st_mtime, reverse=True)[:5]

    for session_dir in session_dirs:
        pkl_count = len(list(session_dir.rglob("*.pkl")))
        import datetime
        dt = datetime.datetime.fromtimestamp(session_dir.stat().st_mtime)
        print(f"  {session_dir.name}: {pkl_count} 个文件 ({dt.strftime('%m-%d %H:%M')})")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
