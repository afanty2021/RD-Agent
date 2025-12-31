#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据前向填充处理

在量化投资中，财务数据需要前向填充：
- 财务数据是季度数据，只在财报发布时更新
- 价格数据是日度数据，每个交易日都有
- 使用最新披露的财务数据填充到下一个财报发布日之前

使用方法：
    python scripts/forward_fill_financial_data.py

作者: RD-Agent Team
"""

import pandas as pd
import numpy as np
from pathlib import Path


def forward_fill_financial_data(
    input_h5: str,
    output_h5: str,
    max_fill_days: int = 500,
) -> pd.DataFrame:
    """
    前向填充财务数据

    Args:
        input_h5: 输入HDF5文件路径
        output_h5: 输出HDF5文件路径
        max_fill_days: 最大填充天数（约1.5年交易日）

    Returns:
        填充后的DataFrame
    """
    print("\n📊 财务数据前向填充处理...")

    # 读取数据
    df = pd.read_hdf(input_h5, key='data')

    print(f"  原始数据: {len(df)} 行 × {len(df.columns)} 列")

    # 识别财务字段
    financial_cols = [
        'EPS', 'BPS', 'OCFPS', 'CFPS',
        'ROE', 'ROA', 'ROIC',
        'NetProfitMargin', 'GrossProfitMargin',
        'EPS_Growth', 'CFPS_Growth', 'NetProfit_Growth', 'OP_Growth',
        'DebtToAssets', 'CurrentRatio', 'QuickRatio', 'OCF_To_Debt',
        'AssetsTurnover', 'AR_Turnover', 'CA_Turnover', 'EBITDA'
    ]

    # 筛选存在的财务字段
    financial_cols = [col for col in financial_cols if col in df.columns]

    print(f"  财务字段数量: {len(financial_cols)}")

    # 重置索引以便处理
    df_reset = df.reset_index()

    # 统计原始覆盖率
    print("\n  原始财务字段覆盖率:")
    for col in financial_cols[:5]:  # 只显示前5个
        coverage = df_reset[col].notna().sum() / len(df_reset) * 100
        print(f"    {col}: {coverage:>6.2f}%")
    print(f"    ... (共{len(financial_cols)}个字段)")

    # 对每只股票分别进行前向填充
    print(f"\n  执行前向填充 (每只股票独立处理)...")

    # 按股票分组填充
    df_grouped = df_reset.groupby('instrument')

    # 对财务字段进行前向填充
    for col in financial_cols:
        # 对每只股票前向填充
        df_reset[col] = df_grouped[col].transform(
            lambda x: x.ffill(limit=max_fill_days)
        )

    # 统计填充后覆盖率
    print(f"\n  填充后财务字段覆盖率:")
    filled_stats = []
    for col in financial_cols[:5]:  # 只显示前5个
        before = df[col].notna().sum()
        after = df_reset[col].notna().sum()
        coverage_after = after / len(df_reset) * 100
        increase = after - before
        print(f"    {col}: {coverage_after:>6.2f}% (+{increase:,} 行)")
        filled_stats.append((col, after, before))
    print(f"    ... (共{len(financial_cols)}个字段)")

    # 恢复MultiIndex
    df_result = df_reset.set_index(['datetime', 'instrument'])

    # 只保留需要的列
    price_cols = ['$open', '$close', '$high', '$low', '$volume', '$factor']
    other_cols = ['end_date', 'ann_date']
    all_cols = price_cols + other_cols + financial_cols

    # 只选择存在的列
    existing_cols = [col for col in all_cols if col in df_result.columns]
    df_result = df_result[existing_cols]

    # 保存
    print(f"\n💾 保存填充数据到: {output_h5}")
    df_result.to_hdf(output_h5, key='data', mode='w')

    print(f"✅ 填充完成！")
    print(f"  文件大小: {Path(output_h5).stat().st_size / 1024 / 1024:.2f} MB")

    # 显示数据样例
    print(f"\n  填充后数据样例 (SH600000的ROE字段):")
    sample_stock = df_result.xs('SH600000', level=1).tail(20)
    if 'ROE' in sample_stock.columns:
        print(f"    日期              ROE      $close")
        for dt, row in sample_stock.iterrows():
            roe_val = row['ROE'] if pd.notna(row['ROE']) else None
            close_val = row['$close'] if pd.notna(row['$close']) else None
            print(f"    {dt.strftime('%Y-%m-%d')}  {roe_val if roe_val is None else f'{roe_val:>8.4f}'}  {close_val if close_val is None else f'{close_val:>8.2f}'}")

    return df_result


def main():
    """主函数"""
    input_h5 = '~/.qlib/qlib_data/cn_data/financial_data/daily_pv_financial_merged.h5'
    output_h5 = '~/.qlib/qlib_data/cn_data/financial_data/daily_pv_financial_filled.h5'

    # 扩展路径
    input_h5 = Path(input_h5).expanduser()
    output_h5 = Path(output_h5).expanduser()

    # 检查文件存在性
    if not input_h5.exists():
        print(f"❌ 错误: 输入文件不存在: {input_h5}")
        return

    # 执行前向填充
    forward_fill_financial_data(
        input_h5=str(input_h5),
        output_h5=str(output_h5),
        max_fill_days=500,  # 约1.5年交易日
    )


if __name__ == "__main__":
    main()
