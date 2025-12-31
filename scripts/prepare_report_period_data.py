#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于报告期概念的财务数据处理

不进行前向填充，保留季度财务数据的时序特性。
在因子计算时，使用"在时间t已公告的最新报告"的数据。

使用方法：
    python scripts/prepare_report_period_data.py

作者: RD-Agent Team
"""

import pandas as pd
import numpy as np
from pathlib import Path
import qlib
from qlib.data import D
from datetime import datetime


def normalize_qlib_code(code: str) -> str:
    """
    标准化Qlib股票代码格式以匹配财务数据

    Qlib格式: SH600000, SZ000001（大写，无点号）
    财务数据格式: 000001.SZ, 600000.SH（有点号，市场后缀）
    """
    if pd.isna(code):
        return code
    code = str(code)
    if code.startswith('SH'):
        return code[2:] + '.SH'
    elif code.startswith('SZ'):
        return code[2:] + '.SZ'
    return code


def load_financial_reports(financial_h5: str) -> pd.DataFrame:
    """
    加载财务报告数据，保留报告期和公告期信息

    Returns:
        DataFrame with columns:
        - instrument: 股票代码
        - end_date: 报告期（财务数据的实际期间）
        - ann_date: 公告期（报告发布的日期）
        - 其他财务字段
    """
    print(f"  读取财务数据: {financial_h5}")
    df = pd.read_hdf(financial_h5, key='data')

    # 重置索引以便处理
    df = df.reset_index()

    # 确保有end_date和ann_date字段
    if 'end_date' not in df.columns:
        print("  警告: 财务数据中没有end_date字段")
    if 'ann_date' not in df.columns:
        print("  警告: 财务数据中没有ann_date字段")

    print(f"  财务数据: {len(df)} 行 × {len(df.columns)} 列")

    # 显示报告期和公告期的范围
    if 'end_date' in df.columns:
        print(f"  报告期范围: {df['end_date'].min()} 至 {df['end_date'].max()}")
    if 'ann_date' in df.columns:
        print(f"  公告期范围: {df['ann_date'].min()} 至 {df['ann_date'].max()}")

    return df


def create_report_based_dataset(
    financial_h5: str,
    price_start_date: str = "2010-01-01",
    price_end_date: str = "2025-12-30",
    market: str = "csi300",
) -> pd.DataFrame:
    """
    创建基于报告期的数据集

    核心思想：
    1. 财务数据保持其季度特性（只在报告日有值）
    2. 价格数据是日频的
    3. 在计算因子时，对于任意日期t，使用该日期已公告的最新报告数据

    Args:
        financial_h5: 财务数据HDF5文件
        price_start_date: 价格数据起始日期
        price_end_date: 价格数据结束日期
        market: 市场范围

    Returns:
        合并后的DataFrame，保留财务数据的季度特性
    """
    print("\n📊 创建基于报告期的数据集...")

    # 初始化Qlib
    print("  初始化Qlib系统...")
    qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")

    # 获取股票列表
    instruments = D.instruments(market=market)
    print(f"  股票数量: {len(instruments)}")

    # 读取价格数据（日频）
    print(f"  读取价格数据 ({price_start_date} 至 {price_end_date})...")
    price_fields = ["$open", "$close", "$high", "$low", "$volume", "$factor"]

    price_data = D.features(
        instruments,
        price_fields,
        start_time=price_start_date,
        end_time=price_end_date,
        freq="day"
    )

    if price_data.empty:
        print("  ❌ 错误: 价格数据为空")
        return None

    # 处理价格数据索引
    price_data = price_data.swaplevel().sort_index()
    price_data.index.names = ['datetime', 'instrument']

    print(f"  价格数据: {len(price_data)} 行 × {len(price_data.columns)} 列")
    print(f"  时间范围: {price_data.index.get_level_values(0).min()} 至 {price_data.index.get_level_values(0).max()}")

    # 读取财务报告数据
    df_financial = load_financial_reports(financial_h5)

    # 标准化股票代码
    print("  标准化股票代码格式...")
    price_reset = price_data.reset_index()
    price_reset['instrument_normalized'] = price_reset['instrument'].apply(normalize_qlib_code)

    # 准备财务数据（保留end_date和ann_date）
    print("  准备财务数据...")
    financial_cols = [col for col in df_financial.columns
                      if col not in ['datetime', 'instrument', 'end_date', 'ann_date']]

    # 创建财务报告的映射表
    # key: (instrument, ann_date) -> 财务数据
    print("  创建财务报告索引...")
    df_financial = df_financial.sort_values(['instrument', 'ann_date'])

    # 合并价格和财务数据（不进行前向填充）
    print("  合并价格和财务数据...")

    # 将财务数据转换为"公告日"视角
    # 即：在ann_date这一天，可以获得end_date的财务数据
    financial_by_announce = df_financial[['instrument', 'ann_date'] + financial_cols].copy()

    # 过滤掉没有公告日期的记录
    financial_by_announce = financial_by_announce.dropna(subset=['ann_date']).copy()

    # 转换ann_date为datetime类型（格式：20200408.0 -> 2020-04-08）
    financial_by_announce['datetime'] = pd.to_datetime(
        financial_by_announce['ann_date'].astype(float).astype(int),
        format='%Y%m%d',
        errors='coerce'
    )
    financial_by_announce = financial_by_announce.drop(columns=['ann_date'])

    # 与价格数据合并
    price_merge = price_reset[['datetime', 'instrument_normalized'] + price_fields].copy()
    price_merge = price_merge.rename(columns={'instrument_normalized': 'instrument'})

    # 使用左连接，保留所有价格数据
    # 财务数据只在公告日有值，其他日期为NaN
    df_merged = price_merge.merge(
        financial_by_announce,
        on=['datetime', 'instrument'],
        how='left'
    )

    print(f"  合并后数据: {len(df_merged)} 行 × {len(df_merged.columns)} 列")

    # 统计财务字段覆盖率
    print("\n  财务字段覆盖率（只在公告日有值）:")
    for col in financial_cols[:10]:
        if col in df_merged.columns:
            coverage = df_merged[col].notna().sum() / len(df_merged) * 100
            print(f"    {col}: {coverage:>6.2f}%")
    if len(financial_cols) > 10:
        print(f"    ... (还有{len(financial_cols) - 10}个字段)")

    # 恢复MultiIndex
    df_result = df_merged.set_index(['datetime', 'instrument'])

    return df_result


def save_report_period_dataset(
    df: pd.DataFrame,
    output_h5: str,
):
    """
    保存基于报告期的数据集

    同时保存：
    1. 主数据文件：价格数据 + 财务数据（财务数据只在公告日有值）
    2. 报告索引文件：用于快速查找"在时间t已公告的最新报告"
    """
    print(f"\n💾 保存基于报告期的数据集...")

    output_path = Path(output_h5)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存主数据文件
    df.to_hdf(output_h5, key='data', mode='w')
    print(f"  ✅ 主数据文件: {output_h5}")
    print(f"     文件大小: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

    # 显示数据样例
    print("\n  数据样例（查看财务数据的稀疏性）:")
    sample_stock = df.index.get_level_values(1).unique()[0]
    sample_data = df.xs(sample_stock, level=1).tail(20)

    print(f"  股票: {sample_stock}")
    print(f"  日期                收盘价    ROE        EPS")
    print(f"  {'='*55}")
    for dt, row in sample_data.iterrows():
        roe_val = row['ROE'] if 'ROE' in row and pd.notna(row['ROE']) else None
        eps_val = row['EPS'] if 'EPS' in row and pd.notna(row['EPS']) else None
        close_val = row['$close'] if pd.notna(row['$close']) else None

        roe_str = f"{roe_val:>8.4f}" if roe_val is not None else "      N/A"
        eps_str = f"{eps_val:>8.2f}" if eps_val is not None else "      N/A"
        close_str = f"{close_val:>8.2f}" if close_val is not None else "      N/A"

        print(f"  {dt.strftime('%Y-%m-%d')}  {close_str}  {roe_str}  {eps_str}")


def main():
    """主函数"""
    financial_h5 = '~/.qlib/qlib_data/cn_data/financial_data/daily_pv_financial.h5'
    output_h5 = 'git_ignore_folder/factor_implementation_source_data/daily_pv_report_period.h5'

    # 扩展路径
    financial_h5 = Path(financial_h5).expanduser()
    output_h5 = Path(output_h5).expanduser()

    # 检查文件存在性
    if not financial_h5.exists():
        print(f"❌ 错误: 财务数据文件不存在: {financial_h5}")
        return

    # 创建基于报告期的数据集
    df = create_report_based_dataset(
        financial_h5=str(financial_h5),
        price_start_date="2010-01-01",
        price_end_date="2025-12-30",
        market="csi300",
    )

    if df is not None:
        # 保存数据集
        save_report_period_dataset(df, str(output_h5))

        print("\n✅ 基于报告期的数据集创建完成！")
        print("\n📝 说明:")
        print("  - 价格数据: 日频，每天有值")
        print("  - 财务数据: 季度，只在公告日有值")
        print("  - 财务数据覆盖率约1%是正常的（季度/交易日 ≈ 1/60）")
        print("  - 在因子计算时，使用'在时间t已公告的最新报告'")


if __name__ == "__main__":
    main()
