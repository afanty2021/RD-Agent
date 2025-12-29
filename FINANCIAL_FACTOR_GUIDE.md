# 财务因子数据准备指南

## 概述

本指南说明如何为 RD-Agent 准备财务数据，以便生成基于公司基本面的量化因子。

## 财务因子类型

### 1. 估值因子 (Valuation Factors)

| 因子名称 | 公式 | 说明 |
|---------|------|------|
| **PE (市盈率)** | 股价 / 每股收益 | 衡量股票价格相对收益的水平 |
| **PB (市净率)** | 股价 / 每股净资产 | 衡量股票价格相对资产的水平 |
| **PS (市销率)** | 股价 / 每股销售额 | 适用于亏损公司的估值 |
| **EV/EBITDA** | 企业价值 / EBITDA | 排除资本结构影响的估值指标 |

**用途**：价值投资策略，寻找被低估的股票

### 2. 盈利能力因子 (Profitability Factors)

| 因子名称 | 公式 | 说明 |
|---------|------|------|
| **ROE (净资产收益率)** | 净利润 / 净资产 | 股东投资回报率 |
| **ROA (总资产收益率)** | 净利润 / 总资产 | 资产利用效率 |
| **ROIC (投入资本回报率)** | 税后净营业利润 / 投入资本 | 资本配置效率 |
| **毛利率** | (收入 - 成本) / 收入 | 产品竞争力 |
| **净利率** | 净利润 / 收入 | 整体盈利能力 |

**用途**：质量因子，寻找盈利能力强的公司

### 3. 成长性因子 (Growth Factors)

| 因子名称 | 公式 | 说明 |
|---------|------|------|
| **营收增长率** | (本期营收 - 上期) / 上期 | 业务扩张能力 |
| **净利润增长率** | (本期净利 - 上期) / 上期 | 盈利增长能力 |
| **EPS 增长率** | (本期EPS - 上期) / 上期 | 每股收益增长 |
| **ROE 变化率** | 本期ROE - 上期ROE | 盈利能力改善 |

**用途**：GARP 策略（合理价格成长），寻找高速成长的股票

### 4. 偿债能力因子 (Solvency Factors)

| 因子名称 | 公式 | 说明 |
|---------|------|------|
| **资产负债率** | 总负债 / 总资产 | 财务杠杆水平 |
| **流动比率** | 流动资产 / 流动负债 | 短期偿债能力 |
| **速动比率** | (流动资产 - 存货) / 流动负债 | 更严格的短期偿债能力 |
| **利息保障倍数** | EBIT / 利息支出 | 利息支付能力 |

**用途**：风险控制，避免高负债公司

### 5. 营运效率因子 (Efficiency Factors)

| 因子名称 | 公式 | 说明 |
|---------|------|------|
| **总资产周转率** | 营收 / 总资产 | 资产使用效率 |
| **存货周转率** | 营业成本 / 平均存货 | 存货管理效率 |
| **应收账款周转率** | 营收 / 平均应收账款 | 回款效率 |

**用途**：寻找运营效率高的公司

### 6. 现金流因子 (Cash Flow Factors)

| 因子名称 | 公式 | 说明 |
|---------|------|------|
| **经营现金流 / 营收** | 经营现金流 / 营业收入 | 现金收入质量 |
| **自由现金流** | 经营现金流 - 资本支出 | 可自由支配的现金 |
| **现金含量** | 经营现金流 / 净利润 | 利润现金含量 |

**用途**：现金流质量分析

## 数据获取方式

### 方式1：使用 Tushare API

```python
import tushare as ts

# 设置 token
ts.set_token('YOUR_TOKEN')
pro = ts.pro_api()

# 获取财务数据
df = pro.income(
    ts_code='000001.SZ',
    start_date='20200101',
    end_date='20231231',
    report_type='1'  # 1: 合并报表, 0: 单季
)

# 获取资产负债表
df_balance = pro.balancesheet(
    ts_code='000001.SZ',
    start_date='20200101',
    end_date='20231231'
)

# 获取现金流量表
df_cashflow = pro.cashflow(
    ts_code='000001.SZ',
    start_date='20200101',
    end_date='20231231'
)

# 获取盈利能力数据
df_fina = pro.fina_indicator(
    ts_code='000001.SZ',
    start_date='20200101',
    end_date='20231231'
)
```

### 方式2：使用 AKShare

```python
import akshare as ak

# 获取资产负债表
df_balance = ak.stock_balance_sheet_by_yearly_em(symbol="000001")

# 获取利润表
df_profit = ak.stock_profit_sheet_by_yearly_em(symbol="000001")

# 获取现金流量表
df_cashflow = ak.stock_cash_flow_sheet_by_yearly_em(symbol="000001")

# 获取财务指标
df_indicator = ak.stock_financial_analysis_indicator(symbol="000001")
```

### 方式3：使用本地数据文件

如果您已经下载了财务数据到本地：

```python
# 读取 CSV 文件
df = pd.read_csv('financial_data.csv')

# 读取 Excel 文件
df = pd.read_excel('financial_data.xlsx', sheet_name='Sheet1')

# 读取 HDF5 文件
df = pd.read_hdf('financial_data.h5', key='data')
```

## 数据格式要求

### 标准格式

财务数据文件应包含以下列：

| 列名 | 类型 | 说明 |
|------|------|------|
| `datetime` | datetime | 报告期或数据日期 |
| `instrument` | str | 股票代码（如 SH600000, SZ000001） |
| `PE` | float | 市盈率 |
| `PB` | float | 市净率 |
| `ROE` | float | 净资产收益率 |
| `ROA` | float | 总资产收益率 |
| `Revenue` | float | 营业收入 |
| `Net_Profit` | float | 净利润 |
| `Total_Debt` | float | 总负债 |
| `Total_Assets` | float | 总资产 |
| ... | ... | 更多财务指标 |

### 示例数据

```csv
datetime,instrument,PE,PB,ROE,ROA,Revenue,Net_Profit,Debt_Ratio
2020-03-31,SH600000,5.2,0.8,0.12,0.03,1000000,150000,0.45
2020-03-31,SH600036,6.1,0.9,0.15,0.04,1200000,180000,0.50
2020-03-31,SZ000001,8.5,1.2,0.18,0.05,2000000,300000,0.60
```

## 数据处理脚本

创建一个脚本 `prepare_financial_data.py`：

```python
#!/usr/bin/env python3
"""
准备财务数据用于 RD-Agent
"""

import pandas as pd
import numpy as np
from pathlib import Path
import tushare as ts
from datetime import datetime, timedelta


def fetch_financial_data_from_tushare(ts_token, stock_list, start_date, end_date):
    """
    从 Tushare 获取财务数据

    Parameters
    ----------
    ts_token : str
        Tushare API token
    stock_list : list
        股票代码列表（如 ['000001.SZ', '600000.SH']）
    start_date : str
        开始日期 (YYYYMMDD)
    end_date : str
        结束日期 (YYYYMMDD)

    Returns
    -------
    pd.DataFrame
        财务数据
    """
    ts.set_token(ts_token)
    pro = ts.pro_api()

    all_data = []

    for ts_code in stock_list:
        try:
            # 获取最新财务指标
            df = pro.fina_indicator(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            all_data.append(df)
        except Exception as e:
            print(f"获取 {ts_code} 数据失败: {e}")
            continue

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        return combined
    else:
        return pd.DataFrame()


def calculate_financial_ratios(raw_df):
    """
    计算财务比率

    Parameters
    ----------
    raw_df : pd.DataFrame
        原始财务数据

    Returns
    -------
    pd.DataFrame
        包含计算比率的财务数据
    """
    df = raw_df.copy()

    # 计算额外指标
    if 'total_revenue_ps' in df.columns and 'total_profit_ps' in df.columns:
        df['Net_Margin'] = df['total_profit_ps'] / df['total_revenue_ps']

    if 'roe_waa' not in df.columns and 'net_profit' in df.columns and 'total_hldr_eqy_exc_min_int' in df.columns:
        df['roe_waa'] = df['net_profit'] / df['total_hldr_eqy_exc_min_int']

    if 'debt_to_assets' not in df.columns and 'total_liab' in df.columns and 'total_assets' in df.columns:
        df['debt_to_assets'] = df['total_liab'] / df['total_assets']

    return df


def save_financial_data(df, output_path='financial_data.csv'):
    """
    保存财务数据

    Parameters
    ----------
    df : pd.DataFrame
        财务数据
    output_path : str
        输出文件路径
    """
    # 转换列名为标准格式
    column_mapping = {
        'ts_code': 'instrument',
        'end_date': 'datetime',
        'pe_ttm': 'PE',
        'pb_ttm': 'PB',
        'ps_ttm': 'PS',
        'roe_waa': 'ROE',
        'roa_waa': 'ROA',
        'debt_to_assets': 'Debt_Ratio',
    }

    df_renamed = df.rename(columns=column_mapping)

    # 确保有必需的列
    required_cols = ['datetime', 'instrument']
    if not all(col in df_renamed.columns for col in required_cols):
        print("警告：缺少必需的列")

    # 保存
    df_renamed.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✓ 财务数据已保存到: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="准备财务数据")
    parser.add_argument("--token", help="Tushare API token")
    parser.add_argument("--stocks", nargs='+', help="股票代码列表")
    parser.add_argument("--start", default="20200101", help="开始日期")
    parser.add_argument("--end", default="20231231", help="结束日期")
    parser.add_argument("--output", default="financial_data.csv", help="输出文件")

    args = parser.parse_args()

    if args.token and args.stocks:
        print("从 Tushare 获取财务数据...")
        df = fetch_financial_data_from_tushare(args.token, args.stocks, args.start, args.end)
        if not df.empty:
            df = calculate_financial_ratios(df)
            save_financial_data(df, args.output)
    else:
        print("请提供 Tushare token 和股票列表")
        print("示例: python prepare_financial_data.py --token YOUR_TOKEN --stocks 000001.SZ 600000.SH")
```

## 集成到 RD-Agent

### 步骤1：准备财务数据文件

```bash
# 使用 Tushare 获取数据
python prepare_financial_data.py \
    --token YOUR_TOKEN \
    --stocks 000001.SZ 600000.SH 600036.SH \
    --output financial_data.csv
```

### 步骤2：复制到工作空间

```bash
# 复制到数据模板目录
cp financial_data.csv rdagent/scenarios/qlib/experiment/factor_data_template/
```

### 步骤3：验证数据

```python
import pandas as pd

# 读取并检查数据
df = pd.read_csv('financial_data.csv')
print(f"数据形状: {df.shape}")
print(f"列名: {df.columns.tolist()}")
print(df.head())

# 检查数据范围
print(f"\n日期范围: {df['datetime'].min()} 到 {df['datetime'].max()}")
print(f"股票数量: {df['instrument'].nunique()}")
```

### 步骤4：启动 RD-Agent

现在 RD-Agent 可以使用财务数据生成因子：

```bash
python -m rdagent.app.qlib_rd_loop.factor --loop_n 30
```

## 常见财务因子实现

### 1. 价值因子

```python
def calculate_Value_Score():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 加载财务数据
    financial_df = pd.read_csv('financial_data.csv')
    df_reset = df_reset.merge(financial_df, on=['datetime', 'instrument'], how='left')

    # 计算价值得分（低 PE + 低 PB = 高价值得分）
    df_reset['PE_ZScore'] = df_reset.groupby('datetime')['PE'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )
    df_reset['PB_ZScore'] = df_reset.groupby('datetime')['PB'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # 低 PE 和 PB 是好的，所以取负值
    df_reset['Value_Score'] = -(df_reset['PE_ZScore'] + df_reset['PB_ZScore']) / 2

    result = df_reset.set_index(['datetime', 'instrument'])[['Value_Score']]
    result.to_hdf('result.h5', key='data')
```

### 2. 质量因子

```python
def calculate_Quality_Score():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 加载财务数据
    financial_df = pd.read_csv('financial_data.csv')
    df_reset = df_reset.merge(financial_df, on=['datetime', 'instrument'], how='left')

    # 计算质量得分（高 ROE + 高 ROA + 高净利率）
    df_reset['ROE_ZScore'] = df_reset.groupby('datetime')['ROE'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )
    df_reset['ROA_ZScore'] = df_reset.groupby('datetime')['ROA'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )
    df_reset['Net_Margin_ZScore'] = df_reset.groupby('datetime')['Net_Margin'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    df_reset['Quality_Score'] = (
        df_reset['ROE_ZScore'] * 0.4 +
        df_reset['ROA_ZScore'] * 0.3 +
        df_reset['Net_Margin_ZScore'] * 0.3
    )

    result = df_reset.set_index(['datetime', 'instrument'])[['Quality_Score']]
    result.to_hdf('result.h5', key='data')
```

### 3. 成长因子

```python
def calculate_Growth_Score():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 加载财务数据
    financial_df = pd.read_csv('financial_data.csv')
    df_reset = df_reset.merge(financial_df, on=['datetime', 'instrument'], how='left')

    # 计算成长得分（营收增长 + 利润增长）
    df_reset['Revenue_Growth_ZScore'] = df_reset.groupby('datetime')['Revenue_Growth'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )
    df_reset['Net_Profit_Growth_ZScore'] = df_reset.groupby('datetime')['Net_Profit_Growth'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    df_reset['Growth_Score'] = (
        df_reset['Revenue_Growth_ZScore'] * 0.5 +
        df_reset['Net_Profit_Growth_ZScore'] * 0.5
    )

    result = df_reset.set_index(['datetime', 'instrument'])[['Growth_Score']]
    result.to_hdf('result.h5', key='data')
```

## 最佳实践

### 1. 数据更新频率

- **季度数据**：每季度更新一次（3月31日、6月30日、9月30日、12月31日）
- **月度数据**：每月更新
- **TTM（Trailing Twelve Months）**：滚动12个月数据

### 2. 数据清洗

```python
# 处理缺失值
df = df.fillna(method='ffill')  # 前向填充
df = df.fillna(method='bfill')  # 后向填充

# 处理异常值
df['ROE'] = df['ROE'].clip(lower=0, upper=1)  # ROE 在 0-100% 之间
df['PE'] = df['PE'].clip(lower=0, upper=200)  # PE 在 0-200 之间

# 对数变换
df['Market_Cap_log'] = np.log(df['Market_Cap'])
```

### 3. 标准化方法

```python
# Z-score 标准化
df['ROE_ZScore'] = df.groupby('datetime')['ROE'].transform(
    lambda x: (x - x.mean()) / (x.std() + 1e-12)
)

# Min-Max 标准化
df['ROE_Normalized'] = df.groupby('datetime')['ROE'].transform(
    lambda x: (x - x.min()) / (x.max() - x.min() + 1e-12)
)

# Rank 标准化
df['ROE_Rank'] = df.groupby('datetime')['ROE'].rank(pct=True)
```

## 数据质量检查

```python
def check_financial_data_quality(df):
    """检查财务数据质量"""
    print("=" * 60)
    print("财务数据质量检查")
    print("=" * 60)

    # 1. 缺失值检查
    missing_pct = df.isnull().sum() / len(df) * 100
    print("\n缺失值比例:")
    print(missing_pct[missing_pct > 0].sort_values(ascending=False))

    # 2. 异常值检查
    print("\n异常值统计:")
    for col in ['PE', 'PB', 'ROE', 'ROA', 'Debt_Ratio']:
        if col in df.columns:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 3 * iqr
            upper = q3 + 3 * iqr
            outliers = ((df[col] < lower) | (df[col] > upper)).sum()
            print(f"  {col}: {outliers} 个异常值 ({outliers/len(df)*100:.2f}%)")

    # 3. 数据范围检查
    print("\n数据范围:")
    for col in ['PE', 'PB', 'ROE', 'Debt_Ratio']:
        if col in df.columns:
            print(f"  {col}: min={df[col].min():.4f}, max={df[col].max():.4f}, mean={df[col].mean():.4f}")

    # 4. 覆盖率检查
    print(f"\n数据覆盖率:")
    total_cells = len(df) * len(df.columns)
    available_cells = df.count().sum()
    coverage = available_cells / total_cells * 100
    print(f"  总体覆盖率: {coverage:.2f}%")

    # 5. 时间序列连续性
    if 'datetime' in df.columns and 'instrument' in df.columns:
        df['datetime'] = pd.to_datetime(df['datetime'])
        expected_records = df['instrument'].nunique() * df['datetime'].nunique()
        actual_records = len(df)
        print(f"  时间序列完整度: {actual_records/expected_records*100:.2f}%")

    print("=" * 60)
```

## 参考资料

- [Tushare 数据接口](https://tushare.pro/document/2)
- [AKShare 文档](https://akshare.akfamily.xyz/)
- [财务分析指标](https://www.investopedia.com/terms/f/financial-ratios.asp)

## 变更记录

- 2025-12-29: 初始版本，添加财务因子支持
- 集成了 5 个财务因子示例（PE、ROE、营收增长、负债率、综合得分）
- 提供了完整的数据获取和处理指南
