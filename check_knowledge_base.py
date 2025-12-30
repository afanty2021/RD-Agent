#!/usr/bin/env python3
"""
检查知识库状态和向量维度
"""

import os
import pickle
import sys
from pathlib import Path

def check_pickle_file(file_path):
    """检查 pickle 文件中的向量维度"""
    try:
        with open(file_path, 'rb') as f:
            data = pickle.load(f)

        print(f"  ✅ 文件可读取: {file_path}")

        # 检查是否是知识库对象
        if hasattr(data, 'vector_df'):
            df = data.vector_df
            if not df.empty and 'embedding' in df.columns:
                first_embedding = df['embedding'].iloc[0]
                dim = len(first_embedding) if hasattr(first_embedding, '__len__') else 'N/A'
                print(f"  📊 向量维度: {dim}")
                print(f"  📦 记录数: {len(df)}")
                return dim
        elif isinstance(data, dict) and 'embeddings' in data:
            embeddings = data['embeddings']
            if embeddings:
                first_emb = embeddings[0] if isinstance(embeddings, list) else list(embeddings.values())[0]
                dim = len(first_emb) if hasattr(first_emb, '__len__') else 'N/A'
                print(f"  📊 向量维度: {dim}")
                print(f"  📦 记录数: {len(embeddings)}")
                return dim

        print(f"  ⚠️  未找到向量数据")
        return None

    except Exception as e:
        print(f"  ❌ 读取失败: {e}")
        return None

def main():
    print("=" * 60)
    print("🔍 检查知识库和缓存状态")
    print("=" * 60)

    # 1. 检查 .env 中的知识库配置
    print("\n📋 知识库配置:")
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "KNOWLEDGE_BASE_PATH" in line and "=" in line and not line.strip().startswith("#"):
                    print(f"  {line.strip()}")

    # 2. 检查 Ollama 缓存
    print("\n💾 Ollama 缓存:")
    cache_dir = Path("./ollama_cache")
    if cache_dir.exists():
        files = list(cache_dir.rglob("*"))
        print(f"  ✅ 缓存目录存在，包含 {len(files)} 个文件")
    else:
        print("  ℹ️  缓存目录不存在")

    # 3. 检查 prompt_cache.db
    print("\n🗄️  Prompt 缓存:")
    prompt_cache = Path("./prompt_cache.db")
    if prompt_cache.exists():
        size_mb = prompt_cache.stat().st_size / (1024*1024)
        print(f"  ✅ 存在，大小: {size_mb:.2f} MB")
    else:
        print("  ℹ️  不存在")

    # 4. 检查知识库文件
    print("\n📚 知识库文件:")

    knowledge_paths = []
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if "KNOWLEDGE_BASE_PATH" in line and "=" in line and not line.strip().startswith("#"):
                    path_str = line.split("=", 1)[1].strip()
                    # 展开 ~
                    path_str = os.path.expanduser(path_str)
                    knowledge_paths.append(path_str)

    # 检查每个知识库文件
    dims = []
    for path_str in knowledge_paths:
        path = Path(path_str)
        print(f"\n  📄 {path}")
        if path.exists():
            dim = check_pickle_file(path)
            if dim:
                dims.append(dim)
        else:
            print(f"  ℹ️  文件不存在")

    # 5. 检查 log 目录
    print("\n📁 Log 目录中的缓存文件:")
    log_dir = Path("./log")
    if log_dir.exists():
        pkl_files = list(log_dir.rglob("*.pkl"))
        print(f"  找到 {len(pkl_files)} 个 .pkl 文件")

        if pkl_files:
            print("\n  最近修改的 5 个文件:")
            for f in sorted(pkl_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                mtime = f.stat().st_mtime
                import datetime
                dt = datetime.datetime.fromtimestamp(mtime)
                print(f"    {f.name} ({dt.strftime('%Y-%m-%d %H:%M')})")

    # 6. 总结和建议
    print("\n" + "=" * 60)
    print("📊 诊断结果")
    print("=" * 60)

    if dims:
        unique_dims = set(dims)
        if len(unique_dims) > 1:
            print(f"\n❌ 发现问题: 向量维度不一致！")
            for d in unique_dims:
                print(f"  - {d} 维向量")
            print("\n💡 需要运行: bash fix_embedding_dimension.sh")
        elif 1024 in unique_dims:
            print(f"\n✅ 向量维度正确: 1024 (BGE-M3)")
        else:
            print(f"\n⚠️  向量维度不是 1024: {unique_dims}")
            print("\n💡 需要运行: bash fix_embedding_dimension.sh")
    else:
        print("\nℹ️  未找到知识库文件或无法读取")
        print("💡 这是正常的，如果这是第一次运行")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
