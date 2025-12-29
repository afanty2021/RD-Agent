# 因子索引名称错误 - 最终正确修复报告

**修复日期**: 2025-12-27
**问题类别**: 数据结构列名与提示词不匹配

---

## 🎯 核心发现

### 真正的问题根源

经过深入分析和 critic 反馈确认：

**实际数据使用 `date` 作为索引名称，不是 `datetime`！**

Critic 明确指出：
> "The data's MultiIndex level is named 'date' after resetting"

### 之前的错误修复

之前的所有修复都基于**错误的假设**：
- ❌ 假设数据使用 `datetime`，因此修改提示词要求使用 `datetime`
- ❌ 创建了多个版本都在强调"不要用 date，要用 datetime"
- ❌ 实际上数据本身就是用 `date`，所以应该使用 `date`！

---

## ✅ 正确的修复方案

### 修复的文件

`rdagent/components/coder/factor_coder/prompts.yaml`

### 关键修改

**修改前（错误）**：
```yaml
# 错误地认为数据使用 datetime
DATA STRUCTURE:
  The data has a MultiIndex structure with index names: ['datetime', 'instrument']
  - First level: 'datetime' (time index)

  # 错误的示例
  result = df_reset.set_index(['datetime', 'instrument'])[['FactorName']]
```

**修改后（正确）**：
```yaml
# 正确：数据实际使用 date
DATA STRUCTURE:
  The data has a MultiIndex structure with index names: ['date', 'instrument']
  - First level: 'date' (time index)
  - Second level: 'instrument' (stock/instrument identifier)

  # 正确的示例
  result = df_reset.set_index(['date', 'instrument'])[['FactorName']]
```

### 完整的正确示例

```python
def calculate_Momentum_5D():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # Calculate 5-day momentum
    df_reset['Momentum_5D'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=5)
    )

    # 正确：使用 date 设置索引
    result = df_reset.set_index(['date', 'instrument'])[['Momentum_5D']]
    result.to_hdf('result.h5', key='data')
```

---

## 📊 数据结构验证

### 实际的数据结构

```python
# 加载数据
df = pd.read_hdf('daily_pv.h5', key='data')

# MultiIndex 索引名称
print(df.index.names)  # 输出: ['date', 'instrument']

# reset_index 后的列名
df_reset = df.reset_index()
print(df_reset.columns.tolist())  # 输出: ['date', 'instrument', '$close', ...]
```

### 为什么之前的修复失败了

1. **错误的假设**：根据旧文档认为数据使用 `datetime`
2. **critic 被忽略**：critic 明确说了使用 `date`，但我们没有相信
3. **方向性错误**：所有修复都在强化错误的 `datetime` 用法

---

## 🚀 验证步骤

### 1. 清理缓存

```bash
# 清理所有缓存
rm -rf pickle_cache/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
rm -rf .mypy_cache/
```

### 2. 验证提示词修复

```bash
# 检查关键行
grep -n "index names:" rdagent/components/coder/factor_coder/prompts.yaml
# 应该输出: The data has a MultiIndex structure with index names: ['date', 'instrument']

grep -n "set_index" rdagent/components/coder/factor_coder/prompts.yaml | head -5
# 所有示例应该使用: set_index(['date', 'instrument'])
```

### 3. 重新运行任务

```bash
export RDAGENT_MULTI_PROC_N=1 && \
python -m rdagent.app.qlib_rd_loop.factor --loop_n 2 --step_n 2
```

### 4. 验证生成的代码

检查生成的因子代码应该包含：

```python
# ✅ 正确的代码
def calculate_YourFactor():
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()  # 列名: ['date', 'instrument', ...]

    # 因子计算...

    # ✅ 正确：使用 date
    result = df_reset.set_index(['date', 'instrument'])[['FactorName']]
    result.to_hdf('result.h5', key='data')
```

---

## 📝 预期结果

### 成功的标志

1. ✅ 不再出现 `KeyError: "None of ['datetime'] are in the columns"`
2. ✅ 不再出现 `ValueError: Index must be (datetime, instrument), got ['date', 'instrument']`
3. ✅ 生成的代码成功执行并生成 `result.h5` 文件
4. ✅ Critic 不再报告索引名称错误

### 错误的标志（需要进一步调试）

- ❌ 仍然出现 `KeyError` 或 `ValueError`
- ❌ 代码执行失败
- ❌ Critic 报告列名错误

---

## 🔍 教训总结

### 问题诊断的关键

1. **相信实际反馈**：critic 的反馈是最直接的信息源
2. **验证假设**：应该首先验证实际数据结构，而不是依赖文档
3. **方向性检查**：修复后如果问题更严重，说明方向错了

### 提示词工程原则

1. **数据优先**：提示词必须与实际数据结构完全匹配
2. **示例准确**：所有代码示例必须是可运行的正确代码
3. **简化原则**：移除不必要的复杂说明和警告

---

## 📁 相关文件

### 修改的文件
- `rdagent/components/coder/factor_coder/prompts.yaml` - **已修复为使用 `date`**

### 备份文件
- `rdagent/components/coder/factor_coder/prompts_datetime_version.yaml` - 错误的 datetime 版本备份
- `rdagent/components/coder/factor_coder/prompts_improved.yaml` - 之前的改进版本（也是错误的）

### 文档文件
- `FACTOR_DATE_FIX_REPORT.md` - 本报告，正确的修复记录
- `FACTOR_COLUMN_FIX_REPORT.md` - 之前基于错误假设的修复报告
- `FACTOR_INDEX_FIX_REPORT.md` - 之前基于错误假设的修复报告

---

## ✨ 技术要点

`★ Insight ─────────────────────────────────────`
**数据结构优先原则**：
1. 在修复代码生成问题前，**首先验证实际数据结构**
2. 相信**运行时错误信息**和**critic 反馈**，而不是文档
3. 当修复使问题更严重时，立即**重新评估假设**
4. 提示词必须与**实际运行环境**完全一致，不能有任何偏差
`─────────────────────────────────────────────────`

---

**修复完成时间**: 2025-12-27
**验证状态**: 待用户验证
**关键发现**: 数据使用 `date`，不是 `datetime`！
