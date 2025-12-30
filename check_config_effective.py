#!/usr/bin/env python3
"""
检查 rdagent 配置修改是否生效
"""

import sys
from pathlib import Path

print("=" * 60)
print("🔍 检查 RD-Agent 配置是否生效")
print("=" * 60)

# 1. 检查 Python 路径
print(f"\n📍 Python 路径: {sys.executable}")
print(f"📍 当前工作目录: {Path.cwd()}")

# 2. 检查 rdagent 导入路径
try:
    import rdagent
    module_path = Path(rdagent.__file__).parent
    print(f"\n📦 rdagent 模块路径: {module_path}")

    # 检查是源码还是安装包
    if "site-packages" in str(module_path):
        print("⚠️  rdagent 从 site-packages 导入（已安装版本）")
        print("   修改源码不会生效，需要重新安装！")
        needs_reinstall = True
    elif "rdagent" in str(module_path) and "github" in str(module_path).lower():
        print("✅ rdagent 从源码目录导入（开发模式）")
        print("   修改源码会立即生效")
        needs_reinstall = False
    else:
        print(f"❓ 未知路径类型: {module_path}")
        needs_reinstall = None
except ImportError:
    print("\n❌ rdagent 模块未安装")
    needs_reinstall = True

# 3. 检查实际的配置文件
print(f"\n📄 源码配置文件: {Path.cwd()}/rdagent/oai/llm_conf.py")
try:
    with open("rdagent/oai/llm_conf.py") as f:
        source_content = f.read()
        if "ollama/bge-m3" in source_content:
            print("✅ 源码文件包含 ollama/bge-m3 配置")
        else:
            print("❌ 源码文件不包含 ollama/bge-m3 配置")
except Exception as e:
    print(f"❌ 无法读取源码文件: {e}")

# 4. 检查导入的配置
print(f"\n🔧 导入的配置:")
try:
    from rdagent.oai.llm_conf import LLM_SETTINGS

    print(f"  embedding_model: {LLM_SETTINGS.embedding_model}")
    print(f"  embedding_max_str_num: {LLM_SETTINGS.embedding_max_str_num}")
    print(f"  use_embedding_cache: {LLM_SETTINGS.use_embedding_cache}")
    print(f"  dump_embedding_cache: {LLM_SETTINGS.dump_embedding_cache}")
    print(f"  embedding_openai_base_url: {LLM_SETTINGS.embedding_openai_base_url}")

    # 验证配置是否匹配
    if LLM_SETTINGS.embedding_model == "ollama/bge-m3":
        print("\n✅ 配置已生效！BGE-M3 配置正在使用")
        config_effective = True
    else:
        print(f"\n❌ 配置未生效！当前使用: {LLM_SETTINGS.embedding_model}")
        config_effective = False

except ImportError as e:
    print(f"❌ 无法导入配置: {e}")
    config_effective = False

# 5. 结论和建议
print("\n" + "=" * 60)
print("📋 结论和建议")
print("=" * 60)

if needs_reinstall and not config_effective:
    print("\n⚠️  检测到问题：")
    print("   1. rdagent 从 site-packages 导入")
    print("   2. 配置修改未生效")
    print("\n🔧 解决方法：")
    print("   conda activate Quant-env-3.11")
    print("   cd /Users/berton/Github/RD-Agent")
    print("   pip install -e . --no-deps")
    print("\n   然后重新运行 RD-Agent")
elif not needs_reinstall and config_effective:
    print("\n✅ 一切正常！")
    print("   rdagent 以开发模式运行")
    print("   配置修改已生效")
    print("   可以直接使用 RD-Agent")
elif not needs_reinstall and not config_effective:
    print("\n⚠️  rdagent 是开发模式，但配置似乎未应用")
    print("   请检查源码文件是否正确修改")
elif needs_reinstall and config_effective:
    print("\n✅ 配置已生效，即使是从 site-packages 导入")
    print("   可能已经重新安装过")

print("\n" + "=" * 60)
