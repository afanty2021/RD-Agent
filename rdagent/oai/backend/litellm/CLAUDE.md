[根目录](../../../../../CLAUDE.md) > [rdagent](../../../../../) > [oai](../../../) > [backend](../) > **litellm**

# LiteLLM 后端集成

## 相对路径面包屑
[根目录](../../../../../CLAUDE.md) > [rdagent](../../../../../) > [oai](../../../) > [backend](../) > **litellm**

## 模块职责

LiteLLM后端是RD-Agent的核心LLM集成模块，提供统一的LLM访问接口，支持多种LLM Provider的统一调用、成本追踪、错误处理和重试机制。该模块基于LiteLLM库构建，为RD-Agent的智能体功能提供强大的语言模型支持。

## 核心架构

### 🔧 litellm.py - 核心实现
**功能**：基于LiteLLM的统一LLM后端接口实现

#### 关键特性

**统一接口支持**：
- OpenAI GPT系列（GPT-3.5, GPT-4, GPT-4-turbo等）
- Azure OpenAI服务
- Anthropic Claude系列
- 本地模型（通过OpenAI兼容API）
- 其他支持LiteLLM的Provider

**成本管理**：
- 自动Token计数和成本计算
- 累计成本追踪
- 多Provider成本对比
- 预算控制和告警

**错误处理和重试**：
- 统一的异常处理机制
- 智能重试策略
- 超时错误的特殊处理
- Provider切换支持

**高级功能支持**：
- 函数调用（Function Calling）
- 流式响应（Streaming）
- 响应模式（Response Mode）
- 多模态输入支持

### 🛠️ 错误处理优化

#### 超时错误序列化修复
解决了LiteLLM超时错误无法序列化的问题：

```python
import copyreg

def _reduce_no_init(exc):
    """解决LiteLLM超时错误的序列化问题"""
    cls = exc.__class__
    return (cls.__new__, (cls,), exc.__dict__)

# 为特定异常类型注册序列化方法
for cls in [BadRequestError, Timeout]:
    copyreg.pickle(cls, _reduce_no_init)
```

**解决的问题**：
- 多进程环境中超时错误的序列化失败
- 分布式系统中的错误传递
- 缓存和持久化中的错误存储

## 配置系统

### LiteLLMSettings
基于Pydantic的配置管理系统，支持环境变量配置：

```python
class LiteLLMSettings(LLMSettings):
    class Config:
        env_prefix = "LITELLM_"
        """使用LITELLM_作为环境变量前缀"""
```

### 环境变量配置
```bash
# 基础配置
LITELLM_MODEL="gpt-3.5-turbo"
LITELLM_API_BASE="https://api.openai.com/v1"
LITELLM_API_KEY="your_api_key_here"

# Azure OpenAI配置
LITELLM_API_BASE="https://your-resource.openai.azure.com/"
LITELLM_API_KEY="your_azure_key"
LITELLM_API_VERSION="2023-12-01-preview"

# 超时配置
LITELLM_TIMEOUT=60
LITELLM_MAX_RETRIES=3

# 成本追踪配置
LITELLM_ENABLE_COST_TRACKING=true
LITELLM_COST_CACHE_TTL=3600
```

## 使用接口

### 基础使用
```python
from rdagent.oai.backend.litellm import LiteLLMAPIBackend

# 初始化后端
backend = LiteLLMAPIBackend()

# 简单调用
response = backend.call(
    prompt="Hello, how are you?",
    model="gpt-3.5-turbo"
)
```

### 高级功能使用
```python
# 函数调用
response = backend.call(
    prompt="What's the weather like?",
    model="gpt-3.5-turbo",
    functions=[{
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {...}
    }]
)

# 流式响应
for chunk in backend.stream(
    prompt="Write a story",
    model="gpt-3.5-turbo"
):
    print(chunk, end="")

# 多模态输入
response = backend.call(
    prompt="Describe this image",
    model="gpt-4-vision-preview",
    image_url="https://example.com/image.jpg"
)
```

### 批量调用
```python
# 并行调用
prompts = ["Question 1", "Question 2", "Question 3"]
responses = backend.batch_call(
    prompts=prompts,
    model="gpt-3.5-turbo",
    max_workers=3
)
```

## 性能优化

### 缓存机制
- **响应缓存**：相同请求的智能缓存
- **Token缓存**：Token计数结果缓存
- **成本缓存**：成本计算结果缓存

### 并发控制
- **请求池管理**：控制并发请求数量
- **速率限制**：遵守Provider速率限制
- **负载均衡**：多Provider负载分配

### 资源管理
- **连接池**：HTTP连接复用
- **内存管理**：大响应的流式处理
- **超时控制**：细粒度超时设置

## 监控和诊断

### 成本追踪
```python
# 获取累计成本
total_cost = backend.get_total_cost()

# 按Provider统计
cost_by_provider = backend.get_cost_by_provider()

# 按模型统计
cost_by_model = backend.get_cost_by_model()
```

### 性能监控
```python
# 获取响应时间统计
response_times = backend.get_response_time_stats()

# 获取错误率
error_rate = backend.get_error_rate()

# 获取使用量统计
usage_stats = backend.get_usage_stats()
```

### 调试工具
```python
# 启用详细日志
backend.enable_debug_logging()

# 获取最近的请求历史
recent_requests = backend.get_recent_requests(limit=10)

# 导出使用报告
backend.export_usage_report("usage_report.json")
```

## 故障排除

### 常见问题

**1. API密钥配置错误**
```bash
# 检查环境变量
echo $LITELLM_API_KEY

# 测试连接
python -c "from rdagent.oai.backend.litellm import LiteLLMAPIBackend; LiteLLMAPIBackend().test_connection()"
```

**2. 超时错误**
```python
# 增加超时时间
backend = LiteLLMAPIBackend(timeout=120)

# 启用重试
backend = LiteLLMAPIBackend(max_retries=5)
```

**3. 速率限制**
```python
# 配置速率限制
backend = LiteLLMAPIBackend(
    requests_per_minute=60,
    tokens_per_minute=90000
)
```

**4. 序列化错误**
- 已通过copyreg修复超时错误的序列化问题
- 确保使用最新版本的代码

### 调试模式
```python
# 启用调试日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 获取详细错误信息
try:
    response = backend.call(prompt="test", model="gpt-3.5-turbo")
except Exception as e:
    backend.log_error(e)
    raise
```

## 扩展开发

### 自定义Provider
```python
class CustomProvider(LiteLLMAPIBackend):
    def custom_call(self, prompt, **kwargs):
        # 自定义调用逻辑
        pass

    def custom_auth(self):
        # 自定义认证逻辑
        pass
```

### 自定义中间件
```python
class LoggingMiddleware:
    def before_call(self, request):
        print(f"Calling: {request}")

    def after_call(self, response):
        print(f"Response: {response}")

backend.add_middleware(LoggingMiddleware())
```

### 钩子函数
```python
# 注册调用前钩子
def before_call_hook(prompt, model):
    # 预处理逻辑
    return processed_prompt, model

backend.register_before_call_hook(before_call_hook)

# 注册调用后钩子
def after_call_hook(response):
    # 后处理逻辑
    return processed_response

backend.register_after_call_hook(after_call_hook)
```

## 最佳实践

### 1. 配置管理
- 使用环境变量管理敏感信息
- 为不同环境创建不同的配置文件
- 定期轮换API密钥

### 2. 成本控制
- 设置月度预算限制
- 监控各项目/团队的用量
- 选择性价比最高的模型

### 3. 性能优化
- 合理使用缓存减少重复请求
- 批量处理提高效率
- 选择合适的模型平衡速度和质量

### 4. 错误处理
- 实现优雅的降级策略
- 监控错误率并设置告警
- 准备备用Provider

---

## 变更记录 (Changelog)

### 2025-12-06 - 超时错误修复和稳定性增强
- **序列化问题修复**：解决LiteLLM超时错误在多进程环境中的序列化问题
- **错误处理优化**：增强异常处理机制，提高系统稳定性
- **成本追踪改进**：优化成本计算和缓存机制
- **性能监控增强**：新增详细的性能监控和诊断工具
- **配置系统完善**：基于Pydantic的配置管理系统
- **文档体系建立**：完整的模块文档和使用指南

### 2025-11-17 - 模块初始化
- **基础架构建立**：LiteLLM后端核心框架搭建
- **多Provider支持**：集成主流LLM Provider
- **统一接口设计**：一致的API调用接口
- **成本管理系统**：自动成本追踪和统计

---

*最后更新：2025-12-06*