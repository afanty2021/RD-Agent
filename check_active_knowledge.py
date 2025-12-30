#!/usr/bin/env python3
"""
检查正在使用的知识库文件
根据 .env 配置定位实际文件
"""

import os
from pathlib import Path

def expand_path(path_str):
    """展开路径中的 ~ 和环境变量"""
    path_str = os.path.expanduser(path_str)
    path_str = os.path.expandvars(path_str)
    return path_str

def main():
    print("=" * 60)
    print("🔍 检查配置的知识库文件")
    print("=" * 60)

    # 读取 .env 配置
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env 文件不存在")
        return

    knowledge_paths = {}

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if "KNOWLEDGE_BASE_PATH" in line and "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                knowledge_paths[key] = value.strip()

    print("\n📋 .env 中配置的知识库路径:")
    for key, path in knowledge_paths.items():
        expanded = expand_path(path)
        print(f"\n  {key}:")
        print(f"    配置值: {path}")
        print(f"    完整路径: {expanded}")

        # 检查文件是否存在
        full_path = Path(expanded)
        if full_path.exists():
            size_mb = full_path.stat().st_size / (1024*1024)
            print(f"    状态: ✅ 存在 ({size_mb:.2f} MB)")

            # 尝试读取并检查向量维度
            try:
                import pickle
                with open(full_path, 'rb') as f:
                    data = pickle.load(f)

                # 检查向量
                if hasattr(data, 'vector_df'):
                    df = data.vector_df
                    if not df.empty and 'embedding' in df.columns:
                        first_emb = df['embedding'].iloc[0]
                        dim = len(first_emb) if hasattr(first_emb, '__len__') else 'N/A'
                        print(f"    向量维度: {dim}")
                        print(f"    记录数: {len(df)}")
                else:
                    print(f"    数据类型: {type(data)}")

            except ImportError as e:
                print(f"    ⚠️  无法读取 (缺少依赖): {e}")
            except Exception as e:
                print(f"    ❌ 读取失败: {e}")

        else:
            print(f"    状态: ❌ 不存在")

    # 检查当前正在运行的任务路径
    print("\n" + "=" * 60)
    print("🔄 当前运行状态")
    print("=" * 60)

    # 从错误信息中看到的路径
    running_session = "2025-12-29_02-05-25-325649"
    session_path = Path(f"./log/{running_session}")

    if session_path.exists():
        print(f"\n📁 最近运行会话: {running_session}")

        # 查找可能的知识库快照
        for pkl_file in session_path.rglob("*knowledge*.pkl"):
            size_kb = pkl_file.stat().st_size / 1024
            print(f"  发现: {pkl_file.relative_to(session_path)} ({size_kb:.2f} KB)")

    print("\n" + "=" * 60)
    print("💡 建议")
    print("=" * 60)

    print("\n根据错误分析，问题可能是:")
    print("  1. 旧的内存知识库（未持久化）")
    print("  2. 隐藏的知识库文件")
    print("  3. 动态生成的缓存")
    print("\n🔧 推荐操作:")
    print("  1. 清理所有缓存: bash fix_embedding_dimension.sh")
    print("  2. 重启 RD-Agent 任务")
    print("  3. 让系统重新生成 1024 维向量")

if __name__ == "__main__":
    main()
