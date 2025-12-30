#!/usr/bin/env python3
"""
验证 Ollama BGE-M3 配置
检查 RD-Agent 配置文件和环境变量
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """检查 .env 文件配置"""
    print("=" * 60)
    print("📋 .env 文件配置检查")
    print("=" * 60)

    env_path = Path.cwd() / ".env"
    if not env_path.exists():
        print("❌ .env 文件不存在")
        return False

    print(f"✅ .env 文件路径: {env_path}")

    # 读取关键配置
    configs = {}
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("EMBEDDING_") or line.startswith("LITELLM_EMBEDDING_"):
                if "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    configs[key] = value

    print("\n🔧 Embedding 相关配置:")
    print(f"  EMBEDDING_OPENAI_API_KEY: {configs.get('EMBEDDING_OPENAI_API_KEY', '未设置')}")
    print(f"  EMBEDDING_OPENAI_BASE_URL: {configs.get('EMBEDDING_OPENAI_BASE_URL', '未设置')}")
    print(f"  LITELLM_EMBEDDING_MODEL: {configs.get('LITELLM_EMBEDDING_MODEL', '未设置')}")
    print(f"  prompt_cache_path: {configs.get('prompt_cache_path', '未设置')}")

    # 验证配置
    print("\n✅ 配置验证:")
    checks = []

    # 检查 API Key
    if configs.get('EMBEDDING_OPENAI_API_KEY') == 'ollama':
        print("  ✅ API Key 设置正确 (ollama)")
        checks.append(True)
    else:
        print("  ❌ API Key 应设置为 'ollama'")
        checks.append(False)

    # 检查 Base URL
    if 'localhost:11434' in configs.get('EMBEDDING_OPENAI_BASE_URL', ''):
        print("  ✅ Base URL 指向本地 Ollama")
        checks.append(True)
    else:
        print("  ❌ Base URL 应指向 http://localhost:11434")
        checks.append(False)

    # 检查模型
    if 'bge-m3' in configs.get('LITELLM_EMBEDDING_MODEL', '').lower():
        print("  ✅ 模型设置为 BGE-M3")
        checks.append(True)
    else:
        print("  ⚠️  模型未设置为 bge-m3")
        checks.append(False)

    return all(checks)

def check_llm_conf():
    """检查 llm_conf.py 配置"""
    print("\n" + "=" * 60)
    print("🔧 llm_conf.py 配置检查")
    print("=" * 60)

    conf_path = Path.cwd() / "rdagent" / "oai" / "llm_conf.py"
    if not conf_path.exists():
        print("❌ llm_conf.py 文件不存在")
        return False

    print(f"✅ 配置文件: {conf_path}")

    # 读取配置文件
    with open(conf_path) as f:
        content = f.read()

    # 检查关键配置
    print("\n🔍 关键配置检查:")

    checks = []

    if 'embedding_model: str = "ollama/bge-m3"' in content:
        print("  ✅ embedding_model 已设置为 ollama/bge-m3")
        checks.append(True)
    else:
        print("  ❌ embedding_model 未正确设置")
        checks.append(False)

    if 'embedding_max_str_num: int = 100' in content:
        print("  ✅ 批量大小已优化为 100")
        checks.append(True)
    else:
        print("  ⚠️  批量大小未优化")
        checks.append(False)

    if 'use_embedding_cache: bool = True' in content:
        print("  ✅ Embedding 缓存已启用")
        checks.append(True)
    else:
        print("  ❌ Embedding 缓存未启用")
        checks.append(False)

    if 'dump_embedding_cache: bool = True' in content:
        print("  ✅ 缓存转储已启用")
        checks.append(True)
    else:
        print("  ⚠️  缓存转储未启用")
        checks.append(False)

    if 'embedding_openai_base_url: str = "http://localhost:11434"' in content:
        print("  ✅ Base URL 配置正确")
        checks.append(True)
    else:
        print("  ❌ Base URL 未配置")
        checks.append(False)

    return all(checks)

def check_ollama_service():
    """检查 Ollama 服务状态"""
    print("\n" + "=" * 60)
    print("🔄 Ollama 服务检查")
    print("=" * 60)

    import subprocess

    # 检查服务是否运行
    try:
        result = subprocess.run(
            ["pgrep", "-x", "ollama"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("✅ Ollama 服务正在运行")
        else:
            print("❌ Ollama 服务未运行")
            print("   请执行: ollama serve")
            return False
    except:
        print("⚠️  无法检查 Ollama 服务状态")

    # 检查 BGE-M3 模型
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True
        )
        if "bge-m3" in result.stdout:
            print("✅ BGE-M3 模型已安装")

            # 提取模型大小
            for line in result.stdout.split('\n'):
                if 'bge-m3' in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ BGE-M3 模型未安装")
            print("   请执行: ollama pull bge-m3")
            return False
    except:
        print("⚠️  无法检查模型列表")

    # 测试 API
    print("\n🧪 测试 Embedding API...")
    try:
        import json
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:11434/api/embeddings',
             '-d', '{"model": "bge-m3", "prompt": "测试"}'],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            response = json.loads(result.stdout)
            if 'embedding' in response:
                embedding = response['embedding']
                print(f"✅ API 测试成功")
                print(f"   向量维度: {len(embedding)}")
                return True
            else:
                print("❌ API 响应格式错误")
                return False
        else:
            print("❌ API 请求失败")
            return False
    except Exception as e:
        print(f"❌ API 测试异常: {e}")
        return False

def check_cache_dir():
    """检查缓存目录"""
    print("\n" + "=" * 60)
    print("💾 缓存目录检查")
    print("=" * 60)

    cache_path = Path.cwd() / "ollama_cache"

    if not cache_path.exists():
        print(f"⚠️  缓存目录不存在: {cache_path}")
        print(f"   正在创建...")
        try:
            cache_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 缓存目录已创建: {cache_path}")
        except Exception as e:
            print(f"❌ 创建缓存目录失败: {e}")
            return False
    else:
        print(f"✅ 缓存目录存在: {cache_path}")

    # 检查写入权限
    test_file = cache_path / ".test"
    try:
        test_file.touch()
        test_file.unlink()
        print("✅ 缓存目录可写")
        return True
    except:
        print("❌ 缓存目录不可写")
        return False

def main():
    print("\n" + "=" * 60)
    print("🚀 RD-Agent Ollama BGE-M3 配置验证")
    print("=" * 60)
    print(f"📍 工作目录: {Path.cwd()}")
    print(f"🖥️  系统: {sys.platform}")
    print("=" * 60)

    results = {}

    # 运行所有检查
    results['env'] = check_env_file()
    results['conf'] = check_llm_conf()
    results['cache'] = check_cache_dir()
    results['service'] = check_ollama_service()

    # 总结
    print("\n" + "=" * 60)
    print("📊 验证结果总结")
    print("=" * 60)

    print(f"\n  .env 配置:      {'✅ 通过' if results['env'] else '❌ 失败'}")
    print(f"  llm_conf.py:    {'✅ 通过' if results['conf'] else '❌ 失败'}")
    print(f"  缓存目录:       {'✅ 通过' if results['cache'] else '❌ 失败'}")
    print(f"  Ollama 服务:    {'✅ 通过' if results['service'] else '❌ 失败'}")

    all_passed = all(results.values())

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有检查通过！配置完成！")
        print("\n💡 下一步:")
        print("   1. 运行 RD-Agent 任务")
        print("   2. BGE-M3 将自动用于 embedding")
        print("   3. 缓存将自动保存到 ./ollama_cache/")
    else:
        print("⚠️  部分检查失败，请根据上述提示修复")

    print("=" * 60 + "\n")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
