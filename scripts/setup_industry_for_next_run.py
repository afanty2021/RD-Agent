#!/usr/bin/env python3
"""
为 RD-Agent 下次运行设置行业数据支持
确保工作空间中有所需的映射文件
"""

import shutil
from pathlib import Path
import json


def setup_industry_mapping_for_workspace():
    """
    设置行业映射，使其在 RD-Agent 工作空间中可用
    """

    project_root = Path(__file__).parent.parent
    mapping_dir = project_root / "data" / "industry_mapping"
    target_dir = project_root / "rdagent" / "scenarios" / "qlib" / "experiment" / "factor_data_template"

    print("=" * 60)
    print("设置行业映射数据")
    print("=" * 60)

    # 检查源文件
    if not mapping_dir.exists():
        print(f"❌ 映射目录不存在: {mapping_dir}")
        print("请先运行: python scripts/get_stock_industry_mapping.py --source sample --save")
        return False

    # 检查目标目录
    if not target_dir.exists():
        print(f"❌ 数据目录不存在: {target_dir}")
        print("请先运行因子数据生成脚本")
        return False

    # 复制映射文件
    files_to_copy = [
        "stock_industry_mapping.py",
        "stock_industry_mapping.json",
        "stock_industry_mapping.csv",
    ]

    for filename in files_to_copy:
        src = mapping_dir / filename
        dst = target_dir / filename

        if src.exists():
            shutil.copy2(src, dst)
            print(f"✓ 已复制: {filename}")
        else:
            print(f"⚠ 文件不存在: {filename}")

    print(f"\n✓ 映射文件已复制到: {target_dir}")

    # 创建一个简化版本的 industry_map.py，可以直接在代码中使用
    simple_mapping_file = target_dir / "industry_map.py"

    # 读取 JSON 映射
    json_file = mapping_dir / "stock_industry_mapping.json"
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)

        # 创建简化的映射（只有行业名称）
        simple_mapping = {
            k: v.get('SW2021_L1_name', '其他')
            for k, v in mapping.items()
        }

        # 写入 Python 文件
        with open(simple_mapping_file, 'w', encoding='utf-8') as f:
            f.write('# -*- coding: utf-8 -*-\n')
            f.write('# 简化的股票-行业映射表\n\n')
            f.write('INDUSTRY_MAP = {\n')
            for instrument, industry in list(simple_mapping.items())[:20]:  # 只显示前20个作为示例
                f.write(f'    "{instrument}": "{industry}",\n')
            if len(simple_mapping) > 20:
                f.write(f'    # ... 共 {len(simple_mapping)} 只股票\n')
            f.write('}\n\n')
            f.write('# 使用示例:\n')
            f.write('# df_reset[\'industry\'] = df_reset[\'instrument\'].map(INDUSTRY_MAP)\n')

        print(f"✓ 已创建简化映射: {simple_mapping_file}")

    print("\n" + "=" * 60)
    print("设置完成！")
    print("=" * 60)
    print("\n下次启动 RD-Agent 时，行业数据将可用。")
    print("\n使用方法:")
    print("  python -m rdagent.app.qlib_rd_loop.factor --loop_n 30")

    return True


def verify_setup():
    """验证设置是否正确"""

    project_root = Path(__file__).parent.parent
    target_dir = project_root / "rdagent" / "scenarios" / "qlib" / "experiment" / "factor_data_template"

    print("\n验证设置...")
    print("-" * 60)

    required_files = [
        "industry_map.py",
        "stock_industry_mapping.py",
    ]

    all_ok = True
    for filename in required_files:
        file_path = target_dir / filename
        if file_path.exists():
            print(f"✓ {filename} 存在")
        else:
            print(f"✗ {filename} 不存在")
            all_ok = False

    if all_ok:
        print("\n✅ 所有文件已就绪，可以启动 RD-Agent")
    else:
        print("\n⚠️  部分文件缺失，请重新运行设置脚本")

    return all_ok


def show_usage_example():
    """显示使用示例"""

    print("\n" + "=" * 60)
    print("行业数据使用示例")
    print("=" * 60)

    example_code = '''
# 在因子代码中使用行业映射

def calculate_Industry_Factor():
    import pandas as pd
    import numpy as np
    from industry_map import INDUSTRY_MAP

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 应用行业映射
    df_reset['industry'] = df_reset['instrument'].map(INDUSTRY_MAP)

    # 计算行业动量
    df_reset['stock_return'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=5)
    )

    df_reset['Industry_Momentum'] = df_reset.groupby(['datetime', 'industry'])['stock_return'].transform('mean')

    result = df_reset.set_index(['datetime', 'instrument'])[['Industry_Momentum']]
    result.to_hdf('result.h5', key='data')
'''

    print(example_code)
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="设置行业数据用于RD-Agent")
    parser.add_argument("--action", choices=['setup', 'verify', 'example'], default='setup',
                        help="执行的操作")

    args = parser.parse_args()

    if args.action == 'setup':
        success = setup_industry_mapping_for_workspace()
        if success:
            verify_setup()
            show_usage_example()

    elif args.action == 'verify':
        verify_setup()

    elif args.action == 'example':
        show_usage_example()
