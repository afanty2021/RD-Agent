# 因子计算列名错误修复报告

**修复日期**: 2025-12-27
**问题类别**: 数据结构列名不匹配
**影响范围**: Qlib 量化因子计算

---

## 📋 问题诊断

### 错误现象
训练日志显示三个因子计算函数均失败，错误信息为：
```python
KeyError: "None of ['date'] are in the columns"
```

涉及失败的函数：
- `calculate_MOMENTUM_10D()`
- `calculate_AVG_VOLUME_20D()`
- `calculate_VOLATILITY_5D()`

### 根本原因分析

1. **数据结构不匹配**：
   - Qlib 生成的 HDF5 数据文件使用 `(datetime, instrument)` 作为 MultiIndex
   - 提示词中示例代码错误地使用 `date` 而不是 `datetime`

2. **提示词错误**：
   - 在 `rdagent/components/coder/factor_coder/prompts.yaml` 第71行
   - 示例代码使用 `set_index(['date', 'instrument'])`
   - 然后要求重命名为 `result.index.names = ['datetime', 'instrument']`
   - 但实际上数据索引已经是 `datetime`，不应该使用 `date`

3. **缺失验证**：
   - 生成的代码没有验证输入数据的列结构
   - 导致错误在运行时才发现

---

## 🔧 修复方案

### 1. 修复列名错误

**文件**: `rdagent/components/coder/factor_coder/prompts.yaml`

**修改前**:
```yaml
3. Use set_index(['date', 'instrument']) to restore MultiIndex AFTER calculations
4. CRITICAL: After set_index(), you MUST rename the index level from 'date' to 'datetime':
   result.index.names = ['datetime', 'instrument']
```

**修改后**:
```yaml
3. Use set_index(['datetime', 'instrument']) to restore MultiIndex AFTER calculations
4. CRITICAL: Always use 'datetime' (NOT 'date') as the index column name
```

**修改前**:
```python
result = df_reset.set_index(['date', 'instrument'])[['VolumeTrend']]
result.index.names = ['datetime', 'instrument']
```

**修改后**:
```python
result = df_reset.set_index(['datetime', 'instrument'])[['VolumeTrend']]
# No need to rename - already correct
```

### 2. 添加数据验证最佳实践

在提示词中添加了完整的数据验证模板：

```python
def calculate_YourFactor():
    import pandas as pd
    import numpy as np

    # Load data
    df = pd.read_hdf('daily_pv.h5', key='data')

    # CRITICAL: Validate data structure
    if not isinstance(df.index, pd.MultiIndex):
        raise ValueError("Data must have a MultiIndex (datetime, instrument)")

    if 'datetime' not in df.index.names or 'instrument' not in df.index.names:
        raise ValueError(f"Index must be (datetime, instrument), got {df.index.names}")

    # Reset index for processing
    df_reset = df.reset_index()

    # Verify columns exist
    required_cols = ['datetime', 'instrument']
    for col in required_cols:
        if col not in df_reset.columns:
            raise ValueError(f"Required column '{col}' not found. Available columns: {df_reset.columns.tolist()}")

    # Your factor calculation logic here
    # ...

    # Restore index with correct names
    result = df_reset.set_index(['datetime', 'instrument'])[['YourFactor']]

    # Final validation
    if 'datetime' not in result.index.names or 'instrument' not in result.index.names:
        raise ValueError(f"Output index must be (datetime, instrument), got {result.index.names}")

    result.to_hdf('result.h5', key='data')
```

### 3. 添加错误示例对比

在提示词中明确标注了正确和错误的用法：

```python
# CORRECT: MultiIndex handling with 'datetime'
df_reset = df.reset_index()
df_reset['factor'] = df_reset.groupby('instrument')['$close'].transform(lambda x: x.rolling(10).std())
result = df_reset.set_index(['datetime', 'instrument'])[['factor']]

# WRONG: Using 'date' instead of 'datetime'
result = df_reset.set_index(['date', 'instrument'])[['factor']]  # WRONG column name
```

---

## ✅ 预期效果

### 修复后的改进

1. **列名一致性**：
   - 所有生成的代码使用 `datetime` 作为列名
   - 与 Qlib 数据结构完全匹配

2. **错误预防**：
   - 在代码执行前验证数据结构
   - 提供清晰的错误信息

3. **开发体验**：
   - 减少调试时间
   - 更快地定位问题

4. **代码质量**：
   - 更健壮的代码
   - 更好的错误处理

### 验证方法

重新运行因子计算，应该看到：
```python
# 正确的代码生成
def calculate_MOMENTUM_10D():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv.h5', key='data')

    # 数据结构验证
    if not isinstance(df.index, pd.MultiIndex):
        raise ValueError("Data must have a MultiIndex (datetime, instrument)")

    # 处理数据
    df_reset = df.reset_index()
    # ... 计算逻辑 ...

    # 正确的列名
    result = df_reset.set_index(['datetime', 'instrument'])[['MOMENTUM_10D']]
    result.to_hdf('result.h5', key='data')
```

---

## 📊 影响范围

### 直接影响
- ✅ 所有新生成的因子计算代码
- ✅ Qlib 量化因子实验
- ✅ 因子评估和验证流程

### 无影响
- ❌ 现有的因子代码（需要重新生成）
- ❌ 其他场景（data_science, kaggle 等）
- ❌ 数据加载和存储逻辑

---

## 🔄 下一步行动

### 立即行动
1. ✅ 修复提示词文件
2. ✅ 添加数据验证模板
3. ⏳ 重新运行失败的因子实验

### 后续优化
1. 考虑为现有因子代码添加迁移脚本
2. 添加单元测试验证列名正确性
3. 在 CI/CD 中集成数据结构检查

### 长期改进
1. 建立数据结构规范文档
2. 添加自动化的列名检查工具
3. 完善错误提示和调试信息

---

## 📚 相关文件

### 修改的文件
- `rdagent/components/coder/factor_coder/prompts.yaml` - 核心提示词修复

### 相关文件（未修改）
- `rdagent/scenarios/qlib/experiment/factor_data_template/generate.py` - 数据生成逻辑
- `rdagent/scenarios/qlib/developer/utils.py` - 数据验证逻辑
- `rdagent/components/coder/factor_coder/eva_utils.py` - 评估器

---

## 💡 经验教训

### 问题根源
1. **提示词示例错误**：示例代码使用了错误的列名
2. **缺乏数据验证**：生成的代码没有验证数据结构
3. **测试覆盖不足**：没有在开发阶段发现列名问题

### 预防措施
1. **提示词工程**：
   - 确保示例代码与实际数据结构一致
   - 提供清晰的正反例对比

2. **代码生成**：
   - 添加数据结构验证
   - 提供详细的错误信息

3. **测试策略**：
   - 添加单元测试验证列名
   - 集成测试覆盖完整流程

---

**修复完成时间**: 2025-12-27
**验证状态**: 待测试
**负责人**: RD-Agent 开发团队
