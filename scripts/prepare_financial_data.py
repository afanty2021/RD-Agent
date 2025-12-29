#!/usr/bin/env python3
"""
财务数据准备脚本
从 Tushare 或 AKShare 获取股票财务数据
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import sys


def fetch_financial_data_from_tushare(ts_token, stock_list, start_date, end_date):
    """
    从 Tushare 获取财务数据
    """
    try:
        import tushare as ts
        ts.set_token(ts_token)
        pro = ts.pro_api()
    except ImportError:
        print("❌ Tushare 未安装，请运行: pip install tushare")
        return None
    except Exception as e:
        print(f"❌ Tushare 初始化失败: {e}")
        return None

    all_data = []

    print(f"从 Tushare 获取 {len(stock_list)} 只股票的财务数据...")
    for i, ts_code in enumerate(stock_list):
        try:
            # 获取财务指标
            df = pro.fina_indicator(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            if not df.empty:
                all_data.append(df)
            print(f"  ✓ ({i+1}/{len(stock_list)}) {ts_code}: {len(df)} 条记录")
        except Exception as e:
            print(f"  ✗ ({i+1}/{len(stock_list)}) {ts_code}: {e}")
            continue

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        print(f"\n✓ 总共获取 {len(combined)} 条财务记录")
        return combined
    else:
        print("\n✗ 未能获取任何数据")
        return pd.DataFrame()


def fetch_financial_data_from_akshare(stock_list):
    """
    从 AKShare 获取财务数据
    """
    try:
        import akshare as ak
    except ImportError:
        print("❌ AKShare 未安装，请运行: pip install akshare")
        return None
    except Exception as e:
        print(f"❌ AKShare 初始化失败: {e}")
        return None

    all_data = []

    print(f"从 AKShare 获取 {len(stock_list)} 只股票的财务数据...")
    for i, symbol in enumerate(stock_list):
        try:
            # 转换代码格式：000001.SZ -> 000001
            stock_code = symbol[:6]

            # 获取资产负债表
            df_balance = ak.stock_balance_sheet_by_yearly_em(symbol=stock_code)
            df_balance['instrument'] = symbol
            all_data.append(df_balance)

            print(f"  ✓ ({i+1}/{len(stock_list)}) {symbol}: 资产负债表")

        except Exception as e:
            print(f"  ✗ ({i+1}/{len(stock_list)}) {symbol}: {e}")
            continue

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        print(f"\n✓ 总共获取 {len(combined)} 条财务记录")
        return combined
    else:
        print("\n✗ 未能获取任何数据")
        return pd.DataFrame()


def calculate_common_financial_ratios(df):
    """
    计算常见财务比率
    """
    df = df.copy()

    # ROE (净资产收益率) = 净利润 / 股东权益
    if 'net_profit' in df.columns and 'total_hldr_eqy_exc_min_int' in df.columns:
        df['ROE'] = df['net_profit'] / df['total_hldr_eqy_exc_min_int'].replace(0, np.nan)

    # ROA (总资产收益率) = 净利润 / 总资产
    if 'net_profit' in df.columns and 'total_assets' in df.columns:
        df['ROA'] = df['net_profit'] / df['total_assets'].replace(0, np.nan)

    # 资产负债率 = 总负债 / 总资产
    if 'total_liab' in df.columns and 'total_assets' in df.columns:
        df['Debt_Ratio'] = df['total_liab'] / df['total_assets'].replace(0, np.nan)

    # 流动比率 = 流动资产 / 流动负债
    if 'current_assets' in df.columns and 'current_liab' in df.columns:
        df['Current_Ratio'] = df['current_assets'] / df['current_liab'].replace(0, np.nan)

    # 速动比率 = (流动资产 - 存货) / 流动负债
    if 'current_assets' in df.columns and 'inventories' in df.columns and 'current_liab' in df.columns:
        df['Quick_Ratio'] = (df['current_assets'] - df['inventories']) / df['current_liab'].replace(0, np.nan)

    return df


def standardize_financial_data(df):
    """
    标准化财务数据格式
    """
    # 转换日期格式
    if 'end_date' in df.columns:
        df['datetime'] = pd.to_datetime(df['end_date'], format='%Y%m%d')
    elif 'report_date' in df.columns:
        df['datetime'] = pd.to_datetime(df['report_date'])
    elif 'date' in df.columns:
        df['datetime'] = pd.to_datetime(df['date'])

    # 转换股票代码格式
    if 'ts_code' in df.columns:
        df['instrument'] = df['ts_code'].apply(lambda x: f"{x[:2]}{x[3:]}" if '.' in x else f"SH{x[:6]}" if x.startswith('6') else f"SZ{x[:6]}")

    # 选择常用列
    common_columns = [
        'datetime', 'instrument',
        'pe', 'pb', 'ps',  # 估值指标
        'roe', 'roa',  # 盈利能力
        'debt_to_assets',  # 偿债能力
        'current_ratio',  # 流动比率
        'basic_eps',  # 每股收益
    ]

    # 检查哪些列存在
    available_cols = [col for col in common_columns if col in df.columns]
    result = df[available_cols].copy()

    # 重命名列为标准名称
    column_mapping = {
        'pe': 'PE',
        'pb': 'PB',
        'ps': 'PS',
        'roe': 'ROE',
        'roa': 'ROA',
        'debt_to_assets': 'Debt_Ratio',
        'current_ratio': 'Current_Ratio',
        'basic_eps': 'EPS',
    }

    result = result.rename(columns=column_mapping)

    return result


def save_financial_data(df, output_path='financial_data.csv'):
    """
    保存财务数据
    """
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n✓ 财务数据已保存到: {output_path}")
    print(f"  数据形状: {df.shape}")
    print(f"  日期范围: {df['datetime'].min()} 到 {df['datetime'].max()}")
    print(f"  股票数量: {df['instrument'].nunique()}")
    print(f"  列名: {', '.join(df.columns.tolist())}")


def create_sample_financial_data(output_path='financial_data.csv'):
    """
    创建示例财务数据（用于测试）
    """
    np.random.seed(42)

    # 创建示例日期范围
    dates = pd.date_range('2020-01-01', '2023-12-31', freq='Q')  # 季度数据

    # 示例股票
    instruments = ['SH600000', 'SH600036', 'SH600519', 'SZ000001', 'SZ000002']

    data = []
    for date in dates:
        for inst in instruments:
            # 生成合理的财务数据
            pe = np.random.uniform(5, 50)
            pb = np.random.uniform(0.5, 5)
            roe = np.random.uniform(0.05, 0.30)
            roa = np.random.uniform(0.01, 0.15)
            debt_ratio = np.random.uniform(0.2, 0.8)

            data.append({
                'datetime': date,
                'instrument': inst,
                'PE': pe,
                'PB': pb,
                'ROE': roe,
                'ROA': roa,
                'Debt_Ratio': debt_ratio,
            })

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')

    print(f"✓ 已创建示例财务数据: {output_path}")
    print(f"  {len(df)} 条记录")
    print(f"  {len(instruments)} 只股票")
    print(f"  {len(dates)} 个时间点")

    return df


def generate_financial_factors_documentation():
    """
    生成财务因子说明文档
    """
    doc = """# 财务数据使用说明

## 可用的财务指标

### 估值指标
- **PE** (市盈率): 股价 / 每股收益。越低越被低估
- **PB** (市净率): 股价 / 每股净资产。越低越被低估
- **PS** (市销率): 股价 / 每股销售额。适用于亏损公司

### 盈利能力指标
- **ROE** (净资产收益率): 净利润 / 净资产。衡量股东回报率
- **ROA** (总资产收益率): 净利润 / 总资产。衡量资产使用效率

### 风险指标
- **Debt_Ratio** (资产负债率): 总负债 / 总资产。衡量财务杠杆

## 使用方法

### 在因子代码中加载财务数据

\`\`\`python
def calculate_Financial_Factor():
    import pandas as pd
    import numpy as np

    # 读取价格数据
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 读取财务数据
    try:
        financial_df = pd.read_csv('financial_data.csv')
        df_reset = df_reset.merge(financial_df, on=['datetime', 'instrument'], how='left')
    except FileNotFoundError:
        print("财务数据文件不存在")
        return

    # 计算因子（例如：价值因子）
    df_reset['PE_ZScore'] = df_reset.groupby('datetime')['PE'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )
    df_reset['Value_Factor'] = -df_reset['PE_ZScore']  # 低 PE 是好的

    result = df_reset.set_index(['datetime', 'instrument'])[['Value_Factor']]
    result.to_hdf('result.h5', key='data')
\`\`\`

## 数据文件格式

财务数据 CSV 文件应包含以下列：
- datetime: 日期
- instrument: 股票代码
- PE, PB, PS: 估值指标
- ROE, ROA: 盈利能力指标
- Debt_Ratio: 财务杠杆指标
- ... 更多指标

## 注意事项

1. 财务数据通常是季度或年度数据
2. 需要与价格数据的时间对齐
3. 使用 merge 时注意处理缺失值
4. 建议使用 Z-score 标准化不同量级的指标
"""

    return doc


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="准备财务数据")
    parser.add_argument("--source", choices=['tushare', 'akshare', 'sample'], default='sample',
                        help="数据源：tushare, akshare, sample")
    parser.add_argument("--token", help="Tushare API token")
    parser.add_argument("--stocks", nargs='+', help="股票代码列表")
    parser.add_argument("--start", default="20200101", help="开始日期")
    parser.add_argument("--end", default="20231231", help="结束日期")
    parser.add_argument("--output", default="financial_data.csv", help="输出文件")

    args = parser.parse_args()

    print("=" * 60)
    print("财务数据准备工具")
    print("=" * 60)

    if args.source == 'sample':
        print("\n创建示例财务数据...")
        df = create_sample_financial_data(args.output)

    elif args.source == 'tushare':
        if not args.token or not args.stocks:
            print("使用 Tushare 需要提供 token 和股票列表")
            print("示例: python prepare_financial_data.py --source tushare --token YOUR_TOKEN --stocks 000001.SZ 600000.SH")
        else:
            df = fetch_financial_data_from_tushare(args.token, args.stocks, args.start, args.end)
            if not df.empty:
                df = standardize_financial_data(df)
                df = calculate_common_financial_ratios(df)
                save_financial_data(df, args.output)

    elif args.source == 'akshare':
        if not args.stocks:
            print("使用 AKShare 需要提供股票列表")
            print("示例: python prepare_financial_data.py --source akshare --stocks 000001 600000")
        else:
            df = fetch_financial_data_from_akshare(args.stocks)
            if not df.empty:
                df = standardize_financial_data(df)
                df = calculate_common_financial_ratios(df)
                save_financial_data(df, args.output)

    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
