# -*- coding: utf-8 -*-
"""
Qlib增强数据加载工具

支持多源数据加载和合并：
1. 基础行情数据（价格/成交量）
2. 财务数据（估值/盈利能力/成长能力等）
3. 行业分类数据（申万2021分类）

作者: RD-Agent Team
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


class EnhancedDataLoader:
    """
    增强的数据加载器

    支持从多个数据源加载和合并数据，为复合因子生成提供完整的数据基础。

    Attributes:
        data_folder: 数据文件夹路径
        base_data: 基础行情数据
        financial_data: 财务数据
        industry_mapping: 行业分类映射
    """

    def __init__(self, data_folder: str = "."):
        """
        初始化数据加载器

        Args:
            data_folder: 数据文件夹路径
        """
        self.data_folder = Path(data_folder)

    def load_base_data(self, filename: str = "daily_pv.h5") -> pd.DataFrame:
        """
        加载基础价格/成交量数据

        Returns:
            包含OHLCV数据的DataFrame，MultiIndex为(datetime, instrument)
        """
        path = self.data_folder / filename
        if not path.exists():
            raise FileNotFoundError(f"基础数据文件不存在: {path}")

        df = pd.read_hdf(path, key='data')

        if not isinstance(df.index, pd.MultiIndex):
            raise ValueError("基础数据索引必须是MultiIndex(datetime, instrument)")

        return df

    def load_financial_data(self, filename: str = "daily_pv_financial.h5") -> pd.DataFrame:
        """
        加载财务数据

        财务数据包括：
        - 估值指标：PE, PB, PS等
        - 盈利能力：ROE, ROA等
        - 成长能力：营收增长率、净利润增长率等
        - 市值数据：总市值、流通市值

        Returns:
            包含财务数据的DataFrame，MultiIndex为(datetime, instrument)
            如果文件不存在返回空DataFrame
        """
        path = self.data_folder / filename
        if not path.exists():
            return pd.DataFrame()

        df = pd.read_hdf(path, key='data')

        if not isinstance(df.index, pd.MultiIndex):
            raise ValueError("财务数据索引必须是MultiIndex(datetime, instrument)")

        return df

    def load_report_period_data(self, filename: str = "daily_pv_report_period.h5") -> pd.DataFrame:
        """
        加载基于报告期的财务数据

        报告期数据特点：
        - 财务数据只在公告日有值（保留季度特性）
        - 在因子计算时使用"在时间t已公告的最新报告"
        - 不进行前向填充，正确反映信息的可获得性

        Returns:
            包含报告期数据的DataFrame，MultiIndex为(datetime, instrument)
            如果文件不存在返回空DataFrame
        """
        path = self.data_folder / filename
        if not path.exists():
            return pd.DataFrame()

        df = pd.read_hdf(path, key='data')

        if not isinstance(df.index, pd.MultiIndex):
            raise ValueError("报告期数据索引必须是MultiIndex(datetime, instrument)")

        return df

    def get_financial_with_report_period(
        self,
        df: pd.DataFrame,
        instruments: List[str],
        date: str,
        field: str,
        max_lag_days: int = 365
    ) -> pd.Series:
        """
        获取指定日期所有股票的财务数据（使用报告期概念）

        对于每只股票，返回在指定日期可获得的最新财务报告数据。

        Args:
            df: 包含财务数据的DataFrame（报告期格式）
            instruments: 股票列表
            date: 查询日期
            field: 财务字段名
            max_lag_days: 最大允许滞后天数

        Returns:
            Series，索引为股票代码，值为财务数据
        """
        from .report_period_utils import ReportPeriodAccessor

        accessor = ReportPeriodAccessor(df)
        result = {}

        for instrument in instruments:
            value = accessor.get_financial_at_date(instrument, date, field, max_lag_days)
            if value is not None:
                result[instrument] = value

        return pd.Series(result)

    def load_industry_mapping(self,
                            filename: Optional[str] = None) -> Dict[str, Dict[str, str]]:
        """
        加载行业分类映射

        从Qlib数据目录加载Tushare行业分类数据：
        - industry_l1: 申万一级行业（29个）
        - industry_l2: 申万二级行业（110个）

        Args:
            filename: 行业映射文件路径，None则使用默认路径

        Returns:
            嵌套字典，格式：{instrument: {"industry_l1": "...", "industry_l2": "..."}}
        """
        if filename is None:
            # 使用默认路径
            filename = Path.home() / '.qlib/qlib_data/cn_data/industry_data/tushare_stock_to_industry_dict_20251229_161019.json'

        path = Path(filename)
        if not path.exists():
            return {}

        with open(path) as f:
            raw_mapping = json.load(f)

        # 转换为简化格式
        mapping = {}
        for stock_code, data in raw_mapping.items():
            # 转换股票代码格式（从 xxxxxx.YZ 到 xxxxxxYZ）
            instrument = stock_code.replace('.', '')
            mapping[instrument] = {
                "industry_l1": data.get("industry_l1", "Unknown"),
                "industry_l2": data.get("industry_l2", "Unknown"),
            }

        return mapping

    def merge_all_data(self,
                      base_df: Optional[pd.DataFrame] = None,
                      financial_df: Optional[pd.DataFrame] = None,
                      industry_mapping: Optional[Dict] = None,
                      how: str = "left") -> pd.DataFrame:
        """
        合并所有数据源

        将基础行情数据、财务数据和行业分类合并为一个完整的DataFrame。

        Args:
            base_df: 基础行情数据
            financial_df: 财务数据
            industry_mapping: 行业分类映射
            how: 合并方式（left/inner/outer）

        Returns:
            合并后的DataFrame，包含所有数据源的字段
        """
        # 加载数据（如果未提供）
        if base_df is None:
            base_df = self.load_base_data()
        if financial_df is None:
            financial_df = self.load_financial_data()
        if industry_mapping is None:
            industry_mapping = self.load_industry_mapping()

        # 开始合并
        df = base_df.copy()

        # 合并财务数据
        if financial_df is not None and len(financial_df) > 0:
            # 只合并不存在的列
            new_cols = [col for col in financial_df.columns if col not in df.columns]
            if new_cols:
                df = df.join(financial_df[new_cols], how=how)

        # 添加行业分类
        if industry_mapping:
            df_reset = df.reset_index()

            # 映射行业分类
            df_reset['industry_l1'] = df_reset['instrument'].map(
                lambda x: industry_mapping.get(x, {}).get('industry_l1', 'Unknown')
            )
            df_reset['industry_l2'] = df_reset['instrument'].map(
                lambda x: industry_mapping.get(x, {}).get('industry_l2', 'Unknown')
            )

            # 恢复MultiIndex
            df = df_reset.set_index(['datetime', 'instrument'])

        return df

    def get_industry_groups(self,
                           df: pd.DataFrame,
                           level: str = "l2") -> Dict[str, List[str]]:
        """
        获取行业分组

        Args:
            df: 包含行业分类的DataFrame
            level: 行业级别（"l1"或"l2"）

        Returns:
            行业分组字典，格式：{industry_name: [instrument_list]}
        """
        industry_col = f"industry_{level}"

        if industry_col not in df.columns:
            raise ValueError(f"数据中缺少行业列: {industry_col}")

        # 重置索引以访问instrument列
        df_reset = df.reset_index()

        # 按行业分组
        industry_groups = df_reset.groupby(industry_col)['instrument'].apply(list).to_dict()

        return industry_groups

    def get_available_fields(self, df: Optional[pd.DataFrame] = None) -> Dict[str, List[str]]:
        """
        获取可用的字段分类

        Args:
            df: 数据DataFrame，None则自动加载

        Returns:
            字段分类字典
        """
        if df is None:
            df = self.merge_all_data()

        fields = {
            "price": [],
            "volume": [],
            "financial": [],
            "industry": [],
        }

        for col in df.columns:
            if col.startswith("$"):
                if col in ["$open", "$high", "$low", "$close"]:
                    fields["price"].append(col)
                elif col in ["$volume", "$amount"]:
                    fields["volume"].append(col)
            elif col in ["PE", "PE_TTM", "PB", "PS", "PS_TTM", "market_cap", "total_mv", "circ_mv"]:
                fields["financial"].append(col)
            elif col in ["industry_l1", "industry_l2"]:
                fields["industry"].append(col)
            else:
                fields["financial"].append(col)

        return fields


def generate_financial_data(market: str = "csi300",
                           start_time: str = "2010-01-01",
                           end_time: Optional[str] = None,
                           output_path: Optional[str] = None):
    """
    生成包含财务数据的HDF5文件

    这是一个工具函数，用于扩展Qlib的数据生成，添加财务字段。

    Args:
        market: 市场标识（csi300, csi500, all等）
        start_time: 起始时间
        end_time: 结束时间
        output_path: 输出文件路径

    Returns:
        生成的DataFrame
    """
    import qlib
    from qlib.data import D

    qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region="cn")

    instruments = D.instruments(market=market)

    # 定义财务字段
    financial_fields = [
        # 基础行情
        "$open", "$close", "$high", "$low", "$volume", "$amount",
        # 估值指标
        "PE", "PE_TTM", "PB", "PS", "PS_TTM",
        # 盈利能力
        "ROE", "ROA",
        # 成长能力（部分Qlib版本可能不支持）
        # "OperatingRevenueGrowRate",
        # "NetProfitGrowRate",
        # 市值
        "market_cap", "total_mv", "circ_mv",
    ]

    # 获取数据
    data = D.features(
        instruments,
        financial_fields,
        start_time=start_time,
        end_time=end_time,
        freq="day"
    )

    # 处理索引
    data = data.swaplevel().sort_index()

    # 保存
    if output_path:
        data.to_hdf(output_path, key='data')

    return data


def inspect_data_quality(df: pd.DataFrame) -> Dict:
    """
    检查数据质量

    Args:
        df: 要检查的DataFrame

    Returns:
        数据质量报告字典
    """
    report = {
        "shape": df.shape,
        "index_names": df.index.names,
        "columns": list(df.columns),
        "missing_values": {},
        "data_types": {},
        "date_range": None,
        "num_instruments": 0,
    }

    # 缺失值统计
    for col in df.columns:
        missing_count = df[col].isna().sum()
        missing_ratio = missing_count / len(df)
        report["missing_values"][col] = {
            "count": int(missing_count),
            "ratio": float(missing_ratio),
        }

    # 数据类型
    report["data_types"] = df.dtypes.astype(str).to_dict()

    # 时间范围和股票数量
    if isinstance(df.index, pd.MultiIndex):
        report["date_range"] = (
            str(df.index.get_level_values(0).min()),
            str(df.index.get_level_values(0).max())
        )
        report["num_instruments"] = df.index.get_level_values(1).nunique()

    return report
