#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于报告期的财务因子计算示例

演示如何使用"报告期概念"计算正确的财务因子：
- 不进行前向填充，保留财务数据的季度特性
- 在因子计算时，使用"在时间t已公告的最新报告"
- 展示ROE动量因子的计算过程

使用方法：
    python -m rdagent.scenarios.qlib.experiment.report_period_factor_example

作者: RD-Agent Team
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 导入报告期访问器
from .report_period_utils import ReportPeriodAccessor


class FinancialFactorCalculator:
    """
    基于报告期的财务因子计算器

    正确处理季度财务数据的时序特性，不进行前向填充。
    """

    def __init__(self, df: pd.DataFrame):
        """
        初始化因子计算器

        Args:
            df: 包含价格和财务数据的DataFrame（报告期格式）
                财务字段只在公告日有值
        """
        self.accessor = ReportPeriodAccessor(df)
        self.df = df

    def calculate_roe_factor(
        self,
        date: str,
        instruments: Optional[List[str]] = None,
        method: str = "latest"
    ) -> pd.Series:
        """
        计算ROE因子（横截面）

        Args:
            date: 计算日期
            instruments: 股票列表（None表示全部）
            method: 计算方法
                - "latest": 使用最新可获得的ROE报告值

        Returns:
            Series，索引为股票代码，值为ROE因子
        """
        if instruments is None:
            instruments = list(self.accessor.report_map.keys())

        result = {}
        for instrument in instruments:
            if method == "latest":
                value = self.accessor.get_financial_at_date(instrument, date, 'ROE')
                if value is not None:
                    result[instrument] = value

        return pd.Series(result)

    def calculate_roe_momentum_factor(
        self,
        date: str,
        instruments: Optional[List[str]] = None,
        periods: int = 4
    ) -> pd.Series:
        """
        计算ROE动量因子（ROE变化率）

        计算方法：
        1. 获取当前日期可获得的最新ROE报告
        2. 获取periods个季度前的ROE报告
        3. 计算变化率：(当前ROE - 过去ROE) / |过去ROE|

        Args:
            date: 计算日期
            instruments: 股票列表
            periods: 对比几个季度前的报告（默认4个季度=1年前）

        Returns:
            Series，索引为股票代码，值为ROE变化率
        """
        if instruments is None:
            instruments = list(self.accessor.report_map.keys())

        result = {}

        # 获取当前日期
        current_date = pd.Timestamp(date)

        for instrument in instruments:
            # 获取当前的ROE
            current_roe = self.accessor.get_financial_at_date(
                instrument, date, 'ROE', max_lag_days=365
            )

            if current_roe is None:
                continue

            # 获取报告信息，找出公告日期
            report_info = self.accessor.get_report_info(instrument, date)
            if report_info['announce_date'] is None:
                continue

            # 计算目标对比日期（大约1年前）
            # 使用公告日期往前推，确保我们可以获得那个季度的报告
            target_date = report_info['announce_date'] - pd.Timedelta(days=periods * 90)

            # 获取过去ROE
            past_roe = self.accessor.get_financial_at_date(
                instrument, target_date.strftime('%Y-%m-%d'), 'ROE', max_lag_days=365
            )

            if past_roe is None or past_roe == 0:
                continue

            # 计算变化率
            momentum = (current_roe - past_roe) / abs(past_roe)
            result[instrument] = momentum

        return pd.Series(result)

    def calculate_roe_trend_factor(
        self,
        date: str,
        instruments: Optional[List[str]] = None,
        quarters: int = 4
    ) -> pd.Series:
        """
        计算ROE趋势因子（基于最近几个季度的ROE线性回归斜率）

        Args:
            date: 计算日期
            instruments: 股票列表
            quarters: 使用最近几个季度的数据

        Returns:
            Series，索引为股票代码，值为ROE趋势斜率
        """
        if instruments is None:
            instruments = list(self.accessor.report_map.keys())

        result = {}

        for instrument in instruments:
            # 获取ROE时间序列
            roe_series = self.accessor.get_financial_series(
                instrument,
                'ROE',
                start_date=(pd.Timestamp(date) - pd.Timedelta(days=quarters * 120)).strftime('%Y-%m-%d'),
                end_date=date
            )

            # 过滤掉NaN值，只保留有实际报告数据的日期
            valid_data = roe_series.dropna()

            if len(valid_data) < 2:
                continue

            # 计算线性回归斜率
            x = np.arange(len(valid_data))
            y = valid_data.values

            # 简单线性回归：y = a*x + b
            # 斜率a = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
            n = len(y)
            sum_x = np.sum(x)
            sum_y = np.sum(y)
            sum_xy = np.sum(x * y)
            sum_x2 = np.sum(x ** 2)

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)

            result[instrument] = slope

        return pd.Series(result)

    def calculate_financial_quality_factor(
        self,
        date: str,
        instruments: Optional[List[str]] = None
    ) -> pd.Series:
        """
        计算财务质量因子（综合多个财务指标）

        因子定义：
        - 高ROE（盈利能力强）
        - 低DebtToAssets（财务风险低）
        - 高CurrentRatio（流动性好）

        计算方法：
        1. 获取各指标的最新报告值
        2. 对每个指标进行横截面标准化
        3. 综合得分 = zROE - zDebtToAssets + zCurrentRatio

        Args:
            date: 计算日期
            instruments: 股票列表

        Returns:
            Series，索引为股票代码，值为财务质量综合得分
        """
        if instruments is None:
            instruments = list(self.accessor.report_map.keys())

        # 收集各指标数据
        roe_values = {}
        debt_values = {}
        current_values = {}

        for instrument in instruments:
            roe = self.accessor.get_financial_at_date(instrument, date, 'ROE')
            debt = self.accessor.get_financial_at_date(instrument, date, 'DebtToAssets')
            current = self.accessor.get_financial_at_date(instrument, date, 'CurrentRatio')

            if roe is not None:
                roe_values[instrument] = roe
            if debt is not None:
                debt_values[instrument] = debt
            if current is not None:
                current_values[instrument] = current

        # 转换为Series
        roe_series = pd.Series(roe_values)
        debt_series = pd.Series(debt_values)
        current_series = pd.Series(current_values)

        # 横截面标准化
        def z_score(series: pd.Series) -> pd.Series:
            return (series - series.mean()) / series.std()

        roe_z = z_score(roe_series)
        debt_z = z_score(debt_series)
        current_z = z_score(current_series)

        # 综合得分
        result = {}
        all_instruments = set(roe_series.index) | set(debt_series.index) | set(current_series.index)

        for instrument in all_instruments:
            score = 0
            count = 0

            if instrument in roe_z:
                score += roe_z[instrument]
                count += 1

            if instrument in debt_z:
                score -= debt_z[instrument]  # 负债率越低越好
                count += 1

            if instrument in current_z:
                score += current_z[instrument]
                count += 1

            if count > 0:
                result[instrument] = score / count

        return pd.Series(result)


def demonstrate_factor_calculation():
    """演示因子计算"""
    print("\n" + "="*70)
    print("基于报告期的财务因子计算演示")
    print("="*70)

    # 加载数据
    h5_path = Path('git_ignore_folder/factor_implementation_source_data/daily_pv_report_period.h5')
    if not h5_path.exists():
        print(f"❌ 数据文件不存在: {h5_path}")
        return

    print(f"\n📂 加载数据: {h5_path}")
    df = pd.read_hdf(h5_path, key='data')

    # 创建因子计算器
    print("\n🔧 创建因子计算器...")
    calculator = FinancialFactorCalculator(df)

    # 演示日期
    demo_date = '2025-12-29'

    # 1. ROE因子
    print(f"\n{'='*70}")
    print(f"因子1: ROE因子 ({demo_date})")
    print('='*70)

    roe_factor = calculator.calculate_roe_factor(demo_date)
    print(f"有效股票数: {len(roe_factor)}")
    print(f"ROE统计:")
    print(f"  均值: {roe_factor.mean():.4f}")
    print(f"  标准差: {roe_factor.std():.4f}")
    print(f"  最小值: {roe_factor.min():.4f}")
    print(f"  中位数: {roe_factor.median():.4f}")
    print(f"  最大值: {roe_factor.max():.4f}")
    print(f"\nROE最高的5只股票:")
    for stock, value in roe_factor.nlargest(5).items():
        print(f"  {stock}: {value:.4f}")

    # 2. ROE动量因子
    print(f"\n{'='*70}")
    print(f"因子2: ROE动量因子 (年度ROE变化率, {demo_date})")
    print('='*70)

    roe_momentum = calculator.calculate_roe_momentum_factor(demo_date, periods=4)
    print(f"有效股票数: {len(roe_momentum)}")
    print(f"ROE变化率统计:")
    print(f"  均值: {roe_momentum.mean():.4f}")
    print(f"  标准差: {roe_momentum.std():.4f}")
    print(f"  最小值: {roe_momentum.min():.4f}")
    print(f"  中位数: {roe_momentum.median():.4f}")
    print(f"  最大值: {roe_momentum.max():.4f}")
    print(f"\nROE改善最明显的5只股票:")
    for stock, value in roe_momentum.nlargest(5).items():
        print(f"  {stock}: {value:.4f}")

    # 3. ROE趋势因子
    print(f"\n{'='*70}")
    print(f"因子3: ROE趋势因子 (最近4季度斜率, {demo_date})")
    print('='*70)

    roe_trend = calculator.calculate_roe_trend_factor(demo_date, quarters=4)
    print(f"有效股票数: {len(roe_trend)}")
    print(f"趋势斜率统计:")
    print(f"  均值: {roe_trend.mean():.6f}")
    print(f"  标准差: {roe_trend.std():.6f}")
    print(f"  最小值: {roe_trend.min():.6f}")
    print(f"  中位数: {roe_trend.median():.6f}")
    print(f"  最大值: {roe_trend.max():.6f}")
    print(f"\nROE上升趋势最明显的5只股票:")
    for stock, value in roe_trend.nlargest(5).items():
        print(f"  {stock}: {value:.6f}")

    # 4. 财务质量因子
    print(f"\n{'='*70}")
    print(f"因子4: 财务质量因子 (ROE - 负债率 + 流动比率, {demo_date})")
    print('='*70)

    quality_factor = calculator.calculate_financial_quality_factor(demo_date)
    print(f"有效股票数: {len(quality_factor)}")
    print(f"质量得分统计:")
    print(f"  均值: {quality_factor.mean():.4f}")
    print(f"  标准差: {quality_factor.std():.4f}")
    print(f"  最小值: {quality_factor.min():.4f}")
    print(f"  中位数: {quality_factor.median():.4f}")
    print(f"  最大值: {quality_factor.max():.4f}")
    print(f"\n财务质量最好的5只股票:")
    for stock, value in quality_factor.nlargest(5).items():
        print(f"  {stock}: {value:.4f}")

    # 5. 展示单只股票的详细数据
    print(f"\n{'='*70}")
    print("示例: 浦发银行(600000.SH)的ROE报告详情")
    print('='*70)

    sample_stock = '600000.SH'
    report_info = calculator.accessor.get_report_info(sample_stock, demo_date)

    print(f"查询日期: {demo_date}")
    print(f"使用报告公告日期: {report_info['announce_date']}")
    print(f"滞后天数: {report_info['lag_days']} 天")
    print(f"可用字段: {', '.join(report_info['available_fields'])}")

    # 获取最近的ROE值
    roe_value = calculator.accessor.get_financial_at_date(sample_stock, demo_date, 'ROE')
    print(f"ROE值: {roe_value:.4f}")

    # 获取ROE时间序列
    print(f"\n最近4个季度的ROE报告:")
    roe_series = calculator.accessor.get_financial_series(
        sample_stock,
        'ROE',
        start_date='2025-01-01',
        end_date=demo_date
    )
    # 只显示有变化的值（不同的报告）
    unique_reports = roe_series.dropna().unique()
    for i, value in enumerate(unique_reports[-5:], 1):
        print(f"  第{i}个报告: ROE = {value:.4f}")

    print(f"\n{'='*70}")
    print("✅ 演示完成！")
    print('='*70)

    print("\n📝 关键要点:")
    print("  1. 财务数据只在公告日有值，不进行前向填充")
    print("  2. 因子计算时使用'在时间t已公告的最新报告'")
    print("  3. 这正确反映了信息的可获得性，避免了未来函数")
    print("  4. 季度财务数据的低频特性被保留和利用")


if __name__ == "__main__":
    demonstrate_factor_calculation()
