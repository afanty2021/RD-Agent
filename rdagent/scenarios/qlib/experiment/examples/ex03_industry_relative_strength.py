#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
行业相对强度因子示例
==================

演示如何使用行业分类数据创建行业中性因子。

行业中性因子的优势：
- 消除行业偏差，避免行业集中风险
- 在行业内选股，更公平地比较公司
- 降低组合的回撤和波动率

数据来源：
- 价格/财务数据：git_ignore_folder/factor_implementation_source_data/daily_pv.h5
- 行业分类：~/.qlib/qlib_data/cn_data/industry_data/tushare_stock_to_industry_dict_*.json

申万 2021 L2 行业分类：
- 110 个二级行业
- 覆盖 5,466 只 A 股
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict


def load_data(data_path: str = None) -> pd.DataFrame:
    """加载 daily_pv.h5 数据"""
    if data_path is None:
        data_path = Path.home() / "git_ignore_folder/factor_implementation_source_data/daily_pv.h5"

    print(f"📂 正在加载数据: {data_path}")
    df = pd.read_hdf(data_path, key="data")
    print(f"✅ 数据加载完成！形状: {df.shape}")
    return df


def load_industry_mapping() -> Dict[str, Dict]:
    """
    加载申万 2021 L2 行业分类映射

    Returns:
        行业映射字典: {股票代码: {'industry_l1': 一级行业, 'industry_l2': 二级行业}}
    """
    print("\n📂 正在加载行业分类映射...")

    # 查找最新的行业分类文件
    industry_dir = Path.home() / ".qlib/qlib_data/cn_data/industry_data"

    # 尝试查找 tushare 行业分类文件
    industry_files = list(industry_dir.glob("tushare_stock_to_industry_dict_*.json"))

    if not industry_files:
        raise FileNotFoundError(
            f"❌ 在 {industry_dir} 中找不到行业分类文件！\n"
            f"   请先运行数据准备脚本生成行业分类。"
        )

    # 使用最新的文件
    industry_file = sorted(industry_files)[-1]
    print(f"   使用文件: {industry_file.name}")

    with open(industry_file, "r", encoding="utf-8") as f:
        industry_mapping = json.load(f)

    print(f"✅ 行业分类加载完成！")
    print(f"   - 覆盖股票数: {len(industry_mapping):,}")

    # 统计行业数量
    l1_industries = set(v.get("industry_l1", "") for v in industry_mapping.values())
    l2_industries = set(v.get("industry_l2", "") for v in industry_mapping.values())

    print(f"   - 一级行业数: {len(l1_industries)}")
    print(f"   - 二级行业数: {len(l2_industries)}")

    return industry_mapping


def map_industry_to_dataframe(df: pd.DataFrame, industry_mapping: Dict) -> pd.DataFrame:
    """
    将行业分类映射到 DataFrame

    Args:
        df: 输入数据
        industry_mapping: 行业映射字典

    Returns:
        添加了行业列的 DataFrame
    """
    print("\n🔍 将行业分类映射到数据...")

    df_reset = df.reset_index()

    # 标准化股票代码格式（移除交易所后缀）
    df_reset["stock_code"] = df_reset["instrument"].str.replace(".", "")

    # 映射一级行业
    df_reset["industry_l1"] = df_reset["stock_code"].map(
        lambda x: industry_mapping.get(x, {}).get("industry_l1", "Unknown")
    )

    # 映射二级行业
    df_reset["industry_l2"] = df_reset["stock_code"].map(
        lambda x: industry_mapping.get(x, {}).get("industry_l2", "Unknown")
    )

    # 统计映射成功率
    total_stocks = len(df_reset["instrument"].unique())
    mapped_l1 = df_reset[df_reset["industry_l1"] != "Unknown"]["instrument"].nunique()
    mapped_l2 = df_reset[df_reset["industry_l2"] != "Unknown"]["instrument"].nunique()

    print(f"✅ 行业映射完成！")
    print(f"   - 总股票数: {total_stocks:,}")
    print(f"   - 一级行业映射成功: {mapped_l1:,} ({mapped_l1/total_stocks*100:.1f}%)")
    print(f"   - 二级行业映射成功: {mapped_l2:,} ({mapped_l2/total_stocks*100:.1f}%)")

    # 显示行业分布
    print(f"\n📊 二级行业分布（Top 10）:")
    l2_dist = df_reset[df_reset["industry_l2"] != "Unknown"]["industry_l2"].value_counts().head(10)
    for industry, count in l2_dist.items():
        print(f"   {industry}: {count:,} 条数据")

    return df_reset


def calculate_industry_relative_pe(df: pd.DataFrame) -> pd.DataFrame:
    """
    行业相对 PE 因子

    逻辑：
    - 在每个行业内计算 PE 的相对排名
    - 低 PE（相对行业）= 高价值
    - 这样可以消除行业间的估值差异

    学术依据：
    - 行业中性策略是量化投资的标准做法
    - 避免行业集中，降低组合风险
    - 在行业内比较更公平

    Args:
        df: 包含行业信息的 DataFrame

    Returns:
        包含行业相对 PE 因子的 DataFrame
    """
    print("\n" + "=" * 70)
    print("📊 行业相对 PE 因子 (Industry-Relative PE)")
    print("=" * 70)

    # 过滤有效数据
    df_valid = df[(df["PE"].notna()) & (df["industry_l2"] != "Unknown")].copy()

    print(f"\n🔍 Step 1: 计算行业内 PE 排名")
    print("-" * 70)

    # 在每个行业内计算 PE 百分位排名
    df_valid["PE_rank_industry"] = df_valid.groupby(["datetime", "industry_l2"])["PE"].transform(
        lambda x: x.rank(pct=True)
    )

    # 取倒数：低 PE = 高价值
    df_valid["Industry_Relative_PE"] = 1 - df_valid["PE_rank_industry"]

    print(f"✅ 行业相对 PE 计算完成")
    print(f"   - 有效数据点: {len(df_valid):,}")
    print(f"   - 涉及行业数: {df_valid['industry_l2'].nunique()}")
    print(f"   - 因子均值: {df_valid['Industry_Relative_PE'].mean():.4f}")
    print(f"   - 因子标准差: {df_valid['Industry_Relative_PE'].std():.4f}")

    # 分析行业分布
    print(f"\n🔍 Step 2: 行业价值分布分析")
    print("-" * 70)

    sample_date = df_valid["datetime"].max()
    sample_df = df_valid[df_valid["datetime"] == sample_date]

    # 按行业统计平均价值得分
    industry_value = sample_df.groupby("industry_l2")["Industry_Relative_PE"].agg(["mean", "count"])
    industry_value = industry_value.sort_values("mean", ascending=False)

    print(f"\n最新时点各行业平均价值得分（Top 10 低估值行业）:")
    for idx, (industry, row) in enumerate(industry_value.head(10).iterrows(), 1):
        print(f"   {idx:2d}. {industry:30s}: {row['mean']:.4f} (n={row['count']})")

    print(f"\n最新时点各行业平均价值得分（Bottom 5 高估值行业）:")
    for idx, (industry, row) in enumerate(industry_value.tail(5).iterrows(), 1):
        print(f"   {idx}. {industry:30s}: {row['mean']:.4f} (n={row['count']})")

    # 展示示例股票
    print(f"\n🔍 Step 3: 示例股票分析（最新时点）")
    print("-" * 70)

    # 选择几个代表性行业
    for industry in ["证券", "银行", "白酒", "半导体"]:
        industry_stocks = sample_df[sample_df["industry_l2"] == industry]
        if len(industry_stocks) > 0:
            print(f"\n   【{industry}】行业内价值排名 Top 3:")

            top3 = industry_stocks.nlargest(3, "Industry_Relative_PE")
            for _, row in top3.iterrows():
                print(f"      {row['instrument']:12s}: "
                      f"PE={row['PE']:7.2f}, "
                      f"行业相对PE={row['Industry_Relative_PE']:.4f}")

    # 返回 MultiIndex 格式
    result = df_valid.set_index(["datetime", "instrument"])
    return result[["Industry_Relative_PE"]]


def calculate_industry_relative_roe(df: pd.DataFrame) -> pd.DataFrame:
    """
    行业相对 ROE 因子

    逻辑：
    - 在每个行业内计算 ROE 的相对强度
    - 高 ROE（相对行业）= 高盈利能力
    - 这样可以识别行业内的优质公司

    Args:
        df: 包含行业信息的 DataFrame

    Returns:
        包含行业相对 ROE 因子的 DataFrame
    """
    print("\n" + "=" * 70)
    print("📊 行业相对 ROE 因子 (Industry-Relative ROE)")
    print("=" * 70)

    # 过滤有效数据
    df_valid = df[(df["ROE"].notna()) & (df["industry_l2"] != "Unknown")].copy()

    print(f"\n🔍 Step 1: 计算行业内 ROE 相对强度")
    print("-" * 70)

    # 在每个行业内计算 ROE z-score
    df_valid["ROE_zscore_industry"] = df_valid.groupby(["datetime", "industry_l2"])["ROE"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    print(f"✅ 行业相对 ROE 计算完成")
    print(f"   - 有效数据点: {len(df_valid):,}")
    print(f"   - 涉及行业数: {df_valid['industry_l2'].nunique()}")
    print(f"   - 因子均值: {df_valid['ROE_zscore_industry'].mean():.4f}")
    print(f"   - 因子标准差: {df_valid['ROE_zscore_industry'].std():.4f}")

    # 分析行业盈利能力分布
    print(f"\n🔍 Step 2: 行业盈利能力分布分析")
    print("-" * 70)

    sample_date = df_valid["datetime"].max()
    sample_df = df_valid[df_valid["datetime"] == sample_date]

    # 按行业统计平均 ROE 相对强度
    industry_roe = sample_df.groupby("industry_l2")["ROE_zscore_industry"].agg(["mean", "count"])
    industry_roe = industry_roe.sort_values("mean", ascending=False)

    print(f"\n最新时点各行业平均盈利能力（Top 10 强势行业）:")
    for idx, (industry, row) in enumerate(industry_roe.head(10).iterrows(), 1):
        print(f"   {idx:2d}. {industry:30s}: {row['mean']:.4f} (n={row['count']})")

    # 展示示例股票
    print(f"\n🔍 Step 3: 示例股票分析（最新时点）")
    print("-" * 70)

    # 选择几个代表性行业
    for industry in ["白酒", "银行", "证券", "半导体"]:
        industry_stocks = sample_df[sample_df["industry_l2"] == industry]
        if len(industry_stocks) > 0:
            print(f"\n   【{industry}】行业内 ROE 相对强度 Top 3:")

            top3 = industry_stocks.nlargest(3, "ROE_zscore_industry")
            for _, row in top3.iterrows():
                print(f"      {row['instrument']:12s}: "
                      f"ROE={row['ROE']:6.2f}%, "
                      f"行业相对ROE={row['ROE_zscore_industry']:.4f}")

    # 返回 MultiIndex 格式
    result = df_valid.set_index(["datetime", "instrument"])
    return result[["ROE_zscore_industry"]]


def calculate_industry_neutral_momentum(df: pd.DataFrame) -> pd.DataFrame:
    """
    行业中性动量因子

    逻辑：
    - 先计算原始动量（20日收益率）
    - 再在每个行业内标准化
    - 这样可以消除行业整体动量的影响

    优势：
    - 避免追高热门行业
    - 在行业内选择强势股票
    - 降低行业轮动风险

    Args:
        df: 包含行业信息的 DataFrame

    Returns:
        包含行业中性动量因子的 DataFrame
    """
    print("\n" + "=" * 70)
    print("📊 行业中性动量因子 (Industry-Neutral Momentum)")
    print("=" * 70)

    # 过滤有效数据
    df_valid = df[(df["industry_l2"] != "Unknown")].copy()

    print(f"\n🔍 Step 1: 计算 20 日收益率")
    print("-" * 70)

    # 计算收益率
    df_valid["returns_20d"] = df_valid.groupby("instrument")["$close"].transform(
        lambda x: x.pct_change(periods=20)
    )

    print(f"✅ 收益率计算完成")

    print(f"\n🔍 Step 2: 行业内收益率标准化")
    print("-" * 70)

    # 在每个行业内标准化收益率
    df_valid["Industry_Neutral_Momentum"] = df_valid.groupby(["datetime", "industry_l2"])["returns_20d"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # 移除 NaN
    df_valid = df_valid[df_valid["Industry_Neutral_Momentum"].notna()]

    print(f"✅ 行业中性动量计算完成")
    print(f"   - 有效数据点: {len(df_valid):,}")
    print(f"   - 涉及行业数: {df_valid['industry_l2'].nunique()}")

    # 分析行业动量分布
    print(f"\n🔍 Step 3: 行业动量分布分析")
    print("-" * 70)

    sample_date = df_valid["datetime"].max()
    sample_df = df_valid[df_valid["datetime"] == sample_date]

    # 按行业统计平均动量
    industry_momentum = sample_df.groupby("industry_l2")["Industry_Neutral_Momentum"].agg(["mean", "std", "count"])
    industry_momentum = industry_momentum.sort_values("mean", ascending=False)

    print(f"\n最新时点各行业平均动量（Top 10 强势行业）:")
    for idx, (industry, row) in enumerate(industry_momentum.head(10).iterrows(), 1):
        print(f"   {idx:2d}. {industry:30s}: {row['mean']:.4f} (std={row['std']:.4f}, n={row['count']})")

    # 展示示例股票
    print(f"\n🔍 Step 4: 示例股票分析（最新时点）")
    print("-" * 70)

    # 选择几个代表性行业
    for industry in ["白酒", "新能源发电", "银行"]:
        industry_stocks = sample_df[sample_df["industry_l2"] == industry]
        if len(industry_stocks) > 0:
            print(f"\n   【{industry}】行业中性动量 Top 3:")

            top3 = industry_stocks.nlargest(3, "Industry_Neutral_Momentum")
            for _, row in top3.iterrows():
                print(f"      {row['instrument']:12s}: "
                      f"收益率={row['returns_20d']:6.2%}, "
                      f"行业中性动量={row['Industry_Neutral_Momentum']:.4f}")

    # 返回 MultiIndex 格式
    result = df_valid.set_index(["datetime", "instrument"])
    return result[["Industry_Neutral_Momentum"]]


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🎯 行业相对强度因子示例")
    print("=" * 70)
    print("\n📚 理论基础:")
    print("   - 行业中性策略是量化投资的标准做法")
    print("   - 消除行业偏差，避免行业集中风险")
    print("   - 在行业内选股，更公平地比较公司")
    print("   - 降低组合回撤和波动率")

    try:
        # 加载数据
        df = load_data()

        # 加载行业分类
        industry_mapping = load_industry_mapping()

        # 映射行业到数据
        df_with_industry = map_industry_to_dataframe(df, industry_mapping)

        # 计算各个行业中性因子
        pe_result = calculate_industry_relative_pe(df_with_industry)
        roe_result = calculate_industry_relative_roe(df_with_industry)
        momentum_result = calculate_industry_neutral_momentum(df_with_industry)

        # 合并所有因子
        print("\n" + "=" * 70)
        print("📊 合并所有行业中性因子")
        print("=" * 70)

        all_factors = pd.concat([pe_result, roe_result, momentum_result], axis=1)
        print(f"✅ 因子合并完成！形状: {all_factors.shape}")

        # 因子相关性分析
        print(f"\n因子相关性矩阵:")
        print(all_factors.corr())

        # 保存结果
        output_path = Path("ex03_industry_relative_strength_output.h5")
        all_factors.to_hdf(output_path, key="data")
        print(f"\n💾 结果已保存到: {output_path}")

        print("\n" + "=" * 70)
        print("✨ 所有行业相对强度因子计算完成！")
        print("=" * 70)
        print("\n🎯 使用建议:")
        print("   1. 行业中性因子适合构建稳健的多因子组合")
        print("   2. 可以与全市场因子结合，平衡行业暴露")
        print("   3. 建议定期检查行业分布，避免隐含行业偏差")
        print("   4. 使用 Qlib 框架进行完整回测验证")

    except FileNotFoundError as e:
        print(f"\n❌ 错误: {e}")
        print("\n💡 解决方案:")
        print("   1. 确保已准备行业分类数据")
        print("   2. 运行数据准备脚本生成行业映射文件")
        print("   3. 检查数据路径是否正确")


if __name__ == "__main__":
    main()
