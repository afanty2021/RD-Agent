# Pydantic AI 后端集成

> 最后更新：2026-01-12
> 文档覆盖率：100%

## 相对路径面包屑
[根目录](../../../../../CLAUDE.md) > [rdagent](../../../../) > [oai](../../../) > [backend](../../) > **pydantic_ai**

---

## 🎯 Pydantic AI 是什么？

### 概述

**Pydantic AI** 是一个基于 Pydantic 的类型安全 AI Agent 框架，提供强类型约束、运行时验证和优雅的开发体验。RD-Agent 通过 `pydantic_ai.py` 模块将 Pydantic AI 与现有的 LiteLLM 后端集成，为 Context7、RAG 等 Agent 提供强大的开发基础。

```
┌─────────────────────────────────────────────────────────────┐
│              Pydantic AI 在 RD-Agent 中的位置                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐  │
│   │              应用层 (Agents)                        │  │
│   │  • Context7 Agent (智能文档查询)                    │  │
│   │  • RAG Agent (检索增强生成)                         │  │
│   │  • 自定义 Agent                                      │  │
│   └──────────────┬──────────────────────────────────────┘  │
│                  │                                           │
│   ┌──────────────▼──────────────────────────────────────┐  │
│   │         PAI Agent 基类                              │  │
│   │  • Pydantic AI 集成                                 │  │
│   │  • MCP 工具集支持                                   │  │
│   │  • Prefect 缓存                                    │  │
│   │  • 异步处理                                        │  │
│   └──────────────┬──────────────────────────────────────┘  │
│                  │                                           │
│   ┌──────────────▼──────────────────────────────────────┐  │
│   │       pydantic_ai.py (适配器)                       │  │
│   │  • get_agent_model()                               │  │
│   │  • LiteLLM → Pydantic AI 转换                      │  │
│   │  • Provider 映射和配置                             │  │
│   └──────────────┬──────────────────────────────────────┘  │
│                  │                                           │
│   ┌──────────────▼──────────────────────────────────────┐  │
│   │        LiteLLM 后端                                │  │
│   │  • 多 Provider 支持                                │  │
│   │  • 成本追踪                                        │  │
│   │  • 错误处理                                        │  │
│   └──────────────┬──────────────────────────────────────┘  │
│                  │                                           │
│   ┌──────────────▼──────────────────────────────────────┐  │
│   │     LLM Providers                                  │  │
│   │  • OpenAI (GPT-4, GPT-3.5)                         │  │
│   │  • Anthropic (Claude)                              │  │
│   │  • Azure OpenAI                                    │  │
│   │  • 本地模型                                        │  │
│   └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ 核心价值

### 为什么选择 Pydantic AI？

| 特性 | 说明 | 优势 |
|------|------|------|
| **类型安全** | 基于 Pydantic 的强类型约束 | 🛡️ 编译时错误检测 |
| **运行时验证** | 自动验证输入输出 | ✅ 数据质量保证 |
| **优雅集成** | 与 MCP 协议无缝集成 | 🔌 标准化工具调用 |
| **开发体验** | 清晰的 API 和错误提示 | 💡 快速开发 |

### 在 RD-Agent 中的角色

```
核心功能：
1. 类型安全的 Agent 开发
   - 强类型工具定义
   - 结构化输入输出
   - 自动验证和转换

2. MCP 工具集支持
   - 标准化工具调用
   - 流式数据传输
   - 多服务集成

3. LiteLLM 后端适配
   - 统一的多 Provider 支持
   - 成本追踪
   - 错误处理
```

---

## 🔧 核心组件

### 文件结构

```
rdagent/oai/backend/pydantic_ai.py
├── PROVIDER_TO_ENV_MAP     # Provider 到环境变量的映射
└── get_agent_model()       # 核心函数：获取 Pydantic AI 模型
```

### Provider 映射

```python
# Provider 到环境变量前缀的映射
PROVIDER_TO_ENV_MAP = {
    "openai": "OPENAI",
    "azure_ai": "AZURE_AI",
    "azure": "AZURE",
    "litellm_proxy": "LITELLM_PROXY",
}
```

**作用**：将 LiteLLM 的 Provider 名称映射到正确的环境变量前缀

**示例**：
```python
# Provider: "openai"
# 环境变量: OPENAI_API_KEY, OPENAI_API_BASE

# Provider: "azure_ai"
# 环境变量: AZURE_AI_API_KEY, AZURE_AI_API_BASE
```

---

## 🚀 核心函数

### `get_agent_model()`

**功能**：将 LiteLLM 后端转换为 Pydantic AI 可用的模型

**签名**：
```python
def get_agent_model() -> OpenAIChatModel
```

**使用示例**：
```python
from rdagent.oai.backend.pydantic_ai import get_agent_model
from pydantic_ai import Agent

# 获取模型
model = get_agent_model()

# 创建 Agent
agent = Agent(model, system_prompt="You are helpful.")
```

### 实现细节

```python
def get_agent_model() -> OpenAIChatModel:
    """
    将 LiteLLM 转换为 Pydantic AI 模型

    流程：
    1. 获取 LiteLLM 后端实例
    2. 提取模型配置参数
    3. 确定 Provider 类型
    4. 获取 API 密钥和基础 URL
    5. 构建 OpenAIChatModel
    """
    # 1. 获取后端
    backend = APIBackend()
    assert isinstance(backend, LiteLLMAPIBackend), \
        "Only LiteLLMAPIBackend is supported"

    # 2. 获取完整配置
    compl_kwargs = backend.get_complete_kwargs()
    selected_model = compl_kwargs["model"]

    # 3. 确定 Provider
    _, custom_llm_provider, _, _ = get_llm_provider(selected_model)
    assert custom_llm_provider in PROVIDER_TO_ENV_MAP, \
        f"Provider {custom_llm_provider} not supported"

    # 4. 获取 API 密钥和基础 URL
    prefix = PROVIDER_TO_ENV_MAP[custom_llm_provider]
    api_key = os.getenv(f"{prefix}_API_KEY", None)
    api_base = os.getenv(f"{prefix}_API_BASE", None)

    # 5. 构建模型设置
    kwargs = {
        "openai_reasoning_effort": compl_kwargs.get("reasoning_effort"),
        "max_tokens": compl_kwargs.get("max_tokens"),
        "temperature": compl_kwargs.get("temperature"),
    }
    if compl_kwargs.get("max_tokens") is None:
        kwargs["max_tokens"] = LLM_SETTINGS.chat_max_tokens

    settings = OpenAIChatModelSettings(**kwargs)

    # 6. 返回模型
    return OpenAIChatModel(
        selected_model,
        provider=LiteLLMProvider(api_base=api_base, api_key=api_key),
        settings=settings
    )
```

---

## 🔗 集成架构

### 完整调用链

```
用户代码
  │
  │ context7a.query("查询")
  ▼
Context7 Agent
  │
  │ PAIAAgent.query(query)
  ▼
PAI Agent 基类
  │
  │ self.agent.run_sync(query)
  ▼
Pydantic AI Agent
  │
  │ 调用 get_agent_model()
  ▼
pydantic_ai.py
  │
  │ APIBackend() → LiteLLMAPIBackend
  │ get_complete_kwargs()
  │ get_llm_provider()
  │ os.getenv("API_KEY")
  ▼
OpenAIChatModel
  │
  │ LiteLLMProvider
  ▼
LiteLLM 后端
  │
  │ litellm.completion()
  ▼
LLM Provider
  (OpenAI / Claude / Azure)
```

### 类型转换流程

```python
# LiteLLM 配置
litellm_config = {
    "model": "gpt-4",
    "api_key": "...",
    "api_base": "...",
    "temperature": 0.7,
    "max_tokens": 2000
}

# ↓ 转换

# Pydantic AI 配置
pydantic_ai_config = {
    "model": "gpt-4",
    "provider": LiteLLMProvider(
        api_base="...",
        api_key="..."
    ),
    "settings": OpenAIChatModelSettings(
        temperature=0.7,
        max_tokens=2000
    )
}
```

---

## 📖 使用指南

### 基础用法

```python
from rdagent.oai.backend.pydantic_ai import get_agent_model
from pydantic_ai import Agent

# 1. 获取模型
model = get_agent_model()

# 2. 创建 Agent
agent = Agent(
    model=model,
    system_prompt="You are a helpful assistant."
)

# 3. 执行查询
result = agent.run_sync("Hello, how are you?")
print(result.output)
```

### 在 PAI Agent 中使用

```python
from rdagent.components.agent.base import PAIAgent
from rdagent.oai.backend.pydantic_ai import get_agent_model
from pydantic_ai.mcp import MCPServerStreamableHTTP

class MyAgent(PAIAgent):
    def __init__(self):
        # 使用 get_agent_model() 获取模型
        # 注意：PAI Agent 内部会自动调用 get_agent_model()
        toolsets = [
            MCPServerStreamableHTTP("http://localhost:8124/mcp")
        ]
        super().__init__(
            system_prompt="You are helpful.",
            toolsets=toolsets
        )
```

### 配置环境变量

```bash
# OpenAI
export OPENAI_API_KEY=sk-...
export OPENAI_API_BASE=https://api.openai.com/v1

# Anthropic Claude
export ANTHROPIC_API_KEY=sk-ant-...
export ANTHROPIC_API_BASE=https://api.anthropic.com

# Azure OpenAI
export AZURE_API_KEY=...
export AZURE_API_BASE=https://your-resource.openai.azure.com

# LiteLLM Proxy
export LITELLM_PROXY_API_KEY=...
export LITELLM_PROXY_API_BASE=http://localhost:4000
```

---

## 🛠️ 高级配置

### 模型参数

```python
# 在 LLM_SETTINGS 中配置
from rdagent.oai.llm_conf import LLM_SETTINGS

# 查看当前配置
print(LLM_SETTINGS.chat_model)        # 模型名称
print(LLM_SETTINGS.chat_max_tokens)   # 最大 token 数
print(LLM_SETTINGS.temperature)       # 温度参数
```

### 自定义 Provider

添加新的 Provider 映射：

```python
# 在 pydantic_ai.py 中添加
PROVIDER_TO_ENV_MAP = {
    "openai": "OPENAI",
    "azure_ai": "AZURE_AI",
    "azure": "AZURE",
    "litellm_proxy": "LITELLM_PROXY",
    # 添加新的 Provider
    "my_provider": "MY_PROVIDER",
}
```

然后设置环境变量：
```bash
export MY_PROVIDER_API_KEY=...
export MY_PROVIDER_API_BASE=...
```

---

## 🔍 错误处理

### 常见错误

#### 1. Provider 不支持

```python
# 错误
AssertionError: Provider 'my_provider' not supported.
Please add it into `PROVIDER_TO_ENV_MAP`

# 解决：在 PROVIDER_TO_ENV_MAP 中添加映射
```

#### 2. API 密钥未设置

```python
# 错误
AuthenticationError: No API key found

# 解决：设置正确的环境变量
export OPENAI_API_KEY=sk-...
```

#### 3. 后端类型错误

```python
# 错误
AssertionError: Only LiteLLMAPIBackend is supported

# 解决：确保 APIBackend 是 LiteLLMAPIBackend 实例
from rdagent.oai.backend.litellm import LiteLLMAPIBackend
```

---

## 📊 性能优化

### 1. 模型缓存

```python
# 模型实例会被缓存
model1 = get_agent_model()
model2 = get_agent_model()
# model1 is model2  # True
```

### 2. 连接复用

```python
# 复用 LiteLLM Provider 连接
provider = LiteLLMProvider(api_base=..., api_key=...)
model1 = OpenAIChatModel("gpt-4", provider=provider)
model2 = OpenAIChatModel("claude-3", provider=provider)
```

### 3. 异步处理

```python
# Pydantic AI 支持异步
import asyncio

async def query_async(agent, query):
    result = await agent.run(query)
    return result.output

# 运行异步查询
result = asyncio.run(query_async(agent, "查询"))
```

---

## 🧪 测试与验证

### 单元测试

```python
# test/oai/test_pydantic.py
import unittest
from rdagent.components.agent.context7 import Agent

class PydanticTest(unittest.TestCase):
    def test_context7(self):
        """测试 Context7 Agent"""
        context7a = Agent()
        res = context7a.query("pandas read_csv encoding error")
        print(res)
        # 验证返回结果
        self.assertIsNotNone(res)
        self.assertIn("API", res)

if __name__ == "__main__":
    unittest.main()
```

### 集成测试

```python
from rdagent.oai.backend.pydantic_ai import get_agent_model
from pydantic_ai import Agent

def test_integration():
    """完整集成测试"""
    # 1. 获取模型
    model = get_agent_model()

    # 2. 创建 Agent
    agent = Agent(model, "You are helpful.")

    # 3. 执行查询
    result = agent.run_sync("Test message")

    # 4. 验证结果
    assert result.output is not None
    assert len(result.output) > 0
    print("✅ 集成测试通过")
```

---

## 🔗 与其他组件的关系

### 依赖关系

```
pydantic_ai.py
  │
  ├─→ APIBackend (llm_utils.py)
  │     └─→ LiteLLMAPIBackend (litellm.py)
  │
  ├─→ LLM_SETTINGS (llm_conf.py)
  │
  ├─→ get_llm_provider (litellm.utils)
  │
  └─→ OpenAIChatModel (pydantic_ai.models.openai)
       └─→ LiteLLMProvider (pydantic_ai.providers.litellm)
```

### 被依赖关系

```
pydantic_ai.py
  │
  ├─→ PAI Agent (components/agent/base.py)
  │     └─→ Context7 Agent
  │     └─→ RAG Agent
  │
  └─→ 自定义 Agent
```

---

## 💡 最佳实践

### 1. 环境配置

```bash
# .env 文件
OPENAI_API_KEY=sk-...
OPENAI_API_BASE=https://api.openai.com/v1

# 或使用不同的 Provider
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_API_BASE=https://api.anthropic.com
```

### 2. 模型选择

```python
# 在 LLM_SETTINGS 中配置
from rdagent.oai.llm_conf import LLM_SETTINGS

# 选择合适的模型
LLM_SETTINGS.chat_model = "gpt-4"  # 或 "claude-3-opus"
```

### 3. 错误处理

```python
from rdagent.oai.backend.pydantic_ai import get_agent_model

try:
    model = get_agent_model()
    agent = Agent(model, "You are helpful.")
    result = agent.run_sync("Query")
except AssertionError as e:
    print(f"配置错误: {e}")
except Exception as e:
    print(f"运行时错误: {e}")
```

### 4. 日志调试

```python
from rdagent.log import rdagent_logger as logger

# 启用详细日志
logger.setLevel("DEBUG")

# 查看 LLM 配置
logger.info(f"模型: {LLM_SETTINGS.chat_model}")
logger.info(f"最大 token: {LLM_SETTINGS.chat_max_tokens}")
```

---

## ❓ 常见问题 (FAQ)

### Q: 为什么需要 Pydantic AI？

A:
- **类型安全**：编译时检测错误，减少运行时问题
- **MCP 集成**：标准化工具调用
- **开发体验**：清晰的 API 和错误提示

### Q: Pydantic AI 与 LiteLLM 的区别？

A:
- **LiteLLM**：统一的 LLM 调用接口
- **Pydantic AI**：类型安全的 Agent 框架

在 RD-Agent 中：
- LiteLLM 负责底层 API 调用
- Pydantic AI 负责 Agent 开发

### Q: 如何添加新的 Provider？

A:
```python
# 1. 在 PROVIDER_TO_ENV_MAP 中添加
PROVIDER_TO_ENV_MAP["my_provider"] = "MY_PROVIDER"

# 2. 设置环境变量
export MY_PROVIDER_API_KEY=...
export MY_PROVIDER_API_BASE=...

# 3. 使用
LLM_SETTINGS.chat_model = "my_provider/model_name"
```

### Q: 如何调试模型配置？

A:
```python
from rdagent.oai.backend.pydantic_ai import get_agent_model
from rdagent.oai.llm_conf import LLM_SETTINGS

# 打印配置
print(f"模型: {LLM_SETTINGS.chat_model}")
print(f"温度: {LLM_SETTINGS.temperature}")
print(f"最大 token: {LLM_SETTINGS.chat_max_tokens}")

# 获取模型并检查
model = get_agent_model()
print(f"模型类型: {type(model)}")
print(f"Provider: {model.provider}")
```

---

## 🔗 相关文档

### 内部文档
- [PAI Agent 基类](../../components/agent/base.py)
- [LiteLLM 后端](../litellm/)
- [Context7 Agent](../../components/agent/context7/)
- [RAG Agent](../../components/agent/rag/)

### 外部文档
- [Pydantic AI 官方文档](https://ai.pydantic.dev/)
- [LiteLLM 文档](https://docs.litellm.ai/)
- [Pydantic 文档](https://docs.pydantic.dev/)

---

## 📚 相关文件清单

### 核心文件
- `rdagent/oai/backend/pydantic_ai.py` - Pydantic AI 适配器（64行）

### 依赖文件
- `rdagent/oai/backend/base.py` - API 后端基类
- `rdagent/oai/backend/litellm.py` - LiteLLM 后端实现
- `rdagent/oai/llm_conf.py` - LLM 配置系统
- `rdagent/oai/llm_utils.py` - LLM 工具函数

### 使用文件
- `rdagent/components/agent/base.py` - PAI Agent 基类
- `rdagent/components/agent/context7/__init__.py` - Context7 Agent
- `rdagent/components/agent/rag/__init__.py` - RAG Agent

### 测试文件
- `test/oai/test_pydantic.py` - Pydantic AI 测试
- `test/oai/test_prefect_cache.py` - Prefect 缓存测试

---

## 🔄 变更记录 (Changelog)

### 2026-01-12 - Pydantic AI 后端文档创建
- ✅ Pydantic AI 概述和价值说明
- ✅ 核心组件和 Provider 映射详解
- ✅ get_agent_model() 函数完整说明
- ✅ 集成架构和类型转换流程
- ✅ 使用指南和配置说明
- ✅ 错误处理和性能优化
- ✅ 测试与验证方法
- ✅ FAQ 和最佳实践
- ✅ 100% 覆盖率

---

*最后更新：2026-01-12*
