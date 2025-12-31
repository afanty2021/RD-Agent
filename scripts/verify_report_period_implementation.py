#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证报告期概念实现

运行此脚本验证所有组件是否正常工作：
1. 数据文件存在性
2. 数据加载功能
3. 报告期访问器功能
4. 因子计算功能

使用方法：
    python scripts/verify_report_period_implementation.py

作者: RD-Agent Team
"""

import sys
from pathlib import Path


def check_data_file():
    """检查数据文件"""
    print("\n" + "="*70)
    print("1. 检查数据文件")
    print("="*70)

    h5_path = Path('git_ignore_folder/factor_implementation_source_data/daily_pv_report_period.h5')

    if not h5_path.exists():
        print(f"❌ 数据文件不存在: {h5_path}")
        print("请先运行: python scripts/prepare_report_period_data.py")
        return False

    file_size = h5_path.stat().st_size / 1024 / 1024
    print(f"✅ 数据文件存在: {h5_path}")
    print(f"   文件大小: {file_size:.2f} MB")

    return True


def check_data_loading():
    """检查数据加载"""
    print("\n" + "="*70)
    print("2. 检查数据加载")
    print("="*70)

    try:
        import pandas as pd

        h5_path = Path('git_ignore_folder/factor_implementation_source_data/daily_pv_report_period.h5')
        df = pd.read_hdf(h5_path, key='data')

        print(f"✅ 数据加载成功")
        print(f"   总记录数: {len(df):,}")
        print(f"   总列数: {len(df.columns)}")
        print(f"   日期范围: {df.index.get_level_values(0).min()} 至 {df.index.get_level_values(0).max()}")
        print(f"   股票数量: {df.index.get_level_values(1).nunique()}")

        # 检查财务字段
        financial_fields = ['ROE', 'EPS', 'DebtToAssets', 'CurrentRatio']
        existing_fields = [f for f in financial_fields if f in df.columns]
        print(f"   财务字段: {', '.join(existing_fields)}")

        return True
    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        return False


def check_accessor():
    """检查报告期访问器"""
    print("\n" + "="*70)
    print("3. 检查报告期访问器")
    print("="*70)

    try:
        from rdagent.scenarios.qlib.experiment.report_period_utils import ReportPeriodAccessor
        import pandas as pd

        h5_path = Path('git_ignore_folder/factor_implementation_source_data/daily_pv_report_period.h5')
        df = pd.read_hdf(h5_path, key='data')

        # 创建访问器
        accessor = ReportPeriodAccessor(df)

        # 获取统计信息
        stats = accessor.get_summary_stats()

        print(f"✅ 报告期访问器创建成功")
        print(f"   有财务报告的股票数: {stats['instruments_with_reports']}")
        print(f"   有财务数据的记录数: {stats['records_with_financial']:,}")
        print(f"   财务数据覆盖率: {stats['financial_coverage']:.2f}%")

        # 测试查询功能
        test_stock = list(accessor.report_map.keys())[0]
        test_date = '2025-12-29'
        test_value = accessor.get_financial_at_date(test_stock, test_date, 'ROE')

        print(f"\n   测试查询:")
        print(f"     股票: {test_stock}")
        print(f"     日期: {test_date}")
        print(f"     ROE: {test_value if test_value else 'N/A'}")

        return True
    except Exception as e:
        print(f"❌ 报告期访问器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_factor_calculator():
    """检查因子计算器"""
    print("\n" + "="*70)
    print("4. 检查因子计算器")
    print("="*70)

    try:
        from rdagent.scenarios.qlib.experiment.report_period_factor_example import FinancialFactorCalculator
        import pandas as pd

        h5_path = Path('git_ignore_folder/factor_implementation_source_data/daily_pv_report_period.h5')
        df = pd.read_hdf(h5_path, key='data')

        # 创建计算器
        calculator = FinancialFactorCalculator(df)

        print(f"✅ 因子计算器创建成功")

        # 测试ROE因子计算
        test_date = '2025-12-29'
        roe_factor = calculator.calculate_roe_factor(test_date)

        print(f"   ROE因子计算:")
        print(f"     日期: {test_date}")
        print(f"     有效股票数: {len(roe_factor)}")
        print(f"     均值: {roe_factor.mean():.4f}")
        print(f"     标准差: {roe_factor.std():.4f}")

        # 测试ROE动量因子计算
        momentum = calculator.calculate_roe_momentum_factor(test_date, periods=4)

        print(f"\n   ROE动量因子计算:")
        print(f"     有效股票数: {len(momentum)}")
        print(f"     均值: {momentum.mean():.4f}")
        print(f"     标准差: {momentum.std():.4f}")

        return True
    except Exception as e:
        print(f"❌ 因子计算器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_enhanced_loader():
    """检查增强数据加载器"""
    print("\n" + "="*70)
    print("5. 检查增强数据加载器")
    print("="*70)

    try:
        from rdagent.scenarios.qlib.experiment.utils_enhanced import EnhancedDataLoader

        loader = EnhancedDataLoader('git_ignore_folder/factor_implementation_source_data')

        # 测试加载报告期数据
        df = loader.load_report_period_data()

        if df.empty:
            print(f"⚠️  报告期数据为空")
            return False

        print(f"✅ 增强数据加载器测试成功")
        print(f"   报告期数据记录数: {len(df):,}")

        # 测试横截面查询
        instruments = list(df.index.get_level_values(1).unique())[:10]
        cross_section = loader.get_financial_with_report_period(
            df, instruments, '2025-12-29', 'ROE'
        )

        print(f"\n   横截面查询测试:")
        print(f"     查询股票数: {len(instruments)}")
        print(f"     有效结果数: {len(cross_section)}")

        return True
    except Exception as e:
        print(f"❌ 增强数据加载器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n" + "="*70)
    print("报告期概念实现验证")
    print("="*70)

    # 检查所有组件
    results = []
    results.append(("数据文件", check_data_file()))
    results.append(("数据加载", check_data_loading()))
    results.append(("报告期访问器", check_accessor()))
    results.append(("因子计算器", check_factor_calculator()))
    results.append(("增强数据加载器", check_enhanced_loader()))

    # 汇总结果
    print("\n" + "="*70)
    print("验证结果汇总")
    print("="*70)

    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")

    all_passed = all(result[1] for result in results)

    print("\n" + "="*70)
    if all_passed:
        print("✅ 所有测试通过！报告期概念实现正确。")
        print("\n下一步：")
        print("  1. 查看文档: rdagent/scenarios/qlib/experiment/REPORT_PERIOD_CONCEPT.md")
        print("  2. 运行演示: python -m rdagent.scenarios.qlib.experiment.report_period_factor_example")
        print("  3. 在RD-Agent中使用报告期数据生成因子")
    else:
        print("❌ 部分测试失败，请检查错误信息。")
    print("="*70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
