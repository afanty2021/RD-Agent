#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成包含财务数据的价格数据文件

从Qlib系统读取最新的价格数据和财务数据，合并后生成HDF5文件。

使用方法：
    python generate.py

作者: RD-Agent Team
"""

import qlib
from qlib.data import D
import pandas as pd
from pathlib import Path


def normalize_code_for_financial(code: str) -> str:
    """将价格数据的代码转换为财务数据格式
    Qlib: SH600000, SZ000001 -> 财务: 000001.SZ, 600000.SH
    注意：需要保留前导零
    """
    if pd.isna(code):
        return code
    code = str(code)
    if code.startswith('SH'):
        # SH600000 -> 600000.SH (可能有前导零，保持原样)
        num_part = code[2:]
        return num_part + '.' + 'SH'
    elif code.startswith('SZ'):
        # SZ000001 -> 000001.SZ (保持前导零)
        return code[2:] + '.' + 'SZ'
    return code


def merge_financial_data(price_df: pd.DataFrame, market: str = "csi300") -> pd.DataFrame:
    """
    合并财务数据到价格数据中

    Args:
        price_df: 价格数据DataFrame（MultiIndex: datetime, instrument）
        market: 市场范围

    Returns:
        合并后的DataFrame（包含价格+财务数据）
    """
    # 财务数据路径
    financial_h5 = Path.home() / '.qlib/qlib_data/cn_data/financial_data/daily_pv_financial.h5'

    if not financial_h5.exists():
        print(f"  警告: 财务数据文件不存在: {financial_h5}")
        print(f"  只使用价格数据（不包含财务字段）")
        return price_df

    # 读取财务数据
    df_financial = pd.read_hdf(financial_h5, key='data')

    print(f"  财务数据: {len(df_financial)} 行 × {len(df_financial.columns)} 列")
    print(f"  时间范围: {df_financial.index.get_level_values(0).min()} 至 {df_financial.index.get_level_values(0).max()}")

    # 重置索引以便合并
    price_reset = price_df.reset_index()
    financial_reset = df_financial.reset_index()

    # 标准化价格数据的代码格式（匹配财务数据格式）
    price_reset['instrument_std'] = price_reset['instrument'].apply(normalize_code_for_financial)

    # 获取财务字段（包括基础字段）
    financial_cols = [col for col in financial_reset.columns
                     if col not in ['datetime', 'instrument']]

    # 准备合并数据
    financial_merge = financial_reset[['datetime', 'instrument'] + financial_cols].copy()

    # 执行合并（使用标准化的代码）
    merged_df = price_reset.merge(
        financial_merge,
        left_on=['datetime', 'instrument_std'],
        right_on=['datetime', 'instrument'],
        how='left'
    )

    # 删除临时列并使用标准化的代码（匹配财务数据格式）
    merged_df = merged_df.drop(columns=['instrument_x', 'instrument_y'])
    merged_df = merged_df.rename(columns={'instrument_std': 'instrument'})

    # 恢复MultiIndex（使用财务数据格式的代码）
    result = merged_df.set_index(['datetime', 'instrument'])

    # 统计财务字段覆盖率
    financial_data_cols = [col for col in financial_cols if col not in ['end_date', 'ann_date']]
    if financial_data_cols:
        coverage = result[financial_data_cols[0]].notna().sum() / len(result) * 100
        print(f"  财务数据覆盖率: {coverage:.2f}% (以{financial_data_cols[0]}为例)")
        print(f"  合并后总列数: {len(result.columns)} (价格6 + 其他2 + 财务{len(financial_data_cols)})")

    return result


def generate_data_files():
    """生成数据文件"""
    print("初始化Qlib...")
    qlib.init(provider_uri="~/.qlib/qlib_data/cn_data")

    # 获取所有股票（使用all market获取最大范围）
    print("获取股票列表...")
    instruments = D.instruments(market="all")
    print(f"  股票数量: {len(instruments)}")

    # 生成完整数据文件
    print("\n生成完整数据文件 (daily_pv_all.h5)...")
    price_fields = ["$open", "$close", "$high", "$low", "$volume", "$factor"]

    print("  读取价格数据...")
    price_data = D.features(
        instruments,
        price_fields,
        freq="day"
    ).swaplevel().sort_index().loc["2000-01-01":].sort_index()  # 从2000年开始

    print(f"  价格数据: {len(price_data)} 行")
    print(f"  时间范围: {price_data.index.get_level_values(0).min()} 至 {price_data.index.get_level_values(0).max()}")

    # 合并财务数据
    print("  合并财务数据...")
    price_data = merge_financial_data(price_data, market="all")

    # 保存完整数据
    price_data.to_hdf("./daily_pv_all.h5", key="data")
    print(f"  ✓ 已保存: daily_pv_all.h5 ({len(price_data)} 行 × {len(price_data.columns)} 列)")

    # 生成调试数据文件（部分股票，短时间范围）
    print("\n生成调试数据文件 (daily_pv_debug.h5)...")

    # 获取前100只股票的数据
    instruments_subset = list(instruments)[:100] if len(instruments) > 100 else list(instruments)

    price_debug = D.features(
        instruments_subset,
        price_fields,
        start_time="2018-01-01",
        end_time="2019-12-31",
        freq="day"
    ).swaplevel().sort_index()

    print(f"  调试数据: {len(price_debug)} 行")
    print(f"  时间范围: {price_debug.index.get_level_values(0).min()} 至 {price_debug.index.get_level_values(0).max()}")

    # 合并财务数据到调试数据
    price_debug = merge_financial_data(price_debug, market="debug")

    # 保存调试数据
    price_debug.to_hdf("./daily_pv_debug.h5", key="data")
    print(f"  ✓ 已保存: daily_pv_debug.h5 ({len(price_debug)} 行 × {len(price_debug.columns)} 列)")

    print("\n✅ 数据生成完成！")
    print(f"\n数据列:")
    for col in price_data.columns:
        print(f"  - {col}")


if __name__ == "__main__":
    generate_data_files()
