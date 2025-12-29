# Embedding API 问题诊断和修复报告

## 问题概述

上一轮 embedding API 失败的根本原因是**模型名称配置格式错误** + **代码未正确传递API参数**。

## 问题分析

### 原始配置（错误）
```bash
LITELLM_EMBEDDING_MODEL="zhipuai/embedding-2"
```

### 错误信息
```
litellm.BadRequestError: LLM Provider NOT provided.
You passed model=zhipuai/embedding-2
```

### 根本原因（双重问题）

1. **模型名称格式错误**：
   - `zhipuai/` 不是LiteLLM识别的标准Provider前缀
   - 智谱AI的embedding模型应该使用 `openai/` 前缀（因为API兼容）

2. **代码缺陷**：
   - `litellm.py` 的 `_create_embedding_inner_function` 方法没有传递 `api_key` 和 `api_base` 参数
   - 导致即使配置正确，也无法调用到智谱AI的API endpoint

## 解决方案

### 修复1：更新 `.env` 配置

```bash
# 智谱AI嵌入模型配置 - 使用OpenAI兼容模式
EMBEDDING_OPENAI_API_KEY="ac6eafe4e0e342728195f134ed37298e.g6LipjAi4zwvuvmh"
EMBEDDING_OPENAI_BASE_URL="https://open.bigmodel.cn/api/paas/v4"
# 使用 openai/ 前缀让LiteLLM知道这是OpenAI兼容的API
LITELLM_EMBEDDING_MODEL="openai/embedding-2"
```

### 修复2：更新 `litellm.py` 代码

**文件**: `rdagent/oai/backend/litellm.py`
**方法**: `_create_embedding_inner_function`

**变更内容**：
```python
# 准备embedding调用参数
embedding_kwargs = {
    "model": model_name,
    "input": input_content_list,
}

# 如果配置了embedding专用的API密钥和base URL，添加到参数中
if LITELLM_SETTINGS.embedding_openai_api_key:
    embedding_kwargs["api_key"] = LITELLM_SETTINGS.embedding_openai_api_key
if LITELLM_SETTINGS.embedding_openai_base_url:
    embedding_kwargs["api_base"] = LITELLM_SETTINGS.embedding_openai_base_url

response = embedding(**embedding_kwargs)
```

**关键变更**：
- 添加了 `api_key` 参数传递
- 添加了 `api_base` 参数传递
- 这两个参数对于使用自定义API endpoint（如智谱AI）至关重要

## 验证结果

### 完整测试脚本

```bash
python3 << 'PYEOF'
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path="/Users/berton/Github/RD-Agent/.env")

from rdagent.oai.llm_utils import APIBackend
from rdagent.components.knowledge_management.vector_base import KnowledgeMetaData, PDVectorBase

# 1. APIBackend测试
backend = APIBackend()
result = backend.create_embedding("测试文本")
print(f"✓ APIBackend: 向量维度 {len(result)}")

# 2. KnowledgeMetaData测试
doc = KnowledgeMetaData(content="测试文档", label="test")
doc.create_embedding()
print(f"✓ KnowledgeMetaData: 向量维度 {len(doc.embedding)}")

# 3. VectorBase搜索测试
vb = PDVectorBase()
vb.add(doc)
results, sims = vb.search("测试查询", topk_k=1)
print(f"✓ VectorBase搜索: 找到 {len(results)} 个结果，相似度 {sims[0]:.4f}")
PYEOF
```

### 测试结果

```
✓ APIBackend: 向量维度 1024
✓ KnowledgeMetaData: 向量维度 1024
✓ VectorBase搜索: 找到 1 个结果，相似度 0.5703
```

## 技术要点

### 1. LiteLLM 的 OpenAI 兼容模式

当使用第三方OpenAI兼容API时（如智谱AI）：
```python
from litellm import embedding

response = embedding(
    model="openai/embedding-2",  # 使用 openai/ 前缀
    input=["text"],
    api_key="your-api-key",      # 第三方API密钥
    api_base="https://...",      # 第三方endpoint
)
```

### 2. 智谱AI API 特点

- **Endpoint**: `https://open.bigmodel.cn/api/paas/v4`
- **Embedding模型**: `embedding-2` (1024维)
- **兼容性**: 完全兼容OpenAI API格式
- **认证**: 使用JWT格式的API密钥

### 3. RD-Agent 配置优先级

```
环境变量 > .env文件 > 默认值
```

对于embedding模型配置：
- `LITELLM_EMBEDDING_MODEL` - 最高优先级
- `EMBEDDING_MODEL` - 次优先级
- 默认值 `text-embedding-3-small` - 最低优先级

## 修改文件清单

1. ✅ `/Users/berton/Github/RD-Agent/.env`
   - 更新 `LITELLM_EMBEDDING_MODEL` 为 `openai/embedding-2`

2. ✅ `/Users/berton/Github/RD-Agent/rdagent/oai/backend/litellm.py`
   - 修改 `_create_embedding_inner_function` 方法
   - 添加 `api_key` 和 `api_base` 参数传递

## 其他配置建议

### 使用官方OpenAI API（推荐用于生产环境）

```bash
OPENAI_API_KEY=sk-your-openai-key
EMBEDDING_MODEL=text-embedding-3-small
```

### 使用本地embedding模型

```bash
EMBEDDING_MODEL=huggingface/BAAI/bge-small-en-v1.5
```

### 使用SiliconFlow等第三方服务

```bash
LITELLM_PROXY_API_KEY=your-siliconflow-key
LITELLM_PROXY_API_BASE=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=litellm_proxy/BAAI/bge-large-en-v1.5
```

## 附加工具

项目已创建 `test_embedding_api.py` 测试脚本：

```bash
python test_embedding_api.py
```

该脚本提供全面的embedding API诊断功能：
1. 库导入检查
2. 环境变量配置验证
3. RD-Agent LLM配置检查
4. LiteLLM直接调用测试
5. RD-Agent APIBackend测试
6. VectorBase KnowledgeMetaData测试

## 总结

- ✅ **问题已完全修复**：配置 + 代码双重修复
- ✅ **测试全部通过**：APIBackend、KnowledgeMetaData、VectorBase均正常工作
- ✅ **向后兼容**：修复不影响其他embedding provider的使用
- ✅ **生产就绪**：智谱AI的API稳定可靠，成本低于OpenAI

---

**修复时间**: 2025-12-27
**修复人员**: Claude Code Assistant
**测试状态**: ✅ 所有测试通过
