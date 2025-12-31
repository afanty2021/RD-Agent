#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证最终合并数据质量

使用方法：
    python scripts/verify_final_data.py

作者: RD-Agent Team
"""

import pandas as pd


def verify_final_data():
    """验证最终数据质量"""
    # 读取最终数据
    df = pd.read_hdf('git_ignore_folder/factor_implementation_source_data/daily_pv_financial.h5', key='data')

    print('=' * 60)
    print('最终数据验证报告')
    print('=' * 60)

    # 基本统计
    print(f'\n数据维度: {len(df)} 行 × {len(df.columns)} 列')
    print(f'时间范围: {df.index.get_level_values(0).min()} 至 {df.index.get_level_values(0).max()}')
    print(f'股票数量: {df.index.get_level_values(1).nunique()}')

    # 字段列表
    print(f'\n所有字段: {list(df.columns)}')

    # 财务字段覆盖率
    financial_cols = ['EPS', 'ROE', 'ROA', 'NetProfitMargin', 'DebtToAssets']
    print(f'\n主要财务字段覆盖率:')
    for col in financial_cols:
        if col in df.columns:
            coverage = df[col].notna().sum() / len(df) * 100
            non_null = df[col].notna().sum()
            print(f'  {col:20s}: {coverage:>6.2f}% ({non_null:,} / {len(df):,})')

    # 价格字段覆盖率
    price_cols = ['$open', '$close', '$high', '$low', '$volume']
    print(f'\n价格字段覆盖率:')
    for col in price_cols:
        if col in df.columns:
            coverage = df[col].notna().sum() / len(df) * 100
            print(f'  {col:10s}: {coverage:>6.2f}%')

    # 有财务数据的行统计
    has_financial = df[financial_cols].notna().any(axis=1).sum()
    print(f'\n至少有1个财务字段的行数: {has_financial:,} ({has_financial/len(df)*100:.2f}%)')

    # 显示最新数据样本
    print(f'\n最新数据样本 (2025-12-29):')
    latest_date = df.index.get_level_values(0).max()
    latest_data = df.loc[latest_date]
    sample_stocks = latest_data.index[:5]
    print(f'  日期: {latest_date}')
    for stock in sample_stocks:
        row = latest_data.loc[stock]
        roe_val = row['ROE'] if 'ROE' in row and pd.notna(row['ROE']) else None
        close_val = row['$close'] if '$close' in row and pd.notna(row['$close']) else None
        print(f'    {stock}: ROE={roe_val if roe_val is None else f"{roe_val:.4f}"}, Close={close_val if close_val is None else f"{close_val:.2f}"}')


if __name__ == "__main__":
    verify_final_data()
