#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
复合因子示例：价值 + 动量组合
==========================

演示如何结合技术面数据和财务数据创建复合因子。

价值 + 动量是学术界和业界公认的最有效因子组合之一：
- Asness, Moskowitz, and Pedersen (2013): "Value and Momentum Everywhere"
- 两个负相关的信号结合，提供更稳定的超额收益

数据来源：git_ignore_folder/factor_implementation_source_data/daily_pv.h5
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_data(data_path: str = None) -> pd.DataFrame:
    """加载 daily_pv.h5 数据"""
    if data_path is None:
        data_path = Path.home() / "git_ignore_folder/factor_implementation_source_data/daily_pv.h5"

    print(f"📂 正在加载数据: {data_path}")
    df = pd.read_hdf(data_path, key="data")
    print(f"✅ 数据加载完成！形状: {df.shape}")
    return df


def calculate_value_momentum_composite(
    df: pd.DataFrame,
    value_weight: float = 0.4,
    momentum_weight: float = 0.6,
    momentum_period: int = 20
) -> pd.DataFrame:
    """
    价值 + 动量复合因子

    价值信号：
    - 使用 PE (市盈率) 的倒数
    - 低 PE = 被低估 = 高价值得分
    - 计算方法：1 - 截面PE排名百分比

    动量信号：
    - 使用过去 N 日收益率
    - 高收益 = 强势 = 高动量得分
    - 计算方法：收益率截面 z-score 标准化

    复合因子：
    - 价值权重 * 价值信号 + 动量权重 * 动量信号
    - 推荐权重：价值 40%, 动量 60%
    - 两个信号负相关，结合后更稳定

    学术依据：
    - Asness et al. (2013): 价值和动量在全球市场都有效
    - 两者负相关，组合后可以平滑收益曲线

    Args:
        df: 输入数据
        value_weight: 价值因子权重（默认 0.4）
        momentum_weight: 动量因子权重（默认 0.6）
        momentum_period: 动量计算周期（默认 20 日）

    Returns:
        包含复合因子列的 DataFrame
    """
    print("\n" + "=" * 70)
    print("📊 价值 + 动量复合因子 (Value + Momentum Composite)")
    print("=" * 70)

    df_reset = df.reset_index()

    # ========== Step 1: 计算价值信号 ==========
    print("\n🔍 Step 1: 计算价值信号（低 PE = 高价值）")
    print("-" * 70)

    if "PE" not in df_reset.columns:
        raise ValueError("❌ 数据中没有 'PE' 列！")

    # PE 截面排名百分比
    df_reset["PE_percentile"] = df_reset.groupby("datetime")["PE"].transform(
        lambda x: x.rank(pct=True)
    )

    # 取倒数：低 PE = 高价值
    df_reset["value_signal"] = 1 - df_reset["PE_percentile"]

    pe_valid = df_reset[df_reset["PE"].notna()]
    print(f"✅ 价值信号计算完成")
    print(f"   - 有效数据点: {len(pe_valid):,}")
    print(f"   - PE 范围: {pe_valid['PE'].min():.2f} ~ {pe_valid['PE'].max():.2f}")
    print(f"   - 价值信号范围: {pe_valid['value_signal'].min():.4f} ~ {pe_valid['value_signal'].max():.4f}")

    # ========== Step 2: 计算动量信号 ==========
    print("\n🔍 Step 2: 计算动量信号（过去 20 日收益率）")
    print("-" * 70)

    # 过滤价格列
    if "$close" not in df_reset.columns:
        raise ValueError("❌ 数据中没有 '$close' 列！")

    # 计算 N 日收益率
    df_reset["returns_%dd" % momentum_period] = df_reset.groupby("instrument")["$close"].transform(
        lambda x: x.pct_change(periods=momentum_period)
    )

    # 收益率截面 z-score 标准化
    df_reset["momentum_signal"] = df_reset.groupby("datetime")["returns_%dd" % momentum_period].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    momentum_valid = df_reset[df_reset["returns_%dd" % momentum_period].notna()]
    print(f"✅ 动量信号计算完成")
    print(f"   - 有效数据点: {len(momentum_valid):,}")
    print(f"   - 收益率范围: {momentum_valid['returns_%dd' % momentum_period].min():.2%} ~ "
          f"{momentum_valid['returns_%dd' % momentum_period].max():.2%}")
    print(f"   - 动量信号范围: {momentum_valid['momentum_signal'].min():.4f} ~ "
          f"{momentum_valid['momentum_signal'].max():.4f}")

    # ========== Step 3: 计算复合因子 ==========
    print("\n🔍 Step 3: 计算复合因子")
    print("-" * 70)

    # 只保留同时有价值和动量信号的行
    df_valid = df_reset[
        df_reset["value_signal"].notna() &
        df_reset["momentum_signal"].notna()
    ].copy()

    # 加权组合
    df_valid["Value_Momentum_Combo"] = (
        df_valid["value_signal"] * value_weight +
        df_valid["momentum_signal"] * momentum_weight
    )

    print(f"✅ 复合因子计算完成")
    print(f"   - 权重配置: 价值 {value_weight:.0%} + 动量 {momentum_weight:.0%}")
    print(f"   - 有效数据点: {len(df_valid):,}")
    print(f"   - 复合因子范围: {df_valid['Value_Momentum_Combo'].min():.4f} ~ "
          f"{df_valid['Value_Momentum_Combo'].max():.4f}")
    print(f"   - 复合因子均值: {df_valid['Value_Momentum_Combo'].mean():.4f}")
    print(f"   - 复合因子标准差: {df_valid['Value_Momentum_Combo'].std():.4f}")

    # ========== Step 4: 信号相关性分析 ==========
    print("\n🔍 Step 4: 信号相关性分析")
    print("-" * 70)

    correlation = df_valid[["value_signal", "momentum_signal", "Value_Momentum_Combo"]].corr()
    print("信号相关系数矩阵:")
    print(correlation.round(4))

    # 学术研究发现：价值和动量通常呈负相关
    value_momentum_corr = correlation.loc["value_signal", "momentum_signal"]
    print(f"\n💡 学术洞察: 价值-动量相关性 = {value_momentum_corr:.4f}")
    if value_momentum_corr < 0:
        print("   ✓ 负相关！这正是预期结果，两个信号互补性强")
    else:
        print("   ⚠ 正相关！可能数据期段特殊，需进一步分析")

    # ========== Step 5: 示例股票展示 ==========
    print("\n🔍 Step 5: 示例股票分析（最新时点）")
    print("-" * 70)

    sample_date = df_valid["datetime"].max()
    sample_stocks = df_valid[df_valid["datetime"] == sample_date].copy()

    # 复合因子 Top 5
    print("\n📈 复合因子 Top 5 股票:")
    top5 = sample_stocks.nlargest(5, "Value_Momentum_Combo")
    for idx, row in top5.iterrows():
        print(f"   {row['instrument']}: "
              f"复合={row['Value_Momentum_Combo']:.4f}, "
              f"价值={row['value_signal']:.4f}, "
              f"动量={row['momentum_signal']:.4f}")

    # 低价值高动量（成长股特征）
    print("\n📈 成长股特征（低价值 + 高动量）Top 3:")
    growth_stocks = sample_stocks[
        (sample_stocks["value_signal"] < 0.3) &
        (sample_stocks["momentum_signal"] > 1.0)
    ].nlargest(3, "momentum_signal")
    if len(growth_stocks) > 0:
        for idx, row in growth_stocks.iterrows():
            print(f"   {row['instrument']}: "
                  f"价值={row['value_signal']:.4f}, "
                  f"动量={row['momentum_signal']:.4f}")
    else:
        print("   (当前时点无明显成长股)")

    # 高价值低动量（深度价值股特征）
    print("\n📈 价值股特征（高价值 + 低动量）Top 3:")
    value_stocks = sample_stocks[
        (sample_stocks["value_signal"] > 0.7) &
        (sample_stocks["momentum_signal"] < -0.5)
    ].nlargest(3, "value_signal")
    if len(value_stocks) > 0:
        for idx, row in value_stocks.iterrows():
            print(f"   {row['instrument']}: "
                  f"价值={row['value_signal']:.4f}, "
                  f"动量={row['momentum_signal']:.4f}")
    else:
        print("   (当前时点无明显深度价值股)")

    # 返回 MultiIndex 格式
    result = df_valid.set_index(["datetime", "instrument"])
    return result[["Value_Momentum_Combo", "value_signal", "momentum_signal"]]


def analyze_factor_stability(df: pd.DataFrame, factor_column: str = "Value_Momentum_Combo"):
    """
    分析因子的时间稳定性

    Args:
        df: 因子数据（MultiIndex格式）
        factor_column: 要分析的因子列名
    """
    print("\n" + "=" * 70)
    print("📊 因子稳定性分析")
    print("=" * 70)

    df_reset = df.reset_index()

    # 按月统计因子均值和标准差
    df_reset["year_month"] = df_reset["datetime"].dt.to_period("M")
    monthly_stats = df_reset.groupby("year_month")[factor_column].agg(["mean", "std", "count"])

    print("\n月度统计:")
    print(monthly_stats.tail(12))

    # 计算因子衰减（IC衰减）
    print("\n因子衰减分析（未来1-5日收益率相关性）:")

    # 合并价格数据计算未来收益
    df_with_returns = df_reset.copy()

    # 这里简化处理，实际使用时需要更完整的回测框架
    print("   （完整回测需要使用 Qlib 框架，此处仅做演示）")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🎯 复合因子示例：价值 + 动量组合")
    print("=" * 70)
    print("\n📚 学术背景:")
    print("   - Asness, Moskowitz, Pedersen (2013): 'Value and Momentum Everywhere'")
    print("   - 价值和动量是全球市场的两个核心异常收益因子")
    print("   - 两者负相关，组合后可显著提升风险调整后收益")
    print("   - 推荐权重：价值 40% + 动量 60%")

    # 加载数据
    df = load_data()

    # 计算复合因子
    result = calculate_value_momentum_composite(
        df,
        value_weight=0.4,
        momentum_weight=0.6,
        momentum_period=20
    )

    # 保存结果
    output_path = Path("ex02_composite_value_momentum_output.h5")
    result.to_hdf(output_path, key="data")
    print(f"\n💾 结果已保存到: {output_path}")

    # 稳定性分析
    analyze_factor_stability(result)

    print("\n" + "=" * 70)
    print("✨ 价值 + 动量复合因子计算完成！")
    print("=" * 70)
    print("\n🎯 使用建议:")
    print("   1. 该因子适合作为选股核心因子")
    print("   2. 建议与其他因子（质量、成长）结合使用")
    print("   3. 可根据市场状态动态调整价值/动量权重")
    print("   4. 使用 Qlib 框架进行完整回测验证")


if __name__ == "__main__":
    main()
