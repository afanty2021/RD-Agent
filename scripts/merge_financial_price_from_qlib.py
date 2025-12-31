#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从Qlib系统合并财务数据和价格数据

直接从Qlib数据系统读取最新价格数据，避免使用旧的HDF5文件。

使用方法：
    python scripts/merge_financial_price_from_qlib.py

作者: RD-Agent Team
"""

import pandas as pd
import numpy as np
from pathlib import Path
import qlib
from qlib.data import D


def normalize_qlib_code(code: str) -> str:
    """
    标准化Qlib股票代码格式以匹配财务数据

    Qlib格式: SH600000, SZ000001（大写，无点号）
    财务数据格式: 000001.SZ, 600000.SH（有点号，市场后缀）

    Args:
        code: Qlib格式的股票代码

    Returns:
        标准化后的代码（匹配财务数据格式）
    """
    if pd.isna(code):
        return code

    code = str(code)

    # Qlib格式: SH600000, SZ000001
    # 转换为财务数据格式: 600000.SH, 000001.SZ
    if code.startswith('SH'):
        return code[2:] + '.SH'
    elif code.startswith('SZ'):
        return code[2:] + '.SZ'

    return code


def merge_from_qlib_system(
    financial_h5: str,
    output_h5: str,
    market: str = "all",
    start_date: str = "2008-01-01",
    end_date: str = "2025-12-30",
):
    """
    从Qlib系统读取最新价格数据并与财务数据合并

    Args:
        financial_h5: 财务数据HDF5文件
        output_h5: 输出合并后的HDF5文件
        market: 市场范围 (csi300, csi500, all等)
        start_date: 起始日期
        end_date: 结束日期
    """
    print("\n📊 从Qlib系统合并财务数据和价格数据...")

    # 初始化Qlib
    print("  初始化Qlib系统...")
    qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")

    # 获取股票列表
    if market == "all":
        # 使用csi300作为基础（可根据需要调整）
        instruments = D.instruments(market="csi300")
    else:
        instruments = D.instruments(market=market)

    print(f"  股票数量: {len(instruments)}")

    # 读取价格数据（从Qlib系统）
    print(f"  读取价格数据 ({start_date} 至 {end_date})...")
    price_fields = ["$open", "$close", "$high", "$low", "$volume", "$factor"]

    price_data = D.features(
        instruments,
        price_fields,
        start_time=start_date,
        end_time=end_date,
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

    # 读取财务数据
    print(f"  读取财务数据: {financial_h5}")
    df_financial = pd.read_hdf(financial_h5, key='data')

    print(f"  财务数据: {len(df_financial)} 行 × {len(df_financial.columns)} 列")
    print(f"  时间范围: {df_financial.index.get_level_values(0).min()} 至 {df_financial.index.get_level_values(0).max()}")

    # 重置索引以便处理
    df_financial = df_financial.reset_index()
    price_reset = price_data.reset_index()

    # 标准化股票代码格式
    print("  标准化股票代码格式...")
    price_reset['instrument_normalized'] = price_reset['instrument'].apply(normalize_qlib_code)

    # 检查匹配情况
    financial_codes = set(df_financial['instrument'].unique())
    price_codes_normalized = set(price_reset['instrument_normalized'].unique())

    matched_codes = financial_codes & price_codes_normalized
    print(f"  价格数据股票数: {len(price_codes_normalized)}")
    print(f"  财务数据股票数: {len(financial_codes)}")
    print(f"  匹配股票数: {len(matched_codes)}")

    # 准备合并财务数据
    financial_cols = [col for col in df_financial.columns if col not in ['datetime', 'instrument']]
    df_financial_merge = df_financial[['datetime', 'instrument'] + financial_cols].copy()

    # 准备合并价格数据
    price_merge = price_reset[['datetime', 'instrument_normalized'] + price_fields].copy()
    price_merge = price_merge.rename(columns={'instrument_normalized': 'instrument'})

    # 执行合并
    print("  执行合并操作...")
    df_merged = price_merge.merge(df_financial_merge, on=['datetime', 'instrument'], how='left')

    print(f"  合并后数据: {len(df_merged)} 行 × {len(df_merged.columns)} 列")

    # 统计财务字段覆盖率
    print("\n  财务字段覆盖率:")
    for col in financial_cols[:10]:  # 只显示前10个
        if col in df_merged.columns:
            coverage = df_merged[col].notna().sum() / len(df_merged) * 100
            print(f"    {col}: {coverage:>6.2f}%")
    if len(financial_cols) > 10:
        print(f"    ... (还有{len(financial_cols) - 10}个字段)")

    # 恢复MultiIndex
    df_result = df_merged.set_index(['datetime', 'instrument'])

    # 保存
    print(f"\n💾 保存合并数据到: {output_h5}")
    Path(output_h5).parent.mkdir(parents=True, exist_ok=True)
    df_result.to_hdf(output_h5, key='data', mode='w')

    print(f"✅ 合并完成！")
    print(f"  文件大小: {Path(output_h5).stat().st_size / 1024 / 1024:.2f} MB")

    # 显示数据样例
    print("\n  合并数据样例:")
    sample = df_result.head(5)
    print(f"    列: {list(sample.columns)}")
    print(f"    数据:\n{sample}")

    return df_result


def main():
    """主函数"""
    financial_h5 = '~/.qlib/qlib_data/cn_data/financial_data/daily_pv_financial.h5'
    output_h5 = 'git_ignore_folder/factor_implementation_source_data/daily_pv_financial.h5'

    # 扩展路径
    financial_h5 = Path(financial_h5).expanduser()
    output_h5 = Path(output_h5).expanduser()

    # 检查文件存在性
    if not financial_h5.exists():
        print(f"❌ 错误: 财务数据文件不存在: {financial_h5}")
        return

    # 执行合并
    merge_from_qlib_system(
        financial_h5=str(financial_h5),
        output_h5=str(output_h5),
        market="csi300",  # 使用CSI300，可根据需要调整
        start_date="2010-01-01",
        end_date="2025-12-30",
    )


if __name__ == "__main__":
    main()
