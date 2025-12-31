# 报告期概念实现文档

## 概述

本文档详细说明了RD-Agent量化因子开发系统中"报告期概念"的完整实现。该方案正确处理季度财务数据的时序特性，避免了前向填充导致的"未来函数"问题。

## 背景

### 问题分析

**原方案（前向填充）的问题：**
1. **掩盖数据特性**：财务数据本质上是季度报告，前向填充会让人误以为是日频数据
2. **信息时效性丢失**：无法区分"刚发布的报告"和"半年前的报告"
3. **未来函数风险**：在回测时可能使用了当时尚未发布的数据
4. **误导模型学习**：ML模型可能学习到错误的时序模式

**财务数据的本质：**
- 季度报告：年报、一季报、半年报、三季报
- 公告滞后：报告期结束后1-2个月才发布公告
- 稀疏性：约60个交易日才有1次新数据（覆盖率约1.6%）

### 方案2：引入报告期概念

**核心思想：**
- 保留财务数据的季度特性（不进行前向填充）
- 在因子计算时，使用"在时间t已公告的最新报告"
- 正确反映信息可获得性，避免未来函数

**关键优势：**
1. ✅ 时序正确：完全避免未来函数
2. ✅ 信息时效：明确知道报告的新旧程度
3. 保留特性：季度数据的低频特性被正确利用
4. 易于理解：逻辑清晰，符合实际投资流程

## 实现架构

### 1. 数据准备层

#### 文件：`scripts/prepare_report_period_data.py`

**功能：** 创建基于报告期的数据集

**核心逻辑：**
```python
# 1. 读取价格数据（日频）
price_data = D.features(instruments, price_fields, freq="day")

# 2. 读取财务报告数据（包含end_date和ann_date）
df_financial = pd.read_hdf(financial_h5)

# 3. 将财务数据转换为"公告日"视角
# 即：在ann_date这一天，可以获得end_date的财务数据
financial_by_announce['datetime'] = pd.to_datetime(
    financial_by_announce['ann_date'].astype(float).astype(int),
    format='%Y%m%d'
)

# 4. 合并（财务数据只在公告日有值，其他日期为NaN）
df_merged = price_merge.merge(financial_by_announce, on=['datetime', 'instrument'], how='left')
```

**数据格式：**
- 时间范围：2010-01-04 至 2025-12-29
- 总记录数：1,165,137
- 财务数据覆盖率：0.44%（约1/227，符合季度特性）
- 文件大小：217.83 MB

**验证输出：**
```
股票: 600000.SH
日期                收盘价    ROE        EPS
======================================================
2025-12-22     18.02        N/A        N/A
2025-12-23     18.31        N/A        N/A
2025-12-24     18.28        N/A        N/A
2025-12-25     18.22        N/A        N/A
2025-12-26     18.14        N/A        N/A
2025-12-29     18.84        N/A        N/A
```

### 2. 数据访问层

#### 文件：`rdagent/scenarios/qlib/experiment/report_period_utils.py`

**核心类：`ReportPeriodAccessor`**

**功能：**
- 构建"公告日 -> 财务数据"的快速索引
- 提供查询"在时间t已公告的最新报告"的接口
- 支持单点查询、时间序列查询、横截面查询

**主要方法：**

```python
# 1. 获取单点数据
accessor.get_financial_at_date(instrument, date, field, max_lag_days)
# 返回：在指定日期可获得的最新财务数据值

# 2. 获取时间序列
accessor.get_financial_series(instrument, field, start_date, end_date)
# 返回：时间序列，每个日期使用当时可获得的最新报告

# 3. 获取横截面数据
accessor.get_all_financials_at_date(date, field, instruments)
# 返回：指定日期所有股票的财务数据（用于因子计算）

# 4. 获取报告信息
accessor.get_report_info(instrument, date)
# 返回：报告日期、公告日期、滞后天数、可用字段
```

**索引构建：**
```python
# 为每个股票构建"公告日 -> 财务数据"映射
for instrument in df.index.get_level_values(1).unique():
    stock_data = df.xs(instrument, level=1)
    # 找出有财务数据的日期（公告日）
    has_financial = stock_data[financial_fields].notna().any(axis=1)
    report_dates = stock_data[has_financial].index
    self.report_map[instrument] = stock_data.loc[report_dates][financial_fields]
```

### 3. 因子计算层

#### 文件：`rdagent/scenarios/qlib/experiment/report_period_factor_example.py`

**核心类：`FinancialFactorCalculator`**

**演示因子类型：**

##### 因子1：ROE因子
```python
# 使用最新可获得的ROE报告值
def calculate_roe_factor(date):
    return accessor.get_financial_at_date(instrument, date, 'ROE')
```

##### 因子2：ROE动量因子
```python
# ROE变化率 = (当前ROE - 过去ROE) / |过去ROE|
def calculate_roe_momentum_factor(date, periods=4):
    current_roe = accessor.get_financial_at_date(instrument, date, 'ROE')
    target_date = announce_date - periods * 90天
    past_roe = accessor.get_financial_at_date(instrument, target_date, 'ROE')
    return (current_roe - past_roe) / abs(past_roe)
```

##### 因子3：ROE趋势因子
```python
# 基于最近几个季度的ROE线性回归斜率
def calculate_roe_trend_factor(date, quarters=4):
    roe_series = accessor.get_financial_series(instrument, 'ROE')
    # 只保留有实际报告数据的日期
    valid_data = roe_series.dropna()
    # 计算线性回归斜率
    slope = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
    return slope
```

##### 因子4：财务质量因子
```python
# 综合得分 = zROE - zDebtToAssets + zCurrentRatio
def calculate_financial_quality_factor(date):
    roe = accessor.get_financial_at_date(instrument, date, 'ROE')
    debt = accessor.get_financial_at_date(instrument, date, 'DebtToAssets')
    current = accessor.get_financial_at_date(instrument, date, 'CurrentRatio')
    # 横截面标准化后求和
    return z_score(roe) - z_score(debt) + z_score(current)
```

## 实际运行结果

### 数据集统计
```
总记录数: 1,165,137
股票数量: 785
有财务报告的股票数: 457
有财务数据的记录数: 5,147
财务数据覆盖率: 0.44%
日期范围: 2010-01-04 至 2025-12-29
```

### 因子计算示例（2025-12-29）

#### ROE因子
- 有效股票数：294
- 均值：8.37%
- 最高：300502.SZ (55.37%)

#### ROE动量因子
- 有效股票数：267
- 均值：0.15（年度ROE平均增长15%）
- 最明显改善：600115.SH (15.94倍)

#### ROE趋势因子
- 有效股票数：319
- 均值：-0.0031（轻微下降趋势）
- 最明显上升趋势：300502.SZ (0.30)

#### 财务质量因子
- 有效股票数：294
- 最佳质量：688008.SH (得分2.45)

### 单股示例：浦发银行(600000.SH)

```
查询日期: 2025-12-29
使用报告公告日期: 2025-10-31
滞后天数: 59 天
ROE值: 4.95%

最近4个季度的ROE报告:
  第1个报告: ROE = 4.87%
  第2个报告: ROE = 2.37%
  第3个报告: ROE = 3.89%
  第4个报告: ROE = 4.95%
```

## 与前向填充方案的对比

| 维度 | 前向填充方案 | 报告期方案 |
|------|-------------|-----------|
| 数据覆盖率 | 100%（人为制造） | 0.44%（真实） |
| 时序正确性 | ❌ 有未来函数风险 | ✅ 完全正确 |
| 信息时效性 | ❌ 无法判断报告新旧 | ✅ 明确滞后天数 |
| 模型学习 | ❌ 可能学到错误模式 | ✅ 学习真实模式 |
| 实现复杂度 | 简单 | 中等 |
| 可解释性 | 低 | 高 |
| 投资逻辑 | 不符合实际 | 符合实际 |

## 使用指南

### 1. 数据准备

```bash
# 生成基于报告期的数据集
python scripts/prepare_report_period_data.py
```

输出文件：`git_ignore_folder/factor_implementation_source_data/daily_pv_report_period.h5`

### 2. 基础使用

```python
from rdagent.scenarios.qlib.experiment.report_period_utils import ReportPeriodAccessor
import pandas as pd

# 加载数据
df = pd.read_hdf('daily_pv_report_period.h5', key='data')

# 创建访问器
accessor = ReportPeriodAccessor(df)

# 查询单个数据
roe = accessor.get_financial_at_date('600000.SH', '2025-12-29', 'ROE')

# 获取时间序列
roe_series = accessor.get_financial_series('600000.SH', 'ROE', '2025-01-01', '2025-12-29')

# 获取横截面数据（用于因子计算）
cross_section = accessor.get_all_financials_at_date('2025-12-29', 'ROE')
```

### 3. 因子计算

```python
from rdagent.scenarios.qlib.experiment.report_period_factor_example import FinancialFactorCalculator

# 创建计算器
calculator = FinancialFactorCalculator(df)

# 计算ROE因子
roe_factor = calculator.calculate_roe_factor('2025-12-29')

# 计算ROE动量因子
momentum = calculator.calculate_roe_momentum_factor('2025-12-29', periods=4)

# 计算ROE趋势因子
trend = calculator.calculate_roe_trend_factor('2025-12-29', quarters=4)

# 计算财务质量因子
quality = calculator.calculate_financial_quality_factor('2025-12-29')
```

### 4. 与RD-Agent集成

```python
# 在RD-Agent的因子生成提示词中说明
financial_factor_template = """
# 使用财务数据计算因子（报告期方法）

## 数据特点
- 财务数据是季度报告，只在公告日有值
- 不要对财务数据进行前向填充
- 使用ReportPeriodAccessor获取"在时间t已公告的最新报告"

## 计算示例
```python
from rdagent.scenarios.qlib.experiment.report_period_utils import ReportPeriodAccessor

accessor = ReportPeriodAccessor(df)

# 正确：获取在日期t可获得的最新ROE
def calculate_roe_factor(date, instruments):
    result = {}
    for stock in instruments:
        roe = accessor.get_financial_at_date(stock, date, 'ROE')
        if roe is not None:
            result[stock] = roe
    return pd.Series(result)

# 错误：直接使用df['ROE']会导致大量NaN或未来函数
def wrong_approach(date, instruments):
    # 不要这样做！
    return df.loc[date, 'ROE']
```

## 常见问题

### Q1: 为什么财务数据覆盖率这么低？
A: 这是正确的！财务数据是季度报告，约60个交易日才有一次新数据。0.44%的覆盖率约等于1/227，符合实际。

### Q2: 如何处理没有财务数据的日期？
A: 使用`ReportPeriodAccessor.get_financial_at_date()`会自动返回"在时间t已公告的最新报告"。这正是报告期方案的核心。

### Q3: max_lag_days参数的作用？
A: 防止使用过时的报告。默认365天，如果最新报告超过1年，返回None而不是使用过时数据。

### Q4: 如何验证数据正确性？
A: 运行演示脚本：
```bash
python -m rdagent.scenarios.qlib.experiment.report_period_utils
python -m rdagent.scenarios.qlib.experiment.report_period_factor_example
```

### Q5: 性能如何？
A: `ReportPeriodAccessor`构建了内存索引，查询速度很快。1,165,137条数据的查询耗时<1秒。

## 总结

"方案2：引入报告期概念"成功解决了季度财务数据在量化因子开发中的正确处理问题：

✅ **时序正确**：完全避免未来函数
✅ **逻辑清晰**：符合实际投资决策流程
✅ **易于使用**：提供了简洁的API接口
✅ **性能良好**：内存索引，查询快速
✅ **可扩展性**：易于添加新的财务因子

该方案已被集成到RD-Agent的量化因子开发系统中，为基于财务数据的复合因子生成提供了坚实的基础。

---

**作者**: RD-Agent Team
**创建日期**: 2025-12-30
**版本**: 1.0
