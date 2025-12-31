#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据使用示例 - 主运行脚本
========================

提供便捷的接口运行所有示例或单个示例。

使用方法：
    # 运行所有示例
    python run_all_examples.py --all

    # 运行单个示例
    python run_all_examples.py --example 1

    # 列出所有示例
    python run_all_examples.py --list

可用示例：
    1. 基础财务因子（ROE, PE, DebtToAssets）
    2. 复合因子：价值 + 动量组合
    3. 行业相对强度因子
    4. 报告期概念：正确的财务数据使用方法
"""

import argparse
import subprocess
import sys
from pathlib import Path


# 示例配置
EXAMPLES = {
    1: {
        "name": "基础财务因子",
        "script": "ex01_basic_financial_factors.py",
        "description": "演示如何使用 ROE、PE、DebtToAssets 等基础财务数据创建因子",
        "output": "ex01_basic_financial_factors_output.h5"
    },
    2: {
        "name": "复合因子：价值 + 动量",
        "script": "ex02_composite_value_momentum.py",
        "description": "演示如何结合价值和动量信号创建复合因子（学术界公认的有效组合）",
        "output": "ex02_composite_value_momentum_output.h5"
    },
    3: {
        "name": "行业相对强度因子",
        "script": "ex03_industry_relative_strength.py",
        "description": "演示如何使用行业分类数据创建行业中性因子",
        "output": "ex03_industry_relative_strength_output.h5"
    },
    4: {
        "name": "报告期概念",
        "script": "ex04_report_period_roe.py",
        "description": "演示如何正确使用季度财务数据，避免前视偏差",
        "output": "ex04_report_period_roe_output.h5"
    }
}


def list_examples():
    """列出所有可用示例"""
    print("\n" + "=" * 70)
    print("📚 可用示例列表")
    print("=" * 70)

    for num, example in EXAMPLES.items():
        print(f"\n示例 {num}: {example['name']}")
        print(f"   📄 脚本: {example['script']}")
        print(f"   📖 描述: {example['description']}")
        print(f"   💾 输出: {example['output']}")

    print("\n" + "=" * 70)
    print("使用方法:")
    print("   python run_all_examples.py --example <编号>")
    print("   python run_all_examples.py --all")
    print("=" * 70)


def run_example(example_num: int) -> bool:
    """
    运行单个示例

    Args:
        example_num: 示例编号

    Returns:
        是否成功运行
    """
    if example_num not in EXAMPLES:
        print(f"❌ 错误: 示例 {example_num} 不存在！")
        print(f"   使用 --list 查看所有可用示例")
        return False

    example = EXAMPLES[example_num]
    script_path = Path(__file__).parent / example["script"]

    if not script_path.exists():
        print(f"❌ 错误: 找不到脚本文件 {script_path}")
        return False

    print("\n" + "=" * 70)
    print(f"🚀 运行示例 {example_num}: {example['name']}")
    print("=" * 70)

    try:
        # 运行脚本
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=Path(__file__).parent,
            check=True
        )

        if result.returncode == 0:
            print(f"\n✅ 示例 {example_num} 运行成功！")
            print(f"   输出文件: {example['output']}")
            return True
        else:
            print(f"\n❌ 示例 {example_num} 运行失败！")
            return False

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 运行错误: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 未知错误: {e}")
        return False


def run_all_examples():
    """运行所有示例"""
    print("\n" + "=" * 70)
    print("🚀 运行所有示例")
    print("=" * 70)

    results = {}

    for example_num in EXAMPLES.keys():
        success = run_example(example_num)
        results[example_num] = success

        # 示例之间的间隔
        if example_num < len(EXAMPLES):
            print("\n" + "─" * 70)
            print()

    # 汇总结果
    print("\n" + "=" * 70)
    print("📊 运行结果汇总")
    print("=" * 70)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for example_num, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        example = EXAMPLES[example_num]
        print(f"   示例 {example_num}: {example['name']:30s} {status}")

    print("\n" + "=" * 70)
    print(f"总计: {success_count}/{total_count} 个示例运行成功")
    print("=" * 70)

    return success_count == total_count


def check_data_availability():
    """检查数据文件是否可用"""
    print("\n🔍 检查数据文件可用性...")

    data_paths = [
        Path.home() / "git_ignore_folder/factor_implementation_source_data/daily_pv.h5",
        Path.home() / "git_ignore_folder/factor_implementation_source_data/daily_pv_report_period.h5"
    ]

    found = False
    for data_path in data_paths:
        if data_path.exists():
            print(f"✅ 找到数据文件: {data_path}")
            found = True
            break

    if not found:
        print(f"⚠️  警告: 未找到数据文件！")
        print(f"   预期路径: {data_paths[0]}")
        print(f"   请确保数据文件存在，否则示例将无法运行")

    return found


def check_dependencies():
    """检查依赖包"""
    print("\n🔍 检查依赖包...")

    required_packages = {
        "pandas": "pandas",
        "numpy": "numpy",
        "tables": "pytables"
    }

    missing_packages = []

    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - 未安装")
            missing_packages.append(package_name)

    if missing_packages:
        print(f"\n⚠️  缺少依赖包: {', '.join(missing_packages)}")
        print(f"   安装命令: pip install {' '.join(missing_packages)}")
        return False

    return True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="数据使用示例运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python run_all_examples.py --all           运行所有示例
    python run_all_examples.py --example 1     运行示例 1
    python run_all_examples.py --list          列出所有示例
        """
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有示例"
    )

    parser.add_argument(
        "--example",
        type=int,
        metavar="N",
        help="运行单个示例（编号 1-4）"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有可用示例"
    )

    parser.add_argument(
        "--check-only",
        action="store_true",
        help="仅检查环境和数据，不运行示例"
    )

    args = parser.parse_args()

    # 检查模式
    if args.check_only:
        print("\n🔍 环境检查模式")
        print("=" * 70)
        deps_ok = check_dependencies()
        data_ok = check_data_availability()

        print("\n" + "=" * 70)
        if deps_ok and data_ok:
            print("✅ 环境检查通过！可以运行示例")
        else:
            print("⚠️  环境检查发现问题，请解决后再运行示例")
        print("=" * 70)
        return

    # 列表模式
    if args.list:
        list_examples()
        return

    # 运行单个示例
    if args.example:
        run_example(args.example)
        return

    # 运行所有示例
    if args.all:
        # 先检查环境
        deps_ok = check_dependencies()
        data_ok = check_data_availability()

        if not (deps_ok and data_ok):
            print("\n⚠️  环境检查失败！")
            print("   使用 --check-only 查看详细信息")
            return

        run_all_examples()
        return

    # 没有参数，显示帮助
    parser.print_help()


if __name__ == "__main__":
    main()
