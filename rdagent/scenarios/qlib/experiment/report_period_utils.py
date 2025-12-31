#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于报告期的财务数据访问工具

提供在因子计算时获取"在时间t已公告的最新报告"的功能。

使用方法：
    from rdagent.scenarios.qlib.experiment.report_period_utils import ReportPeriodAccessor

    accessor = ReportPeriodAccessor(df)
    roe_at_date = accessor.get_financial_at_date('600000.SH', '2025-12-29', 'ROE')

作者: RD-Agent Team
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from pathlib import Path


class ReportPeriodAccessor:
    """
    基于报告期的财务数据访问器

    核心思想：
    - 财务数据只在公告日有值（保留其季度特性）
    - 在任意日期t，使用"在时间t已公告的最新报告"的数据
    - 这正确反映了信息可获得性：在t时刻，我们只能使用t之前已公告的报告
    """

    def __init__(self, df: pd.DataFrame):
        """
        初始化访问器

        Args:
            df: 包含价格和财务数据的DataFrame（MultiIndex: datetime, instrument）
                财务字段只在公告日有值，其他日期为NaN
        """
        self.df = df.copy()

        # 构建财务报告索引（加速查询）
        self._build_report_index()

    def _build_report_index(self):
        """构建财务报告索引，用于快速查找"""
        print("  构建财务报告索引...")

        # 获取所有财务字段（非价格字段）
        financial_fields = [
            'EPS', 'BPS', 'OCFPS', 'CFPS',
            'ROE', 'ROA', 'ROIC',
            'NetProfitMargin', 'GrossProfitMargin',
            'EPS_Growth', 'CFPS_Growth', 'NetProfit_Growth', 'OP_Growth',
            'DebtToAssets', 'CurrentRatio', 'QuickRatio', 'OCF_To_Debt',
            'AssetsTurnover', 'AR_Turnover', 'CA_Turnover', 'EBITDA'
        ]

        # 筛选存在的财务字段
        self.financial_fields = [f for f in financial_fields if f in self.df.columns]

        # 为每个股票构建"公告日 -> 财务数据"的映射
        self.report_map: Dict[str, pd.DataFrame] = {}

        for instrument in self.df.index.get_level_values(1).unique():
            stock_data = self.df.xs(instrument, level=1)

            # 找出有财务数据的日期（公告日）
            # 只要有一个财务字段有值，就认为这一天是公告日
            has_financial = stock_data[self.financial_fields].notna().any(axis=1)
            report_dates = stock_data[has_financial].index

            if len(report_dates) > 0:
                # 保存该股票的公告日财务数据
                self.report_map[instrument] = stock_data.loc[report_dates][self.financial_fields].copy()

        print(f"    索引构建完成: {len(self.report_map)} 只股票有财务报告数据")

    def get_financial_at_date(
        self,
        instrument: str,
        date: str,
        field: str,
        max_lag_days: int = 365
    ) -> Optional[float]:
        """
        获取某股票在指定日期可获得的最新财务数据

        Args:
            instrument: 股票代码（如 '600000.SH'）
            date: 查询日期（如 '2025-12-29'）
            field: 财务字段（如 'ROE', 'EPS'）
            max_lag_days: 最大允许滞后天数（避免使用过时的报告）

        Returns:
            财务数据值，如果找不到则返回None
        """
        if instrument not in self.report_map:
            return None

        if field not in self.financial_fields:
            return None

        # 转换日期
        query_date = pd.Timestamp(date)

        # 获取该股票的所有报告
        reports = self.report_map[instrument]

        # 找出在查询日期之前的最新报告
        available_reports = reports[reports.index <= query_date]

        if len(available_reports) == 0:
            return None

        # 获取最新的报告
        latest_report = available_reports.iloc[-1]

        # 检查滞后时间
        lag_days = (query_date - latest_report.name).days
        if lag_days > max_lag_days:
            # 报告太旧，返回None
            return None

        value = latest_report[field]

        # 如果值为NaN，返回None
        if pd.isna(value):
            return None

        return float(value)

    def get_financial_series(
        self,
        instrument: str,
        field: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        max_lag_days: int = 365
    ) -> pd.Series:
        """
        获取某股票的财务数据时间序列（使用"最新可用报告"）

        Args:
            instrument: 股票代码
            field: 财务字段
            start_date: 起始日期
            end_date: 结束日期
            max_lag_days: 最大允许滞后天数

        Returns:
            时间序列，索引为日期，值为财务数据
        """
        if instrument not in self.df.index.get_level_values(1):
            return pd.Series(dtype=float)

        # 获取该股票的所有交易日数据
        stock_data = self.df.xs(instrument, level=1)

        # 应用日期范围过滤
        if start_date:
            stock_data = stock_data[stock_data.index >= pd.Timestamp(start_date)]
        if end_date:
            stock_data = stock_data[stock_data.index <= pd.Timestamp(end_date)]

        # 对每个交易日，获取可获得的最新财务数据
        result = {}
        for date in stock_data.index:
            value = self.get_financial_at_date(instrument, date.strftime('%Y-%m-%d'), field, max_lag_days)
            result[date] = value

        return pd.Series(result, dtype=float)

    def get_all_financials_at_date(
        self,
        date: str,
        field: str,
        instruments: Optional[List[str]] = None,
        max_lag_days: int = 365
    ) -> pd.Series:
        """
        获取指定日期所有股票的某项财务数据

        用于横截面因子计算

        Args:
            date: 查询日期
            field: 财务字段
            instruments: 股票列表（None表示全部）
            max_lag_days: 最大允许滞后天数

        Returns:
            Series，索引为股票代码，值为财务数据
        """
        if instruments is None:
            instruments = list(self.report_map.keys())

        result = {}
        for instrument in instruments:
            value = self.get_financial_at_date(instrument, date, field, max_lag_days)
            if value is not None:
                result[instrument] = value

        return pd.Series(result)

    def get_report_info(self, instrument: str, date: str) -> Dict[str, Any]:
        """
        获取在指定日期可获得的最新报告的信息

        Args:
            instrument: 股票代码
            date: 查询日期

        Returns:
            包含报告信息的字典：
            - report_date: 报告期（end_date）
            - announce_date: 公告日期
            - lag_days: 滞后天数
            - available_fields: 可用的财务字段
        """
        if instrument not in self.report_map:
            return {
                'report_date': None,
                'announce_date': None,
                'lag_days': None,
                'available_fields': []
            }

        query_date = pd.Timestamp(date)
        reports = self.report_map[instrument]
        available_reports = reports[reports.index <= query_date]

        if len(available_reports) == 0:
            return {
                'report_date': None,
                'announce_date': None,
                'lag_days': None,
                'available_fields': []
            }

        latest_report = available_reports.iloc[-1]
        announce_date = latest_report.name

        # 找出非空的字段
        available_fields = [f for f in self.financial_fields if pd.notna(latest_report[f])]

        return {
            'report_date': announce_date,  # 在这里，公告日期就是数据的日期
            'announce_date': announce_date,
            'lag_days': (query_date - announce_date).days,
            'available_fields': available_fields
        }

    def get_summary_stats(self) -> Dict[str, Any]:
        """获取数据集的统计摘要"""
        total_records = len(self.df)
        total_instruments = self.df.index.get_level_values(1).nunique()

        # 统计有财务数据的记录数
        has_financial = self.df[self.financial_fields].notna().any(axis=1).sum()
        financial_coverage = has_financial / total_records * 100

        # 日期范围
        date_range = (
            self.df.index.get_level_values(0).min(),
            self.df.index.get_level_values(0).max()
        )

        return {
            'total_records': total_records,
            'total_instruments': total_instruments,
            'instruments_with_reports': len(self.report_map),
            'records_with_financial': has_financial,
            'financial_coverage': financial_coverage,
            'date_range': date_range,
            'financial_fields': self.financial_fields
        }


def demo_usage():
    """演示使用方法"""
    print("\n" + "="*60)
    print("报告期访问器使用演示")
    print("="*60)

    # 加载数据
    h5_path = Path('git_ignore_folder/factor_implementation_source_data/daily_pv_report_period.h5')
    if not h5_path.exists():
        print(f"❌ 数据文件不存在: {h5_path}")
        return

    print(f"\n📂 加载数据: {h5_path}")
    df = pd.read_hdf(h5_path, key='data')

    # 创建访问器
    print("\n🔧 创建报告期访问器...")
    accessor = ReportPeriodAccessor(df)

    # 显示统计信息
    print("\n📊 数据集统计:")
    stats = accessor.get_summary_stats()
    print(f"  总记录数: {stats['total_records']:,}")
    print(f"  股票数量: {stats['total_instruments']:,}")
    print(f"  有财务报告的股票数: {stats['instruments_with_reports']:,}")
    print(f"  有财务数据的记录数: {stats['records_with_financial']:,}")
    print(f"  财务数据覆盖率: {stats['financial_coverage']:.2f}%")
    print(f"  日期范围: {stats['date_range'][0]} 至 {stats['date_range'][1]}")

    # 示例1：获取特定日期的ROE
    print("\n📈 示例1: 获取特定股票在特定日期的ROE")
    instrument = '600000.SH'
    date = '2025-12-29'
    roe_value = accessor.get_financial_at_date(instrument, date, 'ROE')
    print(f"  {instrument} 在 {date} 的ROE: {roe_value}")

    # 显示报告信息
    report_info = accessor.get_report_info(instrument, date)
    print(f"  使用报告公告日期: {report_info['announce_date']}")
    print(f"  滞后天数: {report_info['lag_days']} 天")
    print(f"  可用字段: {', '.join(report_info['available_fields'][:5])}...")

    # 示例2：获取时间序列
    print("\n📈 示例2: 获取ROE时间序列（最近30个交易日）")
    roe_series = accessor.get_financial_series(
        instrument,
        'ROE',
        start_date='2025-11-01',
        end_date='2025-12-29'
    )
    print(f"  有效数据点数: {roe_series.notna().sum()}")
    print(f"  最近5个值:")
    for date, value in roe_series.tail(5).items():
        if pd.notna(value):
            print(f"    {date.strftime('%Y-%m-%d')}: {value:.4f}")
        else:
            print(f"    {date.strftime('%Y-%m-%d')}: N/A")

    # 示例3：横截面数据
    print("\n📈 示例3: 获取某日所有股票的ROE（横截面）")
    cross_section = accessor.get_all_financials_at_date('2025-12-29', 'ROE')
    print(f"  有效股票数: {len(cross_section)}")
    print(f"  ROE统计:")
    print(f"    均值: {cross_section.mean():.4f}")
    print(f"    标准差: {cross_section.std():.4f}")
    print(f"    最小值: {cross_section.min():.4f}")
    print(f"    最大值: {cross_section.max():.4f}")

    print("\n✅ 演示完成！")


if __name__ == "__main__":
    demo_usage()
