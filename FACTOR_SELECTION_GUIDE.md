# 双因子选股策略完整指南

## 📋 目录
1. [策略概述](#策略概述)
2. [因子说明](#因子说明)
3. [选股流程](#选股流程)
4. [使用方法](#使用方法)
5. [调仓策略](#调仓策略)
6. [风险控制](#风险控制)

---

## 策略概述

### 核心思想
通过**机器学习因子**挖掘股票的**预期收益**和**波动率制度**，选出具有较高上涨潜力的股票构建投资组合。

### 策略特点
- **双因子驱动**: 岭回归因子 + XGBoost因子
- **量化选股**: 基于因子得分排序选股
- **定期调仓**: 每20个交易日（约1个月）调仓一次
- **等权配置**: 选中的股票等权重配置

### 历史表现
| 指标 | 岭回归因子 | XGBoost因子 | 组合策略 |
|------|-----------|-------------|----------|
| 年化收益 | 13.31% | 13.12% | ~13.2% |
| IC | 0.0339 | 0.0354 | 0.034+ |
| 信息比率 | 1.46 | 1.42 | ~1.44 |

---

## 因子说明

### 因子1：滚动岭回归因子

**逻辑**: 使用60天滚动窗口的岭回归，动态加权4个特征预测次日收益率

**4个特征**:
1. **VAM₁₅** - 波动率调整动量: `15日动量 / 15日波动率`
2. **VSVN₅,₂₀** - 成交量激变: `5日成交量 / 20日成交量标准差`
3. **DDM₂₀** - 下行风险调整动量: `20日动量 / 20日下行偏差`
4. **RSI₁₀** - 相对强弱指标: `10日RSI`

**因子值含义**: 正值表示预测上涨，负值表示预测下跌

### 因子2：XGBoost波动率制度因子

**逻辑**: 使用XGBoost分类器预测未来5天波动率 regime

**输入特征**: 30个滞后特征（价格范围、成交量、动量各10个滞后）

**因子值含义**: 0-1之间的概率值，越高表示进入高波动率上涨阶段的可能性越大

---

## 选股流程

### Step 1: 数据准备
```python
import qlib
from qlib.data import D

# 初始化Qlib
qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region='cn')

# 获取沪深300成分股
instruments = D.instruments(market='csi300')

# 获取OHLCV数据
fields = ['$open', '$high', '$low', '$close', '$volume', '$turnover']
df = D.features(instruments, fields, '2023-01-01', '2024-12-31')
```

### Step 2: 计算因子
```python
# 计算岭回归因子
ridge_factor = calculate_ridge_regression_factor(df)

# 计算XGBoost因子
xgb_factor = calculate_xgboost_factor(df)

# 合并并标准化
combined = combine_factors(ridge_factor, xgb_factor)
```

### Step 3: 因子标准化（Z-score）
```python
# 按日期分组，计算横截面Z-score
combined['Ridge_Factor_zscore'] = combined.groupby('datetime')['Ridge_Factor'].transform(
    lambda x: (x - x.mean()) / x.std()
)
combined['XGBoost_Factor_zscore'] = combined.groupby('datetime')['XGBoost_Factor'].transform(
    lambda x: (x - x.mean()) / x.std()
)
```

### Step 4: 因子组合
```python
# 等权组合
combined['Combined_Factor'] = (
    combined['Ridge_Factor_zscore'] * 0.5 +
    combined['XGBoost_Factor_zscore'] * 0.5
)
```

### Step 5: 选股
```python
# 选择综合得分最高的50只股票
selected = combined[combined['datetime'] == '2024-12-31']
selected = selected.nlargest(50, 'Combined_Factor')
```

---

## 使用方法

### 快速开始

```bash
cd /Users/berton/Github/RD-Agent
python factor_selection_strategy.py
```

### 输出示例

```
============================================================
选股日期: 2024-12-31
============================================================
股票池总数: 300
符合阈值(>=0.5): 45
最终选中: 50只

前10只股票:
   1. 600519    - 综合得分:   2.35 (岭回归:  2.10, XGBoost:  2.60)
   2. 000858    - 综合得分:   2.15 (岭回归:  1.95, XGBoost:  2.35)
   3. 600036    - 综合得分:   2.05 (岭回归:  2.25, XGBoost:  1.85)
   ...
```

---

## 调仓策略

### 推荐调仓频率

| 周期 | 交易日历 | 适用场景 |
|------|----------|----------|
| **月度** | 每20个交易日 | 平衡换手率和因子稳定性（推荐） |
| **周度** | 每5个交易日 | 捕捉短期信号，换手率高 |
| **季度** | 每60个交易日 | 降低交易成本，适合长期资金 |

### 调仓流程

```python
# 1. 计算调仓日期
import pandas_market_calendars as mcal
cn_cal = mcal.get_calendar('XSHG')
trading_days = cn_cal.valid_days(start_date='2024-01-01', end_date='2024-12-31')
rebalance_dates = trading_days[::20]  # 每20天

# 2. 对每个调仓日执行选股
for date in rebalance_dates:
    date_str = date.strftime('%Y-%m-%d')
    selected_stocks = select_stocks(combined_factors, date_str, top_n=50)

    # 3. 卖出不在新名单的股票
    # 4. 买入新选中的股票
    # 5. 持有至下次调仓
```

---

## 风险控制

### 1. 行业中性化

```python
# 计算行业哑变量
industry_df = get_industry_classification(instruments)

# 对行业内股票进行因子标准化
combined['Ridge_Factor_neutral'] = combined.groupby(['datetime', 'industry'])['Ridge_Factor'].transform(
    lambda x: (x - x.mean()) / x.std()
)
```

### 2. 流通市值加权

```python
# 获取流通市值
market_cap = get_market_cap(instruments, date)

# 按市值加权而非等权
selected['weight'] = selected['market_cap'] / selected['market_cap'].sum()
```

### 3. 换手率控制

```python
# 限制单次调仓换手率不超过30%
prev_stocks = set(previous_portfolio)
new_stocks = set(selected_stocks)

sell_stocks = prev_stocks - new_stocks
buy_stocks = new_stocks - prev_stocks

turnover = (len(sell_stocks) + len(buy_stocks)) / (2 * len(prev_stocks))

if turnover > 0.3:
    # 只替换得分差异最大的部分
    replace_count = int(0.3 * len(prev_stocks))
    selected_stocks = partial_replacement(prev_stocks, new_stocks, replace_count)
```

### 4. 止损/止盈

```python
# 单只股票亏损超过15%止损
# 单只股票盈利超过30%止盈
for stock in current_portfolio:
    pnl = (current_price - entry_price) / entry_price
    if pnl <= -0.15:
        sell(stock, reason='stop_loss')
    elif pnl >= 0.30:
        sell(stock, reason='take_profit')
```

---

## 回测评估

### 使用Qlib回测

```python
from qlib.contrib.evaluate import risk_analysis
from qlib.backtest import backtest, executor

# 配置回测
executor_config = {
    'class': 'SimulatorExecutor',
    'module_path': 'qlib.backtest.executor',
    'kwargs': {
        'time_per_step': 'day',
        'generate_portfolio_metrics': True
    }
}

# 运行回测
portfolio_result, indicator_result = backtest(
    strategy=select_stocks_strategy,
    executor=executor_config,
    start_time='2023-01-01',
    end_time='2024-12-31'
)

# 分析结果
print(indicator_result)
```

### 关注指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| **年化收益率** | 策略年化收益 | >10% |
| **夏普比率** | 风险调整后收益 | >1.0 |
| **最大回撤** | 最大亏损幅度 | <20% |
| **换手率** | 每期交易比例 | <50% |
| **IC均值** | 因子预测能力 | >0.03 |
| **ICIR** | IC稳定性 | >0.5 |

---

## 实盘部署

### 数据更新

```python
# 每日盘后更新数据
def daily_update():
    # 1. 更新OHLCV数据
    update_ohlcv_data()

    # 2. 重新计算因子
    ridge_factor = calculate_ridge_regression_factor(latest_df)
    xgb_factor = calculate_xgboost_factor(latest_df)

    # 3. 检查是否需要调仓
    if is_rebalance_day():
        selected = select_stocks(combined_factors, latest_date)
        execute_trades(selected)
```

### 监控告警

```python
# 监控因子有效性
def monitor_factor_performance():
    latest_ic = calculate_ic(latest_factor_values, next_day_returns)

    if latest_ic < 0.01:
        send_alert("因子IC过低，可能失效！")

    if latest_ic < 0:
        send_alert("因子IC为负，考虑暂停使用！")
```

---

## 注意事项

1. **数据质量**: 确保OHLCV数据的准确性和完整性
2. **前视偏差**: 严格按时间顺序，避免使用未来数据
3. **交易成本**: 考虑佣金、印花税、滑点等交易成本
4. **市场环境**: 因子可能在特定市场环境下失效
5. **过拟合风险**: 定期检查样本外表现
6. **容量限制**: 考虑资金容量对小盘股的影响

---

## 常见问题

**Q: 为什么要用Z-score标准化？**
A: 因为两个因子的单位和量纲不同，直接相加不合理。Z-score标准化后，两个因子都在同一尺度上，可以等权组合。

**Q: 为什么选择50只股票？**
A: 50只股票是经验值，既保证了分散化，又不会过于分散导致跟踪误差过大。可以根据资金规模调整。

**Q: 调仓频率怎么选择？**
A: 月度（20个交易日）是平衡点。更频繁会增加交易成本，更少会降低因子有效性。

**Q: 因子失效怎么办？**
A: 停止使用，重新训练模型或寻找新因子。定期检查IC等指标。
