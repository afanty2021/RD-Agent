# -*- coding: utf-8 -*-
"""
复合因子模板库

提供财务因子、行业因子和交互因子的标准模板，用于指导LLM生成复合因子。

分类：
1. 财务因子：价值、质量、成长等
2. 行业因子：行业动量、行业相对强度等
3. 交互因子：价值+动量、质量+成长等

作者: RD-Agent Team
"""

from typing import Dict, List


class CompositeFactorTemplates:
    """复合因子模板库"""

    # ==================== 财务因子模板 ====================

    @staticmethod
    def pe_momentum() -> str:
        """
        PE动量因子

        逻辑：低估值（低PE）股票可能有更好的上涨空间
        组合：PE估值信号 × 动量信号
        """
        return '''
def calculate_PE_Momentum():
    """
    PE动量因子：低估值股票的动量效应

    策略逻辑：
    1. 计算PE的横截面分位数（每天）
    2. 定义低PE为分位数<0.3
    3. 计算动量（20日收益率）
    4. PE动量 = 动量 × (1 - PE分位数)

    低PE股票获得更高权重，结合价值信号和动量信号。
    """
    import pandas as pd
    import numpy as np

    # 加载财务数据
    df = pd.read_hdf('daily_pv_financial.h5', key='data')
    df_reset = df.reset_index()

    # 计算PE的横截面分位数（每天）
    df_reset['PE_percentile'] = df_reset.groupby('datetime')['PE'].transform(
        lambda x: x.rank(pct=True)
    )

    # 计算动量（20日收益率）
    df_reset['momentum_20d'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=20)
    )

    # PE动量因子 = 动量 × (1 - PE分位数)
    # 低PE股票获得更高权重
    df_reset['PE_Momentum'] = df_reset['momentum_20d'] * (1 - df_reset['PE_percentile'])

    # 处理异常值
    df_reset['PE_Momentum'] = df_reset['PE_Momentum'].replace([np.inf, -np.inf], np.nan)

    # 恢复MultiIndex
    result = df_reset.set_index(['datetime', 'instrument'])[['PE_Momentum']]
    result.to_hdf('result.h5', key='data')
'''

    @staticmethod
    def roe_trend() -> str:
        """
        ROE趋势因子

        逻辑：寻找盈利能力持续改善的公司
        组合：ROE水平 + ROE变化
        """
        return '''
def calculate_ROE_Trend():
    """
    ROE趋势因子：盈利能力改善信号

    策略逻辑：
    1. 计算ROE的60日变化率
    2. 标准化ROE和ROE变化
    3. ROE趋势 = 0.5 × ROE_zscore + 0.5 × ROE变化_zscore

    寻找高ROE且ROE持续上升的公司。
    """
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv_financial.h5', key='data')
    df_reset = df.reset_index()

    # 确保数据按时间排序
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

    result = df_reset.set_index(['datetime', 'instrument'])[['ROE_Trend']]
    result.to_hdf('result.h5', key='data')
'''

    # ==================== 行业因子模板 ====================

    @staticmethod
    def industry_momentum() -> str:
        """
        行业动量因子

        逻辑：强势行业的股票可能表现更好
        使用申万L2（110个细分行业）
        """
        return '''
def calculate_Industry_Momentum():
    """
    行业动量因子：申万L2行业动量

    策略逻辑：
    1. 加载申万L2行业分类（110个细分行业）
    2. 计算个股5日收益率
    3. 计算行业平均动量
    4. 行业动量因子 = 该股票所属行业的动量

    买入强势行业的股票，卖出弱势行业的股票。
    """
    import pandas as pd
    import numpy as np
    import json
    from pathlib import Path

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 加载申万L2行业分类
    industry_file = Path.home() / '.qlib/qlib_data/cn_data/industry_data/tushare_stock_to_industry_dict_20251229_161019.json'
    with open(industry_file) as f:
        industry_mapping = json.load(f)

    # 映射股票到L2行业
    df_reset['industry_l2'] = df_reset['instrument'].map(
        lambda x: industry_mapping.get(x.replace('.', ''), {}).get('industry_l2', 'Unknown')
    )

    # 计算个股动量（5日收益率）
    df_reset['stock_return_5d'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=5)
    )

    # 计算L2行业平均动量
    industry_momentum = df_reset.groupby(['datetime', 'industry_l2'])['stock_return_5d'].transform('mean')

    # 行业动量因子
    df_reset['Industry_Momentum'] = industry_momentum.values

    # 过滤掉无行业分类的股票
    df_valid = df_reset[df_reset['industry_l2'] != 'Unknown'].copy()

    result = df_valid.set_index(['datetime', 'instrument'])[['Industry_Momentum']]
    result.to_hdf('result.h5', key='data')
'''

    @staticmethod
    def industry_relative_strength() -> str:
        """
        行业相对强度因子

        逻辑：相对行业表现更好的股票
        """
        return '''
def calculate_Industry_Relative_Strength():
    """
    行业相对强度因子：个股相对行业的表现

    策略逻辑：
    1. 加载申万L2行业分类
    2. 计算个股10日收益率
    3. 计算行业平均收益率
    4. 相对强度 = 个股收益 - 行业收益

    正值表示跑赢行业，负值表示跑输行业。
    """
    import pandas as pd
    import numpy as np
    import json
    from pathlib import Path

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 加载申万L2行业分类
    industry_file = Path.home() / '.qlib/qlib_data/cn_data/industry_data/tushare_stock_to_industry_dict_20251229_161019.json'
    with open(industry_file) as f:
        industry_mapping = json.load(f)

    df_reset['industry_l2'] = df_reset['instrument'].map(
        lambda x: industry_mapping.get(x.replace('.', ''), {}).get('industry_l2', 'Unknown')
    )

    # 计算个股收益率（10日）
    df_reset['stock_return'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=10)
    )

    # 计算L2行业平均收益率
    industry_return = df_reset.groupby(['datetime', 'industry_l2'])['stock_return'].transform('mean')

    # 行业相对强度 = 个股收益 - 行业收益
    df_reset['Industry_Relative_Strength'] = df_reset['stock_return'] - industry_return

    # 过滤
    df_valid = df_reset[df_reset['industry_l2'] != 'Unknown'].copy()

    result = df_valid.set_index(['datetime', 'instrument'])[['Industry_Relative_Strength']]
    result.to_hdf('result.h5', key='data')
'''

    # ==================== 交互因子模板 ====================

    @staticmethod
    def value_momentum_combo() -> str:
        """
        价值+动量组合因子

        经典组合：低估值 + 强动量
        """
        return '''
def calculate_Value_Momentum_Combo():
    """
    价值+动量组合因子

    策略逻辑：
    1. 价值信号：PE分位数倒数（低PE=高价值）
    2. 动量信号：20日收益率标准化
    3. 行业动量：所属行业的5日收益
    4. 组合：价值(30%) + 动量(50%) + 行业(20%)

    结合价值投资和趋势跟踪，同时考虑行业效应。
    """
    import pandas as pd
    import numpy as np
    import json
    from pathlib import Path

    df = pd.read_hdf('daily_pv_financial.h5', key='data')
    df_reset = df.reset_index()

    # 加载行业分类
    industry_file = Path.home() / '.qlib/qlib_data/cn_data/industry_data/tushare_stock_to_industry_dict_20251229_161019.json'
    with open(industry_file) as f:
        industry_mapping = json.load(f)

    df_reset['industry_l2'] = df_reset['instrument'].map(
        lambda x: industry_mapping.get(x.replace('.', ''), {}).get('industry_l2', 'Unknown')
    )

    # 1. 价值信号（PE分位数倒数）
    df_reset['PE_signal'] = df_reset.groupby('datetime')['PE'].transform(
        lambda x: 1 - x.rank(pct=True)
    )

    # 2. 动量信号（20日收益率）
    df_reset['momentum_signal'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=20)
    )
    df_reset['momentum_signal'] = df_reset.groupby('datetime')['momentum_signal'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )

    # 3. 行业动量
    df_reset['stock_return_5d'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=5)
    )
    df_reset['industry_momentum'] = df_reset.groupby(['datetime', 'industry_l2'])['stock_return_5d'].transform('mean')

    # 4. 组合因子 = 价值(30%) + 动量(50%) + 行业(20%)
    df_reset['Value_Momentum_Combo'] = (
        df_reset['PE_signal'] * 0.3 +
        df_reset['momentum_signal'] * 0.5 +
        df_reset['industry_momentum'] * 0.2
    )

    # 过滤
    df_valid = df_reset[
        (df_reset['industry_l2'] != 'Unknown') &
        (df_reset['PE'].notna())
    ].copy()

    # 处理异常值
    df_valid['Value_Momentum_Combo'] = df_valid['Value_Momentum_Combo'].replace([np.inf, -np.inf], np.nan)

    result = df_valid.set_index(['datetime', 'instrument'])[['Value_Momentum_Combo']]
    result.to_hdf('result.h5', key='data')
'''

    @staticmethod
    def quality_growth_momentum_combo() -> str:
        """
        质量+成长+动量组合因子

        三重因子：基本面质量 + 成长性 + 价格趋势
        """
        return '''
def calculate_Quality_Growth_Momentum_Combo():
    """
    质量+成长+动量组合因子

    策略逻辑：
    1. 质量信号：ROE + ROA的标准化组合
    2. 成长信号：营收增长 + 利润增长的标准化组合
    3. 动量信号：20日收益率的标准化
    4. 组合：质量(30%) + 成长(30%) + 动量(40%)

    寻找高质量、高成长且有趋势的股票。
    """
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv_financial.h5', key='data')
    df_reset = df.reset_index()

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

    # 3. 市值信号（小市值效应）
    df_reset['market_cap_signal'] = -df_reset.groupby('datetime')['market_cap'].transform(
        lambda x: (x - x.mean()) / (x.std() + 1e-12)
    )  # 负号：小市值更好

    # 4. 组合：质量(40%) + 动量(40%) + 市值(20%)
    df_reset['Quality_Momentum_Combo'] = (
        df_reset['quality_signal'] * 0.4 +
        df_reset['momentum_signal'] * 0.4 +
        df_reset['market_cap_signal'] * 0.2
    )

    # 处理异常值
    df_reset['Quality_Momentum_Combo'] = df_reset['Quality_Momentum_Combo'].replace([np.inf, -np.inf], np.nan)

    result = df_reset.set_index(['datetime', 'instrument'])[['Quality_Momentum_Combo']]
    result.to_hdf('result.h5', key='data')
'''

    @classmethod
    def get_all_templates(cls) -> Dict[str, str]:
        """获取所有模板"""
        return {
            "财务因子": {
                "PE动量因子": cls.pe_momentum(),
                "ROE趋势因子": cls.roe_trend(),
            },
            "行业因子": {
                "行业动量因子": cls.industry_momentum(),
                "行业相对强度因子": cls.industry_relative_strength(),
            },
            "交互因子": {
                "价值+动量组合": cls.value_momentum_combo(),
                "质量+成长+动量组合": cls.quality_growth_momentum_combo(),
            },
        }

    @classmethod
    def get_template_by_name(cls, name: str) -> str:
        """根据名称获取模板"""
        templates = cls.get_all_templates()
        for category, factors in templates.items():
            if name in factors:
                return factors[name]
        raise ValueError(f"模板不存在: {name}")
