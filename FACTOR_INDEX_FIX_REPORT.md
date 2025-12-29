# 因子索引名称错误修复报告

## 问题描述

### 症状
运行 `export RDAGENT_MULTI_PROC_N=1 && python -m rdagent.app.qlib_rd_loop.factor --loop_n 2 --step_n 2` 时出现以下错误：

```
ValueError: Index must be (date, instrument), got ['datetime', 'instrument']
```

影响因子：
- `MACD_12_26_9`
- `ATR_14D`
- 其他多个因子

### 根本原因

1. **数据结构确认**：实际数据的索引是 `['datetime', 'instrument']`，不是 `['date', 'instrument']`

2. **代码生成问题**：生成的因子代码在验证时使用了错误的索引名称：
   ```python
   # 错误代码
   if df.index.names != ['date', 'instrument']:
       raise ValueError(f"Index must be (date, instrument), got {df.index.names}")
   ```

3. **提示词混淆**：虽然 `prompts.yaml` 第56行明确说明使用 `datetime`，但：
   - 第85行的错误示例（标记为 WRONG）中仍然使用了 `['date', 'instrument']`
   - 这可能导致 LLM 学到了错误的模式
   - 验证示例中的检查条件不够明确

## 修复方案

### 修改文件
`rdagent/components/coder/factor_coder/prompts.yaml`

### 具体修改

#### 1. 强化系统提示词开头 (第52-56行)
```yaml
!!! MOST CRITICAL: The data index is ['datetime', 'instrument'], NOT ['date', 'instrument'] !!!
- ALWAYS use 'datetime' (never 'date') when referring to the time index
- When checking index: df.index.names should be ['datetime', 'instrument']
- When resetting: df_reset has columns 'datetime' and 'instrument'
- When setting index: use set_index(['datetime', 'instrument'])
```

#### 2. 移除混淆的错误示例 (第84-85行)
```yaml
# 之前：
# WRONG: Using 'date' instead of 'datetime'
result = df_reset.set_index(['date', 'instrument'])[['factor']]  # WRONG column name

# 修改后：
# CRITICAL WARNING: NEVER use 'date' - ALWAYS use 'datetime' for the index column name
# The data index is ['datetime', 'instrument'], NOT ['date', 'instrument']
```

#### 3. 更新验证示例 (第111-135行)
```python
# CRITICAL: The index is ['datetime', 'instrument'], NOT ['date', 'instrument']
if df.index.names != ['datetime', 'instrument']:
    raise ValueError(f"Index must be (datetime, instrument), got {df.index.names}")

# ...

# Restore index with correct names - use 'datetime', NOT 'date'
result = df_reset.set_index(['datetime', 'instrument'])[['YourFactor']]

# Final validation
if result.index.names != ['datetime', 'instrument']:
    raise ValueError(f"Output index must be (datetime, instrument), got {result.index.names}")
```

## 修改原则

1. **SOLID - 单一职责**：提示词专注于指导正确的索引命名，避免混淆示例
2. **DRY - 不要重复**：统一使用 `datetime`，避免 `date` 和 `datetime` 混用
3. **明确优先**：使用 `!!! MOST CRITICAL` 强调最关键的要求
4. **防御性编程**：在提示词中提供明确的验证逻辑

## 验证方法

运行以下命令验证修复：
```bash
export RDAGENT_MULTI_PROC_N=1 && python -m rdagent.app.qlib_rd_loop.factor --loop_n 2 --step_n 2
```

预期结果：
- 生成的因子代码应使用 `['datetime', 'instrument']`
- 不应再出现 `Index must be (date, instrument)` 错误

## 后续建议

1. **知识库清理**：如果知识库中有使用 `date` 的历史记录，需要清理或更新
2. **单元测试**：添加测试验证生成的代码使用正确的索引名称
3. **代码审查**：在代码生成后添加自动检查，验证索引名称的正确性

## 相关文件

- `/Users/berton/Github/RD-Agent/rdagent/components/coder/factor_coder/prompts.yaml`
- `/Users/berton/Github/RD-Agent/rdagent/scenarios/qlib/developer/utils.py`
- `/Users/berton/Github/RD-Agent/git_ignore_folder/factor_implementation_source_data/daily_pv.h5`

---
*修复日期: 2025-12-27*
*修复者: Claude Code*
