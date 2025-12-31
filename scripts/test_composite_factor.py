#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
复合因子生成测试

验证财务数据是否可以正常用于复合因子生成。

使用方法：
    python scripts/test_composite_factor.py

作者: RD-Agent Team
"""

import pandas as pd
import numpy as np
from pathlib import Path


def test_roe_trend_factor():
    """
    测试ROE趋势因子（财务因子）
    """
    print("\n" + "=" * 60)
    print("测试1: ROE趋势因子（财务因子）")
    print("=" * 60)

    # 读取数据
    df = pd.read_hdf('git_ignore_folder/factor_implementation_source_data/daily_pv_financial.h5', key='data')
    df_reset = df.reset_index()

    print(f"  数据加载: {len(df_reset)} 行 × {len(df_reset.columns)} 列")

    # 检查ROE字段可用性
    if 'ROE' not in df_reset.columns:
        print("  ❌ 错误: 数据中缺少ROE字段")
        return None

    roe_coverage = df_reset['ROE'].notna().sum() / len(df_reset) * 100
    print(f"  ROE覆盖率: {roe_coverage:.2f}%")

    if roe_coverage < 1:
        print("  ❌ 错误: ROE覆盖率太低，无法计算因子")
        return None

    # 计算ROE趋势因子
    df_reset = df_reset.sort_values(['instrument', 'datetime'])

    # 计算ROE的60日变化率
    df_reset['ROE_change'] = df_reset.groupby('instrument')['ROE'].transform(
        lambda x: x.pct_change(periods=60)
    )

    # 标准化ROE和ROE变化（横截面）
    df_reset['ROE_zscore'] = df_reset.groupby('datetime')['ROE'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )
    df_reset['ROE_change_zscore'] = df_reset.groupby('datetime')['ROE_change'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # ROE趋势因子 = 高ROE + 上升趋势
    df_reset['ROE_Trend'] = (
        df_reset['ROE_zscore'] * 0.5 +
        df_reset['ROE_change_zscore'] * 0.5
    )

    # 处理异常值
    df_reset['ROE_Trend'] = df_reset['ROE_Trend'].replace([np.inf, -np.inf], np.nan)

    # 统计结果
    factor_coverage = df_reset['ROE_Trend'].notna().sum() / len(df_reset) * 100
    print(f"  因子覆盖率: {factor_coverage:.2f}%")
    print(f"  因子均值: {df_reset['ROE_Trend'].mean():.4f}")
    print(f"  因子标准差: {df_reset['ROE_Trend'].std():.4f}")

    # 显示样本
    print(f"\n  因子值样本 (最新5个有值的股票):")
    sample = df_reset[df_reset['ROE_Trend'].notna()].tail(5)
    for _, row in sample.iterrows():
        print(f"    {row['instrument']} ({row['datetime'].strftime('%Y-%m-%d')}): "
              f"ROE={row['ROE']:.4f}, ROE_Trend={row['ROE_Trend']:.4f}")

    # 保存结果
    result = df_reset.set_index(['datetime', 'instrument'])[['ROE_Trend']]
    output_path = 'git_ignore_folder/test_roe_trend_factor.h5'
    result.to_hdf(output_path, key='data')
    print(f"\n  ✓ 因子已保存: {output_path}")

    return result


def test_quality_momentum_combo():
    """
    测试质量+动量组合因子（交互因子）
    """
    print("\n" + "=" * 60)
    print("测试2: 质量+动量组合因子（交互因子）")
    print("=" * 60)

    # 读取数据
    df = pd.read_hdf('git_ignore_folder/factor_implementation_source_data/daily_pv_financial.h5', key='data')
    df_reset = df.reset_index()

    print(f"  数据加载: {len(df_reset)} 行 × {len(df_reset.columns)} 列")

    # 检查所需字段
    required_fields = ['ROE', 'ROA', '$close']
    missing_fields = [f for f in required_fields if f not in df_reset.columns]
    if missing_fields:
        print(f"  ❌ 错误: 缺少字段 {missing_fields}")
        return None

    # 1. 质量信号（ROE + ROA）
    df_reset['ROE_zscore'] = df_reset.groupby('datetime')['ROE'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )
    df_reset['ROA_zscore'] = df_reset.groupby('datetime')['ROA'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )
    df_reset['quality_signal'] = (df_reset['ROE_zscore'] + df_reset['ROA_zscore']) / 2

    # 2. 动量信号（20日收益率）
    df_reset['momentum_signal'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=20)
    )
    df_reset['momentum_signal'] = df_reset.groupby('datetime')['momentum_signal'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # 3. 组合：质量(50%) + 动量(50%)
    df_reset['Quality_Momentum_Combo'] = (
        df_reset['quality_signal'] * 0.5 +
        df_reset['momentum_signal'] * 0.5
    )

    # 处理异常值
    df_reset['Quality_Momentum_Combo'] = df_reset['Quality_Momentum_Combo'].replace([np.inf, -np.inf], np.nan)

    # 统计结果
    factor_coverage = df_reset['Quality_Momentum_Combo'].notna().sum() / len(df_reset) * 100
    print(f"  因子覆盖率: {factor_coverage:.2f}%")
    print(f"  因子均值: {df_reset['Quality_Momentum_Combo'].mean():.4f}")
    print(f"  因子标准差: {df_reset['Quality_Momentum_Combo'].std():.4f}")

    # 显示样本
    print(f"\n  因子值样本 (最新5个有值的股票):")
    sample = df_reset[df_reset['Quality_Momentum_Combo'].notna()].tail(5)
    for _, row in sample.iterrows():
        print(f"    {row['instrument']} ({row['datetime'].strftime('%Y-%m-%d')}): "
              f"Quality={row['quality_signal']:.4f}, Momentum={row['momentum_signal']:.4f}, "
              f"Combo={row['Quality_Momentum_Combo']:.4f}")

    # 保存结果
    result = df_reset.set_index(['datetime', 'instrument'])[['Quality_Momentum_Combo']]
    output_path = 'git_ignore_folder/test_quality_momentum_combo.h5'
    result.to_hdf(output_path, key='data')
    print(f"\n  ✓ 因子已保存: {output_path}")

    return result


def test_available_fields():
    """
    测试所有可用字段的覆盖率
    """
    print("\n" + "=" * 60)
    print("测试3: 可用字段覆盖率统计")
    print("=" * 60)

    df = pd.read_hdf('git_ignore_folder/factor_implementation_source_data/daily_pv_financial.h5', key='data')

    print(f"  数据维度: {df.shape}")
    print(f"  时间范围: {df.index.get_level_values(0).min()} 至 {df.index.get_level_values(0).max()}")
    print(f"  股票数量: {df.index.get_level_values(1).nunique()}")

    # 按类别统计
    price_fields = ['$open', '$close', '$high', '$low', '$volume']
    financial_fields = [col for col in df.columns if col not in price_fields + ['$factor', 'end_date', 'ann_date']]

    print(f"\n  价格字段:")
    for col in price_fields:
        if col in df.columns:
            coverage = df[col].notna().sum() / len(df) * 100
            print(f"    {col:15s}: {coverage:>6.2f}%")

    print(f"\n  财务字段 ({len(financial_fields)}个):")
    for col in financial_fields[:10]:  # 只显示前10个
        coverage = df[col].notna().sum() / len(df) * 100
        print(f"    {col:20s}: {coverage:>6.2f}%")
    if len(financial_fields) > 10:
        print(f"    ... 还有 {len(financial_fields) - 10} 个字段")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("复合因子生成测试")
    print("=" * 60)

    # 测试1: 字段可用性
    test_available_fields()

    # 测试2: ROE趋势因子
    roe_result = test_roe_trend_factor()

    # 测试3: 质量+动量组合因子
    combo_result = test_quality_momentum_combo()

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

    if roe_result is not None and combo_result is not None:
        print("\n🎉 所有测试通过！财务数据可以正常用于复合因子生成。")
        print("\n📁 测试输出文件:")
        print("  - git_ignore_folder/test_roe_trend_factor.h5")
        print("  - git_ignore_folder/test_quality_momentum_combo.h5")
    else:
        print("\n⚠️  部分测试失败，请检查数据完整性。")


if __name__ == "__main__":
    main()
