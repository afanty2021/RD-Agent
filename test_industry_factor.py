#!/usr/bin/env python3
"""
测试行业因子代码
演示如何在 RD-Agent 中使用行业板块数据
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from data.industry_mapping.stock_industry_mapping import STOCK_INDUSTRY_MAPPING


def calculate_Industry_Momentum():
    """
    行业动量因子示例
    计算申万一级行业的平均收益率
    """
    import pandas as pd
    import numpy as np

    # 读取数据
    df = pd.read_hdf('daily_pv_debug.h5', key='data')
    df_reset = df.reset_index()

    print(f"原始数据形状: {df_reset.shape}")
    print(f"数据列: {df_reset.columns.tolist()}")
    print(f"股票数量: {df_reset['instrument'].nunique()}")
    print(f"日期范围: {df_reset['datetime'].min()} 到 {df_reset['datetime'].max()}")

    # 加载股票-行业映射
    print(f"\n加载行业映射表...")
    print(f"映射表包含 {len(STOCK_INDUSTRY_MAPPING)} 只股票")

    # 简化映射表
    industry_map = {
        k: v.get('SW2021_L1_name', '其他')
        for k, v in STOCK_INDUSTRY_MAPPING.items()
    }

    # 应用行业映射
    df_reset['industry'] = df_reset['instrument'].map(industry_map)

    # 统计映射情况
    mapped_count = df_reset['industry'].notna().sum()
    unmapped_count = df_reset['industry'].isna().sum()
    print(f"\n已映射股票: {mapped_count} ({mapped_count/len(df_reset)*100:.2f}%)")
    print(f"未映射股票: {unmapped_count} ({unmapped_count/len(df_reset)*100:.2f}%)")

    # 显示行业分布
    print(f"\n行业分布（前10个）:")
    industry_dist = df_reset[df_reset['industry'] != '其他']['industry'].value_counts()
    print(industry_dist.head(10))

    # 计算股票收益率（5日）
    df_reset['stock_return'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=5)
    )

    # 计算行业平均收益率（行业动量）
    print(f"\n计算行业动量...")
    df_reset['Industry_Momentum'] = df_reset.groupby(['datetime', 'industry'])['stock_return'].transform('mean')

    # 统计结果
    print(f"\n行业动量统计:")
    print(df_reset[['datetime', 'instrument', 'industry', 'Industry_Momentum']].dropna().head(20))

    # 显示各行业的平均动量
    industry_mom_stats = df_reset.groupby('industry')['Industry_Momentum'].agg(['mean', 'std', 'count'])
    print(f"\n各行业动量统计:")
    print(industry_mom_stats.sort_values('mean', ascending=False))

    # 恢复 MultiIndex 并保存
    result = df_reset.set_index(['datetime', 'instrument'])[['Industry_Momentum']]
    result.to_hdf('result.h5', key='data')

    print(f"\n✓ 因子已保存到 result.h5")
    print(f"  输出形状: {result.shape}")
    print(f"  非空值数量: {result['Industry_Momentum'].notna().sum()}")


def calculate_Industry_Relative_Strength():
    """
    行业相对强弱因子示例
    计算股票相对所属行业的超额收益
    """
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv_debug.h5', key='data')
    df_reset = df.reset_index()

    # 加载行业映射
    industry_map = {
        k: v.get('SW2021_L1_name', '其他')
        for k, v in STOCK_INDUSTRY_MAPPING.items()
    }
    df_reset['industry'] = df_reset['instrument'].map(industry_map)

    # 只处理有行业分类的股票
    df_valid = df_reset[df_reset['industry'] != '其他'].copy()

    # 计算股票收益率
    df_valid['stock_return'] = df_valid.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=10)
    )

    # 计算行业平均收益率
    industry_return = df_valid.groupby(['datetime', 'industry'])['stock_return'].transform('mean')

    # 计算相对强弱
    df_valid['Industry_Relative_Strength'] = df_valid['stock_return'] - industry_return

    print(f"相对强弱统计:")
    print(df_valid[['instrument', 'industry', 'stock_return', 'Industry_Relative_Strength']].dropna().head(20))

    # 恢复索引并保存
    result = df_valid.set_index(['datetime', 'instrument'])[['Industry_Relative_Strength']]
    result.to_hdf('result.h5', key='data')

    print(f"\n✓ 相对强弱因子已保存")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="测试行业因子代码")
    parser.add_argument("--factor", choices=['momentum', 'relative_strength', 'all'], default='all',
                        help="测试的因子类型")

    args = parser.parse_args()

    print("=" * 60)
    print("测试行业因子代码")
    print("=" * 60)

    # 切换到数据目录
    data_dir = Path(__file__).parent / "rdagent" / "scenarios" / "qlib" / "experiment" / "factor_data"
    if not data_dir.exists():
        data_dir = Path(__file__).parent / "target_0" / "task_1" / "execute"

    if data_dir.exists():
        import os
        os.chdir(data_dir)
        print(f"工作目录: {os.getcwd()}")
    else:
        print(f"警告: 未找到数据目录 {data_dir}")

    if args.factor in ['momentum', 'all']:
        print("\n" + "=" * 60)
        print("测试1: 行业动量因子")
        print("=" * 60)
        try:
            calculate_Industry_Momentum()
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()

    if args.factor in ['relative_strength', 'all']:
        print("\n" + "=" * 60)
        print("测试2: 行业相对强弱因子")
        print("=" * 60)
        try:
            calculate_Industry_Relative_Strength()
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
