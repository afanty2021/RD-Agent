#!/usr/bin/env python3
"""
查找包含 embedding 向量的文件
"""

import pickle
import os
from pathlib import Path

def has_embedding_data(file_path):
    """快速检查文件是否包含 embedding"""
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)

        # 快速检查：是否有 vector_base 或 embedding
        if hasattr(data, 'vector_base'):
            return True, 'vector_base'
        if hasattr(data, 'graph'):
            return True, 'graph'

        # 检查字典
        if isinstance(data, dict):
            if 'vector_base' in data or 'embedding' in data:
                return True, 'dict_with_vectors'

        return False, None
    except:
        return False, None

def get_embedding_dim(file_path):
    """获取向量维度"""
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)

        # 尝试各种方式获取向量
        if hasattr(data, 'vector_base'):
            vb = data.vector_base
            if hasattr(vb, 'vector_df') and not vb.vector_df.empty:
                emb = vb.vector_df['embedding'].iloc[0]
                return len(emb) if hasattr(emb, '__len__') else None

        if hasattr(data, 'graph'):
            graph = data.graph
            if hasattr(graph, 'vector_base'):
                vb = graph.vector_base
                if hasattr(vb, 'vector_df') and not vb.vector_df.empty:
                    emb = vb.vector_df['embedding'].iloc[0]
                    return len(emb) if hasattr(emb, '__len__') else None

        return None
    except:
        return None

def main():
    print("=" * 60)
    print("🔍 查找包含 Embedding 向量的文件")
    print("=" * 60)

    log_dir = Path("./log")
    if not log_dir.exists():
        print("❌ log 目录不存在")
        return

    # 扫描所有 .pkl 文件
    pkl_files = list(log_dir.rglob("*.pkl"))
    print(f"\n📁 扫描 {len(pkl_files)} 个 .pkl 文件...\n")

    vector_files = []
    checked = 0

    for file_path in pkl_files:
        has_vec, reason = has_embedding_data(file_path)
        if has_vec:
            vector_files.append((file_path, reason))
            checked += 1

            if checked <= 20:  # 只显示前20个
                print(f"✅ {file_path.relative_to(log_dir)}")
                print(f"   原因: {reason}")

    print(f"\n📊 统计:")
    print(f"  总文件数: {len(pkl_files)}")
    print(f"  包含向量: {len(vector_files)}")

    if vector_files:
        print(f"\n🔍 检查向量维度（前10个）:")

        dim_summary = {}
        for file_path, reason in vector_files[:10]:
            dim = get_embedding_dim(file_path)
            if dim:
                dim_summary[dim] = dim_summary.get(dim, 0) + 1
                print(f"  {file_path.name}: {dim} 维")

        if dim_summary:
            print(f"\n📋 维度分布:")
            for dim, count in sorted(dim_summary.items()):
                print(f"  {dim} 维: {count} 个文件")

            if any(d != 1024 for d in dim_summary.keys()):
                print("\n❌ 发现问题: 有非 1024 维的向量！")
                print("\n💡 需要清理这些文件")
            else:
                print("\n✅ 所有向量都是 1024 维")
        else:
            print("\n⚠️  无法读取向量维度")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
