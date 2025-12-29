#!/usr/bin/env python3
"""
生成行业板块因子数据
将 ~/.qlib/qlib_data/cn_data/industry_data 中的行业数据转换为因子可用的格式
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json


def load_industry_data():
    """加载行业数据"""
    industry_dir = Path.home() / ".qlib/qlib_data/cn_data/industry_data"

    # 加载申万2021一级行业分类
    sw_l1_file = industry_dir / "industry_SW2021_L1_20251229_112014.csv"
    if sw_l1_file.exists():
        df_sw_l1 = pd.read_csv(sw_l1_file, encoding='utf-8-sig')
        print(f"✓ 加载申万一级行业: {len(df_sw_l1)} 个行业")
        return df_sw_l1
    else:
        print(f"✗ 未找到申万行业数据文件")
        return None


def get_stock_industry_mapping():
    """
    获取股票到行业的映射关系
    注意：实际应用中需要从数据库或API获取完整的股票-行业映射
    这里提供一个示例框架
    """
    # TODO: 实现实际的股票-行业映射
    # 可以从以下来源获取：
    # 1. Qlib 的 instruments 元数据
    # 2. Tushare 等数据源
    # 3. 手动维护的映射表

    mapping = {
        # 示例格式
        # 'SH600000': {'industry': '银行', 'industry_code': '210000'},
        # 'SZ000001': {'industry': '房地产', 'industry_code': '220000'},
    }
    return mapping


def generate_industry_factor_h5(daily_pv_path: str, output_path: str = None):
    """
    生成包含行业信息的因子数据文件

    Parameters
    ----------
    daily_pv_path : str
        原始日线数据文件路径 (daily_pv.h5)
    output_path : str
        输出文件路径，默认为 daily_pv_with_industry.h5
    """
    if output_path is None:
        output_path = str(Path(daily_pv_path).parent / "daily_pv_with_industry.h5")

    # 读取原始数据
    print(f"读取原始数据: {daily_pv_path}")
    df = pd.read_hdf(daily_pv_path, key='data')

    print(f"原始数据形状: {df.shape}")
    print(f"原始数据列: {df.columns.tolist()}")

    # 加载行业数据
    industry_df = load_industry_data()
    if industry_df is None:
        print("无法加载行业数据，返回原始数据")
        df.to_hdf(output_path, key='data')
        return output_path

    # 为每个股票添加行业信息
    # 注意：这里需要实际的股票-行业映射
    # 由于当前数据可能没有完整映射，我们创建一个示例列

    df_reset = df.reset_index()

    # TODO: 添加实际的行业映射
    # 示例：创建一个虚拟的行业列（实际应用中需要真实映射）
    if 'industry' not in df_reset.columns:
        # 这里应该根据实际的 instrument 映射到行业
        # 暂时创建一个占位列
        df_reset['industry_sw_l1'] = '未知'
        df_reset['industry_code'] = '0'

    # 创建行业哑变量因子（示例）
    # 为每个申万一级行业创建一个因子列
    for _, row in industry_df.iterrows():
        industry_name = row['industry_name']
        industry_code = row['industry_code']
        factor_name = f"industry_{industry_code}"

        # TODO: 根据股票-行业映射设置值为1或0
        # df_reset[factor_name] = df_reset['instrument'].map(lambda x: 1 if stock_in_industry(x, industry_code) else 0)
        pass

    # 恢复 MultiIndex
    result = df_reset.set_index(['datetime', 'instrument'])

    # 保存到文件
    result.to_hdf(output_path, key='data')
    print(f"✓ 数据已保存到: {output_path}")

    return output_path


def create_industry_lookup_table(output_path: str = None):
    """
    创建行业查找表，供因子开发使用

    Parameters
    ----------
    output_path : str
        输出文件路径
    """
    if output_path is None:
        output_path = "industry_lookup.csv"

    # 加载所有级别的行业数据
    industry_dir = Path.home() / ".qlib/qlib_data/cn_data/industry_data"

    all_industries = []

    # 加载申万2021分类
    for level in ['L1', 'L2', 'L3']:
        file = industry_dir / f"industry_SW2021_{level}_20251229_112014.csv"
        if file.exists():
            df = pd.read_csv(file, encoding='utf-8-sig')
            df['source'] = f'SW2021_{level}'
            all_industries.append(df)

    if all_industries:
        combined = pd.concat(all_industries, ignore_index=True)
        combined.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"✓ 行业查找表已保存: {output_path}")
        print(f"  总计 {len(combined)} 个行业分类")

        # 打印分类统计
        print("\n行业分类统计:")
        for source in combined['source'].unique():
            count = len(combined[combined['source'] == source])
            print(f"  {source}: {count} 个")

    return output_path


def create_sample_industry_factors():
    """
    创建示例行业因子，展示如何在因子开发中使用行业数据
    """
    print("\n=== 示例：行业相关因子 ===\n")

    examples = {
        "行业动量因子": {
            "description": "计算特定行业的平均收益率作为行业动量",
            "formulation": "计算行业内所有股票过去N天的平均收益率",
            "code_example": """
def calculate_Industry_Momentum():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 假设我们有行业映射表
    industry_mapping = {
        'SH600000': '银行',
        'SH600036': '银行',
        # ... 更多映射
    }

    df_reset['industry'] = df_reset['instrument'].map(industry_mapping)

    # 计算每只股票的5日收益率
    df_reset['return_5d'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=5)
    )

    # 计算行业平均收益率（行业动量）
    industry_momentum = df_reset.groupby(['datetime', 'industry'])['return_5d'].mean().reset_index()
    industry_momentum.columns = ['datetime', 'industry', 'industry_momentum']

    # 将行业动量映射回每只股票
    df_reset = df_reset.merge(industry_momentum, on=['datetime', 'industry'], how='left')

    # 恢复 MultiIndex
    result = df_reset.set_index(['datetime', 'instrument'])[['industry_momentum']]
    result.to_hdf('result.h5', key='data')
"""
        },
        "行业相对强弱因子": {
            "description": "计算股票相对所属行业的强弱",
            "formulation": "股票收益率 - 行业平均收益率",
            "code_example": """
def calculate_Industry_Relative_Strength():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 计算股票收益率
    df_reset['stock_return'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=5)
    )

    # 假设有行业映射
    # df_reset['industry'] = ...

    # 计算行业平均收益率
    industry_return = df_reset.groupby(['datetime', 'industry'])['stock_return'].mean().reset_index()
    industry_return.columns = ['datetime', 'industry', 'industry_return']

    df_reset = df_reset.merge(industry_return, on=['datetime', 'industry'], how='left')

    # 计算相对强弱
    df_reset['relative_strength'] = df_reset['stock_return'] - df_reset['industry_return']

    result = df_reset.set_index(['datetime', 'instrument'])[['relative_strength']]
    result.to_hdf('result.h5', key='data')
"""
        }
    }

    for name, info in examples.items():
        print(f"📊 {name}")
        print(f"   描述: {info['description']}")
        print(f"   公式: {info['formulation']}")
        print(f"   代码:\n{info['code_example']}\n")
        print("-" * 80)

    return examples


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="生成行业板块因子数据")
    parser.add_argument("--action", choices=["generate", "lookup", "examples"], default="generate",
                        help="执行的操作：generate(生成数据), lookup(创建查找表), examples(显示示例)")
    parser.add_argument("--input", default="daily_pv.h5", help="输入数据文件")
    parser.add_argument("--output", help="输出文件路径")

    args = parser.parse_args()

    if args.action == "generate":
        generate_industry_factor_h5(args.input, args.output)
    elif args.action == "lookup":
        create_industry_lookup_table(args.output)
    elif args.action == "examples":
        create_sample_industry_factors()
