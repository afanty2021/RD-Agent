#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Embedding API 测试脚本

用于诊断RD-Agent中embedding API配置和调用是否正常。
"""

import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def test_imports():
    """测试必要的库是否已安装"""
    print("=" * 60)
    print("1. 测试库导入")
    print("=" * 60)

    try:
        import litellm
        # litellm 可能没有 __version__ 属性
        try:
            version = litellm.__version__
        except AttributeError:
            version = "未知版本"
        print("✓ litellm 已安装, 版本:", version)
    except ImportError as e:
        print("✗ litellm 未安装:", e)
        return False

    try:
        import numpy as np
        print("✓ numpy 已安装")
    except ImportError as e:
        print("✗ numpy 未安装:", e)
        return False

    print()
    return True


def test_env_config():
    """测试环境变量配置"""
    print("=" * 60)
    print("2. 测试环境变量配置")
    print("=" * 60)

    # 检查关键配置
    configs = {
        "OPENAI_API_KEY": "OpenAI API Key",
        "OPENAI_API_BASE": "OpenAI API Base",
        "EMBEDDING_OPENAI_API_KEY": "Embedding API Key",
        "EMBEDDING_OPENAI_BASE_URL": "Embedding Base URL",
        "LITELLM_EMBEDDING_MODEL": "LiteLLM Embedding Model",
        "DEEPSEEK_API_KEY": "DeepSeek API Key",
    }

    for env_var, desc in configs.items():
        value = os.getenv(env_var)
        if value:
            # 隐藏API密钥的敏感部分
            if "KEY" in env_var or "SECRET" in env_var:
                display_value = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            else:
                display_value = value
            print(f"✓ {desc} ({env_var}): {display_value}")
        else:
            print(f"✗ {desc} ({env_var}): 未设置")

    print()
    return True


def test_rdagent_settings():
    """测试RD-Agent的LLM配置"""
    print("=" * 60)
    print("3. 测试RD-Agent LLM配置")
    print("=" * 60)

    try:
        from rdagent.oai.llm_conf import LLM_SETTINGS, LITELLM_SETTINGS

        print(f"✓ Backend: {LLM_SETTINGS.backend}")
        print(f"✓ Chat Model: {LLM_SETTINGS.chat_model}")
        print(f"✓ Embedding Model: {LLM_SETTINGS.embedding_model}")
        print(f"✓ Use Embedding Cache: {LLM_SETTINGS.use_embedding_cache}")
        print(f"✓ Dump Embedding Cache: {LLM_SETTINGS.dump_embedding_cache}")

        # 检查 LiteLLM 特定配置
        print(f"✓ LiteLLM Env Prefix: {LITELLM_SETTINGS.model_fields['env_prefix'].default}")

    except Exception as e:
        print(f"✗ 加载RD-Agent配置失败: {e}")
        return False

    print()
    return True


def test_litellm_embedding():
    """直接测试LiteLLM的embedding功能"""
    print("=" * 60)
    print("4. 测试LiteLLM Embedding API调用")
    print("=" * 60)

    try:
        from litellm import embedding
        from rdagent.oai.llm_conf import LLM_SETTINGS

        model_name = LLM_SETTINGS.embedding_model
        test_texts = ["这是一个测试文本", "This is a test text"]

        print(f"使用模型: {model_name}")
        print(f"测试文本: {test_texts}")

        print("正在调用embedding API...")
        response = embedding(
            model=model_name,
            input=test_texts,
        )

        print(f"✓ Embedding API调用成功!")
        print(f"  - 返回数量: {len(response.data)}")
        print(f"  - 向量维度: {len(response.data[0]['embedding'])}")
        print(f"  - 模型: {response.model}")
        print(f"  - 用途: {response.usage}")

        return True, response.data[0]['embedding']

    except Exception as e:
        print(f"✗ Embedding API调用失败: {e}")
        print(f"  错误类型: {type(e).__name__}")
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()
        return False, None


def test_rdagent_backend():
    """测试RD-Agent的APIBackend embedding功能"""
    print("=" * 60)
    print("5. 测试RD-Agent APIBackend Embedding")
    print("=" * 60)

    try:
        from rdagent.oai.llm_utils import APIBackend

        backend = APIBackend()
        test_text = "测试RD-Agent embedding功能"

        print(f"测试文本: {test_text}")
        print("正在调用APIBackend.create_embedding()...")

        embedding_vector = backend.create_embedding(input_content=test_text)

        print(f"✓ APIBackend embedding调用成功!")
        print(f"  - 向量类型: {type(embedding_vector)}")
        print(f"  - 向量维度: {len(embedding_vector) if isinstance(embedding_vector, list) else 'N/A'}")
        print(f"  - 前5个值: {embedding_vector[:5] if isinstance(embedding_vector, list) else 'N/A'}")

        return True, embedding_vector

    except Exception as e:
        print(f"✗ APIBackend embedding调用失败: {e}")
        print(f"  错误类型: {type(e).__name__}")
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()
        return False, None


def test_vector_base():
    """测试VectorBase的embedding功能"""
    print("=" * 60)
    print("6. 测试VectorBase KnowledgeMetaData")
    print("=" * 60)

    try:
        from rdagent.components.knowledge_management.vector_base import KnowledgeMetaData

        doc = KnowledgeMetaData(
            content="这是一个测试文档，用于验证VectorBase的embedding功能",
            label="test"
        )

        print(f"文档内容: {doc.content}")
        print(f"文档标签: {doc.label}")
        print("正在创建embedding...")

        doc.create_embedding()

        if doc.embedding is not None:
            print(f"✓ KnowledgeMetaData embedding创建成功!")
            print(f"  - 向量类型: {type(doc.embedding)}")
            print(f"  - 向量维度: {len(doc.embedding) if hasattr(doc.embedding, '__len__') else 'N/A'}")
        else:
            print(f"✗ embedding为None，可能使用了fallback机制")

        return True

    except Exception as e:
        print(f"✗ KnowledgeMetaData embedding创建失败: {e}")
        print(f"  错误类型: {type(e).__name__}")
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()
        return False


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("RD-Agent Embedding API 诊断测试")
    print("=" * 60 + "\n")

    results = []

    # 1. 测试库导入
    if not test_imports():
        print("\n❌ 缺少必要的库，请先安装依赖")
        sys.exit(1)

    # 2. 测试环境变量
    test_env_config()

    # 3. 测试RD-Agent配置
    if not test_rdagent_settings():
        print("\n⚠️ RD-Agent配置加载失败，继续测试...")

    # 4. 测试LiteLLM直接调用
    litellm_success, embedding_vector = test_litellm_embedding()
    results.append(("LiteLLM直接调用", litellm_success))

    # 5. 测试RD-Agent APIBackend
    backend_success, _ = test_rdagent_backend()
    results.append(("APIBackend", backend_success))

    # 6. 测试VectorBase
    vector_success = test_vector_base()
    results.append(("VectorBase", vector_success))

    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")

    print()

    # 给出诊断建议
    if all(r[1] for r in results):
        print("🎉 所有测试通过！Embedding API配置正常。")
    else:
        print("❌ 存在问题，请参考以下建议：")
        print()

        for test_name, success in results:
            if not success:
                if test_name == "LiteLLM直接调用":
                    print(f"• {test_name}失败:")
                    print("  - 检查 API密钥是否正确")
                    print("  - 检查 API Base URL是否正确")
                    print("  - 检查模型名称是否支持")
                    print("  - 检查网络连接")
                    print()
                elif test_name == "APIBackend":
                    print(f"• {test_name}失败:")
                    print("  - 检查 LiteLLM 配置")
                    print("  - 检查缓存设置")
                    print()
                elif test_name == "VectorBase":
                    print(f"• {test_name}失败:")
                    print("  - 检查 fallback 机制是否生效")
                    print("  - 查看警告信息")
                    print()

    print("\n建议的配置示例:")
    print("-" * 60)
    print("# 在 .env 文件中配置:")
    print("OPENAI_API_KEY=your-api-key")
    print("OPENAI_API_BASE=https://api.openai.com/v1")
    print("EMBEDDING_MODEL=text-embedding-3-small")
    print()
    print("# 或者使用 DeepSeek + 智谱AI:")
    print("OPENAI_API_KEY=your-deepseek-key")
    print("OPENAI_API_BASE=https://api.deepseek.com/v1")
    print("CHAT_MODEL=deepseek-chat")
    print("EMBEDDING_OPENAI_API_KEY=your-zhipu-key")
    print("EMBEDDING_OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4")
    print("LITELLM_EMBEDDING_MODEL=zhipuai/embedding-2")
    print("-" * 60)


if __name__ == "__main__":
    main()
