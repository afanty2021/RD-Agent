#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础财务因子示例
================

演示如何使用 daily_pv.h5 中的财务数据创建基础因子。

包含因子：
1. ROE Factor - 净资产收益率因子（盈利能力）
2. PE Factor - 市盈率因子（估值）
3. DebtToAssets Factor - 资产负债率因子（偿债风险）

数据来源：git_ignore_folder/factor_implementation_source_data/daily_pv.h5
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_data(data_path: str = None) -> pd.DataFrame:
    """
    加载 daily_pv.h5 数据

    Args:
        data_path: 数据文件路径，默认使用 README 中指定的路径

    Returns:
        MultiIndex DataFrame: (datetime, instrument) 索引，29列数据
    """
    if data_path is None:
        # 默认数据路径
        data_path = Path.home() / "git_ignore_folder/factor_implementation_source_data/daily_pv.h5"

    print(f"📂 正在加载数据: {data_path}")
    df = pd.read_hdf(data_path, key="data")
    print(f"✅ 数据加载完成！形状: {df.shape}")
    print(f"   - 时间范围: {df.index.get_level_values(0).min()} 到 {df.index.get_level_values(0).max()}")
    print(f"   - 股票数量: {df.index.get_level_values(1).nunique()}")

    return df


def calculate_roe_factor(df: pd.DataFrame) -> pd.DataFrame:
    """
    ROE (Return on Equity) 因子 - 盈利能力因子

    逻辑：
    - ROE = 净利润 / 股东权益
    - 高 ROE 表示公司盈利能力强
    - 使用截面 z-score 标准化

    学术依据：
    - Novy-Marx (2013): "The Other Side of Value: Gross Profitability Premium"
    - ROE 是最重要的盈利能力指标之一

    Args:
        df: 输入数据

    Returns:
        包含 ROE_factor 列的 DataFrame
    """
    print("\n" + "=" * 60)
    print("📊 因子 1: ROE (净资产收益率) - 盈利能力因子")
    print("=" * 60)

    # 重置索引以便操作
    df_reset = df.reset_index()

    # 检查 ROE 列是否存在
    if "ROE" not in df_reset.columns:
        raise ValueError("❌ 数据中没有 'ROE' 列！请确认数据文件包含财务数据。")

    # 计算截面 z-score 标准化
    df_reset["ROE_factor"] = df_reset.groupby("datetime")["ROE"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # 过滤掉 ROE 为空的行
    df_valid = df_reset[df_reset["ROE"].notna()].copy()

    # 统计信息
    print(f"✅ ROE 因子计算完成")
    print(f"   - 有效数据点: {len(df_valid):,}")
    print(f"   - ROE 范围: {df_valid['ROE'].min():.2f}% ~ {df_valid['ROE'].max():.2f}%")
    print(f"   - 因子均值: {df_valid['ROE_factor'].mean():.4f}")
    print(f"   - 因子标准差: {df_valid['ROE_factor'].std():.4f}")

    # 显示示例股票
    print(f"\n📈 ROE Top 5 股票（某一时点）:")
    sample_date = df_valid["datetime"].max()
    top_stocks = df_valid[df_valid["datetime"] == sample_date].nlargest(5, "ROE_factor")
    for idx, row in top_stocks.iterrows():
        print(f"   {row['instrument']}: ROE={row['ROE']:.2f}%, Factor={row['ROE_factor']:.4f}")

    # 返回 MultiIndex 格式
    result = df_valid.set_index(["datetime", "instrument"])
    return result[["ROE_factor"]]


def calculate_pe_factor(df: pd.DataFrame) -> pd.DataFrame:
    """
    PE (Price-to-Earnings) 因子 - 估值因子

    逻辑：
    - PE = 股价 / 每股收益
    - 低 PE 表示股票被低估（价值效应）
    - 使用截面排名百分比，然后取倒数

    学术依据：
    - Basu (1977): "Investment Performance of Common Stocks in Relation to Their Price-Earnings Ratios"
    - Fama and French (1992): 价值因子是重要的风险因子

    Args:
        df: 输入数据

    Returns:
        包含 PE_factor 列的 DataFrame
    """
    print("\n" + "=" * 60)
    print("📊 因子 2: PE (市盈率) - 估值因子")
    print("=" * 60)

    df_reset = df.reset_index()

    if "PE" not in df_reset.columns:
        raise ValueError("❌ 数据中没有 'PE' 列！")

    # 计算截面排名百分比 (0-100%)
    df_reset["PE_percentile"] = df_reset.groupby("datetime")["PE"].transform(
        lambda x: x.rank(pct=True)
    )

    # 取倒数：低 PE = 高因子值
    df_reset["PE_factor"] = 1 - df_reset["PE_percentile"]

    df_valid = df_reset[df_reset["PE"].notna()].copy()

    print(f"✅ PE 因子计算完成")
    print(f"   - 有效数据点: {len(df_valid):,}")
    print(f"   - PE 范围: {df_valid['PE'].min():.2f} ~ {df_valid['PE'].max():.2f}")
    print(f"   - 因子均值: {df_valid['PE_factor'].mean():.4f}")

    print(f"\n📈 价值因子 Top 5（低PE）股票（某一时点）:")
    sample_date = df_valid["datetime"].max()
    top_stocks = df_valid[df_valid["datetime"] == sample_date].nsmallest(5, "PE")
    for idx, row in top_stocks.iterrows():
        print(f"   {row['instrument']}: PE={row['PE']:.2f}, Factor={row['PE_factor']:.4f}")

    result = df_valid.set_index(["datetime", "instrument"])
    return result[["PE_factor"]]


def calculate_debt_to_assets_factor(df: pd.DataFrame) -> pd.DataFrame:
    """
    DebtToAssets 因子 - 偿债风险因子

    逻辑：
    - DebtToAssets = 总负债 / 总资产
    - 高负债率表示财务风险高
    - 使用截面 z-score 标准化，然后取负值（低负债 = 高因子值）

    学术依据：
    - Bhandari (1988): "Debt/Equity Ratio and Expected Common Stock Returns"
    - 低负债公司通常有更好的长期表现

    Args:
        df: 输入数据

    Returns:
        包含 DebtToAssets_factor 列的 DataFrame
    """
    print("\n" + "=" * 60)
    print("📊 因子 3: DebtToAssets (资产负债率) - 偿债风险因子")
    print("=" * 60)

    df_reset = df.reset_index()

    if "DebtToAssets" not in df_reset.columns:
        raise ValueError("❌ 数据中没有 'DebtToAssets' 列！")

    # 计算截面 z-score 标准化
    df_reset["DebtToAssets_zscore"] = df_reset.groupby("datetime")["DebtToAssets"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # 取负值：低负债 = 高因子值（低风险）
    df_reset["DebtToAssets_factor"] = -df_reset["DebtToAssets_zscore"]

    df_valid = df_reset[df_reset["DebtToAssets"].notna()].copy()

    print(f"✅ DebtToAssets 因子计算完成")
    print(f"   - 有效数据点: {len(df_valid):,}")
    print(f"   - DebtToAssets 范围: {df_valid['DebtToAssets'].min():.2%} ~ {df_valid['DebtToAssets'].max():.2%}")
    print(f"   - 因子均值: {df_valid['DebtToAssets_factor'].mean():.4f}")

    print(f"\n📈 低负债 Top 5 股票（某一时点）:")
    sample_date = df_valid["datetime"].max()
    top_stocks = df_valid[df_valid["datetime"] == sample_date].nsmallest(5, "DebtToAssets")
    for idx, row in top_stocks.iterrows():
        print(f"   {row['instrument']}: DebtToAssets={row['DebtToAssets']:.2%}, Factor={row['DebtToAssets_factor']:.4f}")

    result = df_valid.set_index(["datetime", "instrument"])
    return result[["DebtToAssets_factor"]]


def main():
    """主函数：演示所有基础财务因子的计算"""
    print("\n" + "=" * 60)
    print("🎯 基础财务因子示例")
    print("=" * 60)

    # 加载数据
    df = load_data()

    # 计算各个因子
    roe_result = calculate_roe_factor(df)
    pe_result = calculate_pe_factor(df)
    debt_result = calculate_debt_to_assets_factor(df)

    # 合并所有因子
    print("\n" + "=" * 60)
    print("📊 合并所有因子")
    print("=" * 60)

    all_factors = pd.concat([roe_result, pe_result, debt_result], axis=1)
    print(f"✅ 因子合并完成！形状: {all_factors.shape}")
    print(f"\n因子相关性矩阵:")
    print(all_factors.corr())

    # 保存结果
    output_path = Path("ex01_basic_financial_factors_output.h5")
    all_factors.to_hdf(output_path, key="data")
    print(f"\n💾 结果已保存到: {output_path}")

    print("\n" + "=" * 60)
    print("✨ 所有基础财务因子计算完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
