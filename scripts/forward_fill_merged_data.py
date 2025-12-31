#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前向填充合并后的财务数据

使用方法：
    python scripts/forward_fill_merged_data.py

作者: RD-Agent Team
"""

import pandas as pd
import numpy as np
from pathlib import Path


def forward_fill_merged_data(
    input_h5: str,
    output_h5: str,
    max_fill_days: int = 500,
):
    """前向填充合并后的数据"""
    print("\n=== 前向填充合并数据 ===")

    # 读取数据
    df = pd.read_hdf(input_h5, key='data')
    print(f'原始数据: {len(df)} 行 × {len(df.columns)} 列')
    print(f'时间范围: {df.index.get_level_values(0).min()} 至 {df.index.get_level_values(0).max()}')

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
    print(f'\n财务字段数量: {len(financial_cols)}')

    # 原始覆盖率
    print('\n原始财务字段覆盖率:')
    for col in financial_cols[:5]:
        coverage = df[col].notna().sum() / len(df) * 100
        print(f'  {col}: {coverage:.2f}%')

    # 重置索引
    df_reset = df.reset_index()

    # 按股票分组进行前向填充
    print(f'\n执行前向填充（最大{max_fill_days}天）...')
    for col in financial_cols:
        df_reset[col] = df_reset.groupby('instrument')[col].transform(
            lambda x: x.ffill(limit=max_fill_days)
        )

    # 填充后覆盖率
    print(f'\n填充后财务字段覆盖率:')
    for col in financial_cols[:5]:
        before = df[col].notna().sum()
        after = df_reset[col].notna().sum()
        coverage = after / len(df_reset) * 100
        increase = after - before
        print(f'  {col}: {coverage:.2f}% (+{increase:,} 行)')

    # 恢复索引
    df_result = df_reset.set_index(['datetime', 'instrument'])

    # 保存
    print(f'\n保存填充后的数据: {output_h5}')
    df_result.to_hdf(output_h5, key='data', mode='w')

    print(f'✅ 填充完成！文件大小: {Path(output_h5).stat().st_size / 1024 / 1024:.2f} MB')

    # 验证
    print(f'\n验证数据样例 (600000.SH 最新10行):')
    try:
        sample = df_result.xs('600000.SH', level=1).tail(10)
        for dt, row in sample.iterrows():
            roe_val = row['ROE'] if 'ROE' in row and pd.notna(row['ROE']) else None
            close_col = '$close' if '$close' in row else None
            if close_col:
                close_val = row[close_col] if pd.notna(row[close_col]) else None
                print(f'  {dt.strftime("%Y-%m-%d")}: ROE={roe_val if roe_val is None else f"{roe_val:.4f}"}, Close={close_val if close_val is None else f"{close_val:.2f}"}')
            else:
                print(f'  {dt.strftime("%Y-%m-%d")}: ROE={roe_val if roe_val is None else f"{roe_val:.4f}"}')
    except KeyError:
        print("  600000.SH 不在数据中")


def main():
    input_h5 = 'git_ignore_folder/factor_implementation_source_data/daily_pv_financial.h5'
    output_h5 = 'git_ignore_folder/factor_implementation_source_data/daily_pv_financial.h5'

    forward_fill_merged_data(
        input_h5=input_h5,
        output_h5=output_h5,
        max_fill_days=500,
    )


if __name__ == "__main__":
    main()
