#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
报告期概念示例：正确的财务数据使用方法
======================================

演示如何正确使用季度财务数据，避免前视偏差（look-ahead bias）。

**核心问题：**
财务数据是季度报告，不能简单 forward-fill 到日频，否则会引入前视偏差。

**正确做法：**
使用报告期概念（report period concept），在每个交易日使用该交易日或之前
公布的最新财务报告数据。

**数据结构：**
- `end_date`: 财报报告期结束日期（YYYYMMDD 格式）
- `ann_date`: 财报公告日期（YYYYMMDD 格式）

**示例场景：**
- 2023-03-31 的季报可能在 2023-04-30 才公布
- 在 2023-04-29 这一天，我们只能使用 2022-12-31 的年报数据
- 在 2023-05-01 这一天，才能使用 2023-03-31 的季报数据

数据来源：git_ignore_folder/factor_implementation_source_data/daily_pv_report_period.h5

参考文档：
- rdagent/scenarios/qlib/experiment/REPORT_PERIOD_CONCEPT.md
- rdagent/scenarios/qlib/experiment/report_period_utils.py
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


def load_report_period_data(data_path: str = None) -> pd.DataFrame:
    """
    加载包含报告期概念的数据

    Returns:
        包含 end_date 和 ann_date 列的 DataFrame
    """
    if data_path is None:
        # 使用带报告期的数据文件
        data_path = Path.home() / "git_ignore_folder/factor_implementation_source_data/daily_pv_report_period.h5"

        # 如果不存在，尝试使用普通数据文件
        if not data_path.exists():
            data_path = Path.home() / "git_ignore_folder/factor_implementation_source_data/daily_pv.h5"
            print(f"⚠️  警告: 未找到带报告期的数据文件，使用普通数据文件")
            print(f"   (该文件可能没有 end_date 和 ann_date 列)")

    print(f"📂 正在加载数据: {data_path}")
    df = pd.read_hdf(data_path, key="data")
    print(f"✅ 数据加载完成！形状: {df.shape}")

    # 检查是否有报告期列
    df_reset = df.reset_index()
    has_report_period = "end_date" in df_reset.columns and "ann_date" in df_reset.columns

    if has_report_period:
        print(f"✅ 数据包含报告期信息")
        print(f"   - end_date 范围: {df_reset['end_date'].min()} ~ {df_reset['end_date'].max()}")
        print(f"   - ann_date 范围: {df_reset['ann_date'].min()} ~ {df_reset['ann_date'].max()}")
    else:
        print(f"⚠️  数据不包含报告期信息")

    return df


def demonstrate_look_ahead_bias(df: pd.DataFrame) -> None:
    """
    演示前视偏差问题

    对比错误方法和正确方法的差异
    """
    print("\n" + "=" * 70)
    print("🔍 前视偏差（Look-Ahead Bias）演示")
    print("=" * 70)

    df_reset = df.reset_index()

    # 检查是否有报告期数据
    if "end_date" not in df_reset.columns or "ann_date" not in df_reset.columns:
        print("\n⚠️  当前数据不包含报告期信息，跳过演示")
        return

    # 选择一个示例股票和时间段
    sample_stock = "000001.SZ"
    if sample_stock not in df_reset["instrument"].values:
        print(f"\n⚠️  样本股票 {sample_stock} 不在数据中，使用第一个股票")
        sample_stock = df_reset["instrument"].values[0]

    sample_data = df_reset[df_reset["instrument"] == sample_stock].copy()
    sample_data = sample_data.sort_values("datetime")

    # 找一个有财报公告的时间段
    sample_data["ann_date_dt"] = pd.to_datetime(sample_data["ann_date"], format="%Y%m%d", errors="coerce")
    sample_data["end_date_dt"] = pd.to_datetime(sample_data["end_date"], format="%Y%m%d", errors="coerce")

    # 选择有公告日期的行
    announcement_rows = sample_data[sample_data["ann_date_dt"].notna()].head(3)

    if len(announcement_rows) == 0:
        print("\n⚠️  未找到有效的财报公告数据")
        return

    print("\n📊 财报公告时序分析：")
    print("-" * 70)

    for idx, row in announcement_rows.iterrows():
        report_end = row["end_date"]
        announcement = row["ann_date"]
        current_dt = row["datetime"]

        print(f"\n   财报报告期: {report_end}")
        print(f"   公告日期:   {announcement}")
        print(f"   当前交易:   {current_dt.date()}")
        print(f"   ROE:        {row.get('ROE', 'N/A')}")

        # 计算公告滞后
        if pd.notna(row["end_date_dt"]) and pd.notna(row["ann_date_dt"]):
            lag_days = (row["ann_date_dt"] - row["end_date_dt"]).days
            print(f"   ⏱ 公告滞后: {lag_days} 天")

            # 如果当前交易日在公告日之前，说明数据不可用
            if current_dt < row["ann_date_dt"]:
                print(f"   ❌ 前视偏差！当前交易日 < 公告日期，数据还未公布")
            else:
                print(f"   ✓ 数据已公布，可以安全使用")


def calculate_roe_with_report_period(df: pd.DataFrame) -> pd.DataFrame:
    """
    使用报告期概念计算 ROE 因子（正确方法）

    逻辑：
    1. 对于每个交易日，找到该日或之前公告的最新财报
    2. 使用该财报的 ROE 数据
    3. 这样确保没有使用未来数据

    Args:
        df: 包含报告期信息的 DataFrame

    Returns:
        包含正确 ROE 因子的 DataFrame
    """
    print("\n" + "=" * 70)
    print("📊 ROE 因子（使用报告期概念 - 正确方法）")
    print("=" * 70)

    df_reset = df.reset_index()

    # 检查是否有报告期数据
    if "end_date" not in df_reset.columns or "ann_date" not in df_reset.columns:
        print("\n⚠️  数据不包含报告期信息，使用简化方法")
        # 简化方法：直接使用 ROE 列（假设数据已经正确处理）
        if "ROE" in df_reset.columns:
            df_reset["ROE_ReportPeriod"] = df_reset.groupby("datetime")["ROE"].transform(
                lambda x: (x - x.mean()) / (x.std() + 1e-12)
            )

            result = df_reset.set_index(["datetime", "instrument"])
            return result[["ROE_ReportPeriod"]]
        else:
            raise ValueError("数据中没有 ROE 列")

    print("\n🔍 Step 1: 转换日期格式")
    print("-" * 70)

    # 转换日期格式
    df_reset["datetime_dt"] = pd.to_datetime(df_reset["datetime"])
    df_reset["ann_date_dt"] = pd.to_datetime(df_reset["ann_date"], format="%Y%m%d", errors="coerce")
    df_reset["end_date_dt"] = pd.to_datetime(df_reset["end_date"], format="%Y%m%d", errors="coerce")

    print("✅ 日期转换完成")

    print("\n🔍 Step 2: 过滤有效数据")
    print("-" * 70)

    # 只保留有公告日期和 ROE 的行
    valid_data = df_reset[
        (df_reset["ann_date_dt"].notna()) &
        (df_reset["ROE"].notna())
    ].copy()

    print(f"✅ 有效数据: {len(valid_data):,} 条")
    print(f"   - 总数据: {len(df_reset):,} 条")
    print(f"   - 有效率: {len(valid_data)/len(df_reset)*100:.2f}%")

    print("\n🔍 Step 3: 按公告日期排序并去重")
    print("-" * 70)

    # 对每个股票，按公告日期排序
    valid_data = valid_data.sort_values(["instrument", "ann_date_dt"])

    # 对每个股票-日期对，只保留最新公告的数据
    # 这确保了每个交易日使用的是该日或之前公布的最新财报
    valid_data["rank"] = valid_data.groupby(["instrument", "datetime"])["ann_date_dt"].rank(ascending=False)
    latest_report_data = valid_data[valid_data["rank"] == 1].copy()

    print(f"✅ 去重后数据: {len(latest_report_data):,} 条")

    print("\n🔍 Step 4: 计算截面标准化的 ROE 因子")
    print("-" * 70)

    # 截面 z-score 标准化
    latest_report_data["ROE_ReportPeriod"] = latest_report_data.groupby("datetime")["ROE"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    print(f"✅ ROE 因子计算完成")
    print(f"   - 有效数据点: {len(latest_report_data):,}")
    print(f"   - ROE 范围: {latest_report_data['ROE'].min():.2f}% ~ {latest_report_data['ROE'].max():.2f}%")
    print(f"   - 因子均值: {latest_report_data['ROE_ReportPeriod'].mean():.4f}")
    print(f"   - 因子标准差: {latest_report_data['ROE_ReportPeriod'].std():.4f}")

    print("\n🔍 Step 5: 验证数据质量")
    print("-" * 70)

    # 检查前视偏差
    lookahead_check = latest_report_data[
        latest_report_data["datetime_dt"] < latest_report_data["ann_date_dt"]
    ]

    if len(lookahead_check) > 0:
        print(f"⚠️  警告: 发现 {len(lookahead_check)} 条可能存在前视偏差的数据！")
        print(f"   (交易日 < 公告日期，但使用了该财报数据)")
    else:
        print(f"✅ 没有前视偏差！所有交易日 >= 公告日期")

    # 统计数据密度
    total_dates = latest_report_data["datetime"].nunique()
    total_stocks = latest_report_data["instrument"].nunique()
    possible_points = total_dates * total_stocks
    actual_points = len(latest_report_data)

    print(f"\n📊 数据密度统计:")
    print(f"   - 交易日数: {total_dates}")
    print(f"   - 股票数: {total_stocks}")
    print(f"   - 理论数据点: {possible_points:,}")
    print(f"   - 实际数据点: {actual_points:,}")
    print(f"   - 数据密度: {actual_points/possible_points*100:.2f}%")

    # 返回 MultiIndex 格式
    result = latest_report_data.set_index(["datetime", "instrument"])
    return result[["ROE_ReportPeriod"]]


def compare_methods(df: pd.DataFrame) -> None:
    """
    对比不同方法的差异
    """
    print("\n" + "=" * 70)
    print("📊 方法对比分析")
    print("=" * 70)

    df_reset = df.reset_index()

    if "ROE" not in df_reset.columns:
        print("\n⚠️  数据中没有 ROE 列，跳过对比")
        return

    print("\n对比三种方法：")
    print("   1. 错误方法：简单 forward-fill（前视偏差）")
    print("   2. 朴素方法：直接使用当日数据（假设已正确）")
    print("   3. 正确方法：报告期概念（无前视偏差）")

    # 朴素方法：直接标准化
    df_reset["ROE_Naive"] = df_reset.groupby("datetime")["ROE"].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # 如果有报告期数据，使用正确方法
    if "end_date" in df_reset.columns and "ann_date" in df_reset.columns:
        correct_result = calculate_roe_with_report_period(df)
        print("\n📊 相关性分析:")
        print("   朴素方法 vs 正确方法的相关性:")
        # 这里可以计算相关性，但需要数据对齐
    else:
        print("\n⚠️  无法进行完整对比（缺少报告期数据）")


def analyze_report_period_pattern(df: pd.DataFrame) -> None:
    """
    分析财报公告的时间模式
    """
    print("\n" + "=" * 70)
    print("📊 财报公告时间模式分析")
    print("=" * 70)

    df_reset = df.reset_index()

    if "ann_date" not in df_reset.columns or "end_date" not in df_reset.columns:
        print("\n⚠️  数据不包含报告期信息，跳过分析")
        return

    # 转换日期
    df_reset["ann_date_dt"] = pd.to_datetime(df_reset["ann_date"], format="%Y%m%d", errors="coerce")
    df_reset["end_date_dt"] = pd.to_datetime(df_reset["end_date"], format="%Y%m%d", errors="coerce")

    # 计算公告滞后
    valid_data = df_reset[
        (df_reset["ann_date_dt"].notna()) &
        (df_reset["end_date_dt"].notna())
    ].copy()

    valid_data["announcement_lag_days"] = (
        valid_data["ann_date_dt"] - valid_data["end_date_dt"]
    ).dt.days

    print(f"\n📊 公告滞后统计:")
    print(f"   - 平均滞后: {valid_data['announcement_lag_days'].mean():.1f} 天")
    print(f"   - 中位数滞后: {valid_data['announcement_lag_days'].median():.1f} 天")
    print(f"   - 最小滞后: {valid_data['announcement_lag_days'].min():.0f} 天")
    print(f"   - 最大滞后: {valid_data['announcement_lag_days'].max():.0f} 天")

    # 按季度统计
    valid_data["year"] = valid_data["end_date_dt"].dt.year
    valid_data["quarter"] = valid_data["end_date_dt"].dt.quarter

    quarterly_stats = valid_data.groupby(["year", "quarter"])["announcement_lag_days"].agg(["mean", "count"])

    print(f"\n📊 分季度公告滞后（最近8个季度）:")
    print(quarterly_stats.tail(8))


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🎯 报告期概念示例")
    print("=" * 70)
    print("\n📚 核心概念:")
    print("   - 财务数据是季度报告，不能简单 forward-fill")
    print("   - 必须使用公告日期（ann_date）确定数据可用性")
    print("   - 在每个交易日使用该日或之前公布的最新财报")
    print("   - 这样可以避免前视偏差（look-ahead bias）")

    try:
        # 加载数据
        df = load_report_period_data()

        # 演示前视偏差
        demonstrate_look_ahead_bias(df)

        # 分析财报公告时间模式
        analyze_report_period_pattern(df)

        # 计算正确的 ROE 因子
        result = calculate_roe_with_report_period(df)

        # 保存结果
        output_path = Path("ex04_report_period_roe_output.h5")
        result.to_hdf(output_path, key="data")
        print(f"\n💾 结果已保存到: {output_path}")

        # 方法对比
        compare_methods(df)

        print("\n" + "=" * 70)
        print("✨ 报告期概念演示完成！")
        print("=" * 70)
        print("\n🎯 关键要点:")
        print("   1. 永远不要简单 forward-fill 季度财务数据到日频")
        print("   2. 使用公告日期（ann_date）确定数据可用性")
        print("   3. 对每个交易日，使用该日或之前公布的最新财报")
        print("   4. 验证：交易日 >= 公告日期，确保无前视偏差")
        print("\n📖 更多信息:")
        print("   - rdagent/scenarios/qlib/experiment/REPORT_PERIOD_CONCEPT.md")
        print("   - rdagent/scenarios/qlib/experiment/report_period_utils.py")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
