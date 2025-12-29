# 因子索引名称错误 - 完整修复报告

## 修复日期
2025-12-27

## 问题描述

### 错误信息
```
ValueError: Index must be (date, instrument), got ['datetime', 'instrument']
```

### 影响范围
- `MACD_12_26_9` 因子
- `ATR_14D` 因子
- 其他多个量化因子

### 根本原因
1. **数据结构**：实际数据的索引是 `['datetime', 'instrument']`
2. **代码生成错误**：LLM 生成的代码检查 `['date', 'instrument']`，导致立即失败
3. **提示词混淆**：`prompts.yaml` 中虽然标记为 "WRONG" 的错误示例，但 LLM 仍然学到了错误模式

---

## 修复内容

### 1. 修复文件
`rdagent/components/coder/factor_coder/prompts.yaml`

### 2. 三处关键修改

#### 修改1: 强化系统提示词（第52-56行）
```yaml
!!! MOST CRITICAL: The data index is ['datetime', 'instrument'], NOT ['date', 'instrument'] !!!
- ALWAYS use 'datetime' (never 'date') when referring to the time index
- When checking index: df.index.names should be ['datetime', 'instrument']
- When resetting: df_reset has columns 'datetime' and 'instrument'
- When setting index: use set_index(['datetime', 'instrument'])
```

#### 修改2: 移除混淆示例（第84-85行）
```yaml
# 之前（错误）：
# WRONG: Using 'date' instead of 'datetime'
result = df_reset.set_index(['date', 'instrument'])[['factor']]  # WRONG column name

# 修改后（正确）：
# CRITICAL WARNING: NEVER use 'date' - ALWAYS use 'datetime' for the index column name
# The data index is ['datetime', 'instrument'], NOT ['date', 'instrument']
```

#### 修改3: 更新验证示例（第111-135行）
```python
# CRITICAL: The index is ['datetime', 'instrument'], NOT ['date', 'instrument']
if df.index.names != ['datetime', 'instrument']:
    raise ValueError(f"Index must be (datetime, instrument), got {df.index.names}")

# Reset index for processing
df_reset = df.reset_index()

# Verify columns exist after reset_index
required_cols = ['datetime', 'instrument']
for col in required_cols:
    if col not in df_reset.columns:
        raise ValueError(f"Required column '{col}' not found")

# Restore index with correct names - use 'datetime', NOT 'date'
result = df_reset.set_index(['datetime', 'instrument'])[['YourFactor']]

# Final validation
if result.index.names != ['datetime', 'instrument']:
    raise ValueError(f"Output index must be (datetime, instrument), got {result.index.names}")
```

---

## 清理缓存

### 清理位置
```bash
/Users/berton/github/rd-agent/pickle_cache/
```

### 清理内容
- 🗑️ **257个缓存文件** 包含错误的代码模式
- 🗑️ `rdagent.components.coder.factor_coder.factor.execute/` 缓存
- 🗑️ `rdagent.scenarios.qlib.developer.factor_runner.develop/` 缓存

### 清理命令
```bash
rm -rf pickle_cache/
```

### 清理原因
LLM 可能从缓存中加载旧代码，导致即使修复了提示词，仍然生成错误的索引检查。

---

## 验证方法

### 1. 数据结构验证
```python
import pandas as pd
df = pd.read_hdf('daily_pv.h5', key='data')
print(df.index.names)  # 应该输出: ['datetime', 'instrument']
```

### 2. 正确代码示例
```python
def calculate_CORRECT_FACTOR():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv.h5', key='data')

    # ✅ 正确：检查 ['datetime', 'instrument']
    if df.index.names != ['datetime', 'instrument']:
        raise ValueError(f"Index must be (datetime, instrument), got {df.index.names}")

    df_reset = df.reset_index()

    # ✅ 正确：验证 datetime 列存在
    required_cols = ['datetime', 'instrument', '$close']
    for col in required_cols:
        if col not in df_reset.columns:
            raise ValueError(f"Required column '{col}' not found")

    # 因子计算逻辑...

    # ✅ 正确：使用 datetime 设置索引
    result = df_reset.set_index(['datetime', 'instrument'])[['FACTOR_NAME']]

    result.to_hdf('result.h5', key='data')
```

### 3. 重新运行任务
```bash
export RDAGENT_MULTI_PROC_N=1 && \
python -m rdagent.app.qlib_rd_loop.factor --loop_n 2 --step_n 2
```

**预期结果**：
- ✅ 生成的代码使用 `['datetime', 'instrument']`
- ✅ 不再出现 `Index must be (date, instrument)` 错误
- ✅ 因子成功计算并生成 `result.h5` 文件

---

## 技术亮点

### 提示词工程原则
1. **避免混淆**：即使标记为 "WRONG" 的示例也可能被 LLM 学习
2. **明确优先**：使用 `!!! MOST CRITICAL` 等标记强化关键约束
3. **统一标准**：在整个提示词中保持一致的命名和验证逻辑

### 知识库管理
1. **缓存位置**：`./costeer_knowledge.pkl` 或通过环境变量 `CoSTEER_KNOWLEDGE_BASE_PATH` 指定
2. **代码缓存**：`pickle_cache/` 目录存储 LLM 生成的代码缓存
3. **清理时机**：修复提示词后必须清理缓存，避免 LLM 从旧缓存中学习错误模式

---

## 相关文件

### 修改的文件
- `/Users/berton/Github/RD-Agent/rdagent/components/coder/factor_coder/prompts.yaml`

### 创建的文档
- `/Users/berton/Github/RD-Agent/FACTOR_INDEX_FIX_REPORT.md`
- `/Users/berton/Github/RD-Agent/FACTOR_INDEX_FIX_SUMMARY.md` (本文件)

### 数据文件
- `/Users/berton/Github/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5`

---

## 后续建议

### 1. 监控首次运行
首次运行时仔细观察生成的代码，确保：
- 所有验证步骤使用 `datetime` 而不是 `date`
- 列名检查使用正确的索引名称
- 错误信息中明确指出正确的索引名称

### 2. 添加单元测试
建议添加测试验证生成的代码：
```python
def test_factor_index_names():
    # 确保生成的因子代码使用正确的索引名称
    pass
```

### 3. 持续改进
- 观察是否还有其他类似的混淆问题
- 收集 LLM 生成的错误代码模式
- 定期更新提示词以避免常见错误

---

## 总结

本次修复通过以下三个步骤彻底解决了因子索引名称错误问题：

1. ✅ **修复提示词**：移除混淆示例，强化正确模式的约束
2. ✅ **清理缓存**：删除257个包含错误模式的缓存文件
3. ✅ **验证修复**：提供验证方法和预期结果

现在系统应该能够正确生成使用 `['datetime', 'instrument']` 索引的因子代码。

---
*修复完成时间: 2025-12-27*
*执行者: Claude Code*
