#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tushare财务数据转换为HDF5格式

功能：
1. 读取Tushare下载的财务数据CSV文件
2. 转换为Qlib兼容的MultiIndex格式
3. 生成包含财务数据的HDF5文件
4. 支持增量更新

使用方法：
    python scripts/convert_tushare_financial_to_hdf5.py

作者: RD-Agent Team
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Optional
import argparse


# 核心财务指标映射（Tushare字段名 -> Qlib风格字段名）
FINANCIAL_FIELDS_MAPPING = {
    # 估值指标
    "eps": "EPS",                    # 每股收益
    "bps": "BPS",                    # 每股净资产
    "ocfps": "OCFPS",                # 每股经营现金流
    "cfps": "CFPS",                  # 每股现金流

    # 盈利能力
    "roe": "ROE",                    # 净资产收益率
    "roa": "ROA",                    # 总资产收益率
    "roic": "ROIC",                  # 投入资本回报率
    "netprofit_margin": "NetProfitMargin",  # 销售净利率
    "grossprofit_margin": "GrossProfitMargin",  # 销售毛利率

    # 成长能力
    "basic_eps_yoy": "EPS_Growth",   # 每股收益增长率
    "cfps_yoy": "CFPS_Growth",       # 每股现金流增长率
    "netprofit_yoy": "NetProfit_Growth",  # 净利润增长率
    "op_yoy": "OP_Growth",           # 营业利润增长率

    # 偿债能力
    "debt_to_assets": "DebtToAssets", # 资产负债率
    "current_ratio": "CurrentRatio", # 流动比率
    "quick_ratio": "QuickRatio",     # 速动比率
    "ocf_to_debt": "OCF_To_Debt",    # 现金流债务比

    # 运营能力
    "assets_turn": "AssetsTurnover", # 总资产周转率
    "ar_turn": "AR_Turnover",        # 应收账款周转率
    "ca_turn": "CA_Turnover",        # 流动资产周转率

    # 其他重要指标
    "ebitda": "EBITDA",              # 息税折旧摊销前利润
    "operating_profit": "OperatingProfit",  # 营业利润
}


def convert_financial_csv_to_hdf5(
    input_csv: str,
    output_h5: str,
    fields_mapping: Optional[dict] = None,
    min_date: Optional[str] = None,
    max_date: Optional[str] = None,
) -> pd.DataFrame:
    """
    转换Tushare财务数据CSV为HDF5格式

    Args:
        input_csv: 输入CSV文件路径
        output_h5: 输出HDF5文件路径
        fields_mapping: 字段映射字典，None则使用默认
        min_date: 最小日期（过滤）
        max_date: 最大日期（过滤）

    Returns:
        转换后的DataFrame
    """
    print(f"📂 读取财务数据: {input_csv}")

    # 读取CSV文件
    df = pd.read_csv(input_csv, encoding='utf-8-sig')

    print(f"  原始数据: {len(df)} 行 × {len(df.columns)} 列")

    # 基本数据清洗
    df = df[df['end_date'].notna()].copy()

    # 转换股票代码格式（000001.SZ -> 000001SZ）
    df['instrument'] = df['ts_code'].str.replace('.', '')

    # 转换日期格式
    df['datetime'] = pd.to_datetime(df['end_date'], format='%Y%m%d')

    # 选择字段映射
    if fields_mapping is None:
        fields_mapping = FINANCIAL_FIELDS_MAPPING

    # 选择要转换的字段（存在的字段）
    available_fields = {k: v for k, v in fields_mapping.items() if k in df.columns}
    print(f"  可用字段: {len(available_fields)}/{len(fields_mapping)}")
    print(f"  字段列表: {list(available_fields.values())}")

    # 创建新的DataFrame（包含原始的ts_code、end_date、ann_date列）
    base_cols = ['ts_code', 'end_date']
    if 'ann_date' in df.columns:
        base_cols.append('ann_date')
    df_selected = df[base_cols + list(available_fields.keys())].copy()

    # 重命名列
    df_selected = df_selected.rename(columns=available_fields)

    # 先去重（同一股票同一日期保留最新数据）
    sort_cols = ['ts_code', 'end_date']
    if 'ann_date' in df_selected.columns:
        sort_cols.append('ann_date')
    df_selected = df_selected.sort_values(sort_cols)
    df_selected = df_selected.drop_duplicates(subset=['ts_code', 'end_date'], keep='last')

    # 创建datetime列（用于索引）
    df_selected['datetime'] = pd.to_datetime(df_selected['end_date'], format='%Y%m%d')

    # 日期过滤
    if min_date:
        df_selected = df_selected[df_selected['datetime'] >= min_date]
    if max_date:
        df_selected = df_selected[df_selected['datetime'] <= max_date]

    # 设置MultiIndex
    df_result = df_selected.set_index(['datetime', 'ts_code'])
    df_result.index.names = ['datetime', 'instrument']

    # 移除全为NaN的列
    df_result = df_result.dropna(axis=1, how='all')

    # 转换数据类型
    for col in df_result.columns:
        df_result[col] = pd.to_numeric(df_result[col], errors='coerce')

    print(f"  转换后数据: {len(df_result)} 行 × {len(df_result.columns)} 列")
    print(f"  时间范围: {df_result.index.get_level_values(0).min()} 至 {df_result.index.get_level_values(0).max()}")
    print(f"  股票数量: {df_result.index.get_level_values(1).nunique()}")

    # 保存为HDF5
    print(f"💾 保存到: {output_h5}")
    df_result.to_hdf(output_h5, key='data', mode='w')

    print(f"✅ 转换完成！")
    print(f"  文件大小: {Path(output_h5).stat().st_size / 1024 / 1024:.2f} MB")

    return df_result


def merge_financial_with_price(
    financial_h5: str,
    price_h5: str,
    output_h5: str,
):
    """
    合并财务数据和价格数据

    Args:
        financial_h5: 财务数据HDF5文件
        price_h5: 价格数据HDF5文件
        output_h5: 输出合并后的HDF5文件
    """
    print("\n📊 合并财务数据和价格数据...")

    # 读取数据
    df_financial = pd.read_hdf(financial_h5, key='data')
    df_price = pd.read_hdf(price_h5, key='data')

    print(f"  财务数据: {len(df_financial)} 行 × {len(df_financial.columns)} 列")
    print(f"  价格数据: {len(df_price)} 行 × {len(df_price.columns)} 列")

    # 合并数据（保留所有列）
    df_merged = df_price.join(df_financial, how='left')

    # 统计合并情况
    financial_cols = set(df_financial.columns)
    price_cols = set(df_price.columns)

    print(f"  合并后数据: {len(df_merged)} 行 × {len(df_merged.columns)} 列")
    print(f"  价格字段: {len(price_cols)} 个")
    print(f"  财务字段: {len(financial_cols)} 个")

    # 统计财务字段的覆盖率
    for col in financial_cols:
        coverage = df_merged[col].notna().sum() / len(df_merged) * 100
        print(f"    {col}: {coverage:.1f}% 覆盖率")

    # 保存
    print(f"💾 保存合并数据到: {output_h5}")
    df_merged.to_hdf(output_h5, key='data', mode='w')

    print(f"✅ 合并完成！")
    print(f"  文件大小: {Path(output_h5).stat().st_size / 1024 / 1024:.2f} MB")

    return df_merged


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='转换Tushare财务数据为HDF5格式')
    parser.add_argument(
        '--input',
        type=str,
        default='~/.qlib/qlib_data/cn_data/financial_data/a_share_financial_latest.csv',
        help='输入CSV文件路径'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='~/.qlib/qlib_data/cn_data/financial_data/daily_pv_financial.h5',
        help='输出HDF5文件路径'
    )
    parser.add_argument(
        '--merge-price',
        type=str,
        default=None,
        help='价格数据HDF5文件路径（如果需要合并）'
    )
    parser.add_argument(
        '--min-date',
        type=str,
        default='2010-01-01',
        help='最小日期（过滤早于此日期的数据）'
    )
    parser.add_argument(
        '--max-date',
        type=str,
        default=None,
        help='最大日期（过滤晚于此日期的数据）'
    )

    args = parser.parse_args()

    # 扩展路径
    input_csv = Path(args.input).expanduser()
    output_h5 = Path(args.output).expanduser()

    if not input_csv.exists():
        print(f"❌ 错误: 输入文件不存在: {input_csv}")
        return

    # 创建输出目录
    output_h5.parent.mkdir(parents=True, exist_ok=True)

    # 转换财务数据
    df_financial = convert_financial_csv_to_hdf5(
        input_csv=str(input_csv),
        output_h5=str(output_h5),
        min_date=args.min_date,
        max_date=args.max_date,
    )

    # 如果指定了价格数据，进行合并
    if args.merge_price:
        price_h5 = Path(args.merge_price).expanduser()
        if price_h5.exists():
            merged_output = output_h5.parent / "daily_pv_financial_merged.h5"
            merge_financial_with_price(
                financial_h5=str(output_h5),
                price_h5=str(price_h5),
                output_h5=str(merged_output),
            )
        else:
            print(f"⚠️  警告: 价格数据文件不存在: {price_h5}")

    print("\n✅ 全部完成！")


if __name__ == "__main__":
    main()
