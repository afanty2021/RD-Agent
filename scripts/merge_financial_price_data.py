#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
合并财务数据和价格数据（修复股票代码格式）

处理股票代码格式不匹配问题：
- 价格数据：SH600000, SZ000001
- 财务数据：000001.SZ

作者: RD-Agent Team
"""

import pandas as pd
import numpy as np
from pathlib import Path


def normalize_instrument_code(code: str) -> str:
    """
    标准化股票代码格式

    转换规则：
    - SH600000 -> 600000.SH
    - SZ000001 -> 000001.SZ
    - 000001.SZ -> 000001.SZ（保持不变）
    """
    if pd.isna(code):
        return code

    code = str(code)

    # 如果已经是 000001.SZ 格式
    if '.' in code:
        return code

    # 如果是 SH600000 格式，转换为 600000.SH
    if code.startswith('SH'):
        return code[2:] + '.SH'
    elif code.startswith('SZ'):
        return code[2:] + '.SZ'

    return code


def normalize_financial_code(code: str) -> str:
    """
    将财务数据代码转换为价格数据格式

    转换规则：
    - 000001.SZ -> SZ000001
    """
    if pd.isna(code):
        return code

    code = str(code)

    if '.' in code:
        parts = code.split('.')
        if len(parts) == 2:
            stock_code, market = parts
            if market == 'SH':
                return 'SH' + stock_code
            elif market == 'SZ':
                return 'SZ' + stock_code

    return code


def merge_financial_with_price_fixed(
    financial_h5: str,
    price_h5: str,
    output_h5: str,
):
    """
    合并财务数据和价格数据（修复股票代码格式）

    Args:
        financial_h5: 财务数据HDF5文件
        price_h5: 价格数据HDF5文件
        output_h5: 输出合并后的HDF5文件
    """
    print("\n📊 合并财务数据和价格数据（修复股票代码格式）...")

    # 读取数据
    df_financial = pd.read_hdf(financial_h5, key='data')
    df_price = pd.read_hdf(price_h5, key='data')

    print(f"  财务数据: {len(df_financial)} 行 × {len(df_financial.columns)} 列")
    print(f"  价格数据: {len(df_price)} 行 × {len(df_price.columns)} 列")

    # 重置索引以便处理
    df_financial = df_financial.reset_index()
    df_price = df_price.reset_index()

    # 标准化股票代码格式
    print("  标准化股票代码格式...")
    df_financial['instrument_normalized'] = df_financial['instrument'].apply(normalize_financial_code)

    # 检查匹配情况
    price_codes = set(df_price['instrument'].unique())
    financial_codes_normalized = set(df_financial['instrument_normalized'].unique())

    matched_codes = price_codes & financial_codes_normalized
    print(f"  价格数据股票数: {len(price_codes)}")
    print(f"  财务数据股票数: {len(financial_codes_normalized)}")
    print(f"  匹配股票数: {len(matched_codes)}")

    # 准备合并
    financial_cols = [col for col in df_financial.columns if col not in ['datetime', 'instrument', 'instrument_normalized']]

    # 创建用于合并的财务数据
    df_financial_merge = df_financial[['datetime', 'instrument_normalized'] + financial_cols].copy()
    df_financial_merge = df_financial_merge.rename(columns={'instrument_normalized': 'instrument'})

    # 执行合并
    print("  执行合并操作...")
    df_merged = df_price.merge(df_financial_merge, on=['datetime', 'instrument'], how='left')

    print(f"  合并后数据: {len(df_merged)} 行 × {len(df_merged.columns)} 列")

    # 统计合并情况
    print("\n  财务字段覆盖率:")
    for col in financial_cols:
        if col in df_merged.columns:
            coverage = df_merged[col].notna().sum() / len(df_merged) * 100
            print(f"    {col}: {coverage:>6.2f}%")

    # 恢复MultiIndex
    df_result = df_merged.set_index(['datetime', 'instrument'])

    # 保存
    print(f"\n💾 保存合并数据到: {output_h5}")
    df_result.to_hdf(output_h5, key='data', mode='w')

    print(f"✅ 合并完成！")
    print(f"  文件大小: {Path(output_h5).stat().st_size / 1024 / 1024:.2f} MB")

    # 显示数据样例
    print("\n  合并数据样例:")
    sample = df_result.head(10)
    print(f"    列: {list(sample.columns)}")
    print(f"    数据:\n{sample}")

    return df_result


def main():
    """主函数"""
    financial_h5 = '~/.qlib/qlib_data/cn_data/financial_data/daily_pv_financial.h5'
    price_h5 = 'git_ignore_folder/factor_implementation_source_data/daily_pv.h5'
    output_h5 = '~/.qlib/qlib_data/cn_data/financial_data/daily_pv_financial_merged.h5'

    # 扩展路径
    financial_h5 = Path(financial_h5).expanduser()
    price_h5 = Path(price_h5).expanduser()
    output_h5 = Path(output_h5).expanduser()

    # 检查文件存在性
    if not financial_h5.exists():
        print(f"❌ 错误: 财务数据文件不存在: {financial_h5}")
        print(f"   请先运行: python scripts/convert_tushare_financial_to_hdf5.py")
        return

    if not price_h5.exists():
        print(f"❌ 错误: 价格数据文件不存在: {price_h5}")
        return

    # 执行合并
    merge_financial_with_price_fixed(
        financial_h5=str(financial_h5),
        price_h5=str(price_h5),
        output_h5=str(output_h5),
    )


if __name__ == "__main__":
    main()
