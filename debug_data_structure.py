#!/usr/bin/env python3
"""
调试脚本：检查 daily_pv.h5 的实际数据结构
"""
import pandas as pd
import sys

def debug_data_structure(filepath='daily_pv.h5'):
    """检查数据文件的结构"""
    print("=" * 60)
    print("数据结构调试脚本")
    print("=" * 60)

    try:
        # 1. 加载数据
        print("\n[1] 正在加载数据...")
        df = pd.read_hdf(filepath, key='data')
        print(f"✓ 数据加载成功")
        print(f"  - 形状: {df.shape}")
        print(f"  - 索引类型: {type(df.index)}")
        print(f"  - 索引名称: {df.index.names}")

        # 2. 检查 MultiIndex
        print("\n[2] MultiIndex 信息:")
        if isinstance(df.index, pd.MultiIndex):
            print(f"  ✓ 是 MultiIndex")
            print(f"  - 第一级: {df.index.names[0]}")
            print(f"  - 第二级: {df.index.names[1]}")
            print(f"  - 第一级唯一值数量: {df.index.get_level_values(0).nunique()}")
            print(f"  - 第二级唯一值数量: {df.index.get_level_values(1).nunique()}")
        else:
            print(f"  ✗ 不是 MultiIndex")
            print(f"  - 索引名: {df.index.name}")

        # 3. 检查列名
        print("\n[3] 数据列:")
        print(f"  - 前5列: {df.columns.tolist()[:5]}")
        print(f"  - 总列数: {len(df.columns)}")

        # 4. reset_index 测试
        print("\n[4] reset_index 测试:")
        df_reset = df.reset_index()
        print(f"  ✓ reset_index 成功")
        print(f"  - 新形状: {df_reset.shape}")
        print(f"  - 前5列: {df_reset.columns.tolist()[:5]}")

        # 5. 检查 datetime 列
        print("\n[5] datetime 列检查:")
        if 'datetime' in df_reset.columns:
            print(f"  ✓ 'datetime' 列存在")
        else:
            print(f"  ✗ 'datetime' 列不存在")
            print(f"  - 可用的索引相关列:")
            for col in df_reset.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    print(f"    • {col}")

        # 6. 检查 instrument 列
        print("\n[6] instrument 列检查:")
        if 'instrument' in df_reset.columns:
            print(f"  ✓ 'instrument' 列存在")
        else:
            print(f"  ✗ 'instrument' 列不存在")
            print(f"  - 可用的品种相关列:")
            for col in df_reset.columns:
                if 'inst' in col.lower() or 'stock' in col.lower() or 'symbol' in col.lower():
                    print(f"    • {col}")

        # 7. 数据预览
        print("\n[7] 数据预览:")
        print(df.head(3))

        # 8. 诊断结论
        print("\n" + "=" * 60)
        print("诊断结论")
        print("=" * 60)

        time_col = None
        inst_col = None

        # 查找时间列
        for col in df_reset.columns:
            if col.lower() in ['datetime', 'date', 'time']:
                time_col = col
                break

        # 查找品种列
        for col in df_reset.columns:
            if col.lower() in ['instrument', 'symbol', 'code', 'stock']:
                inst_col = col
                break

        if time_col and inst_col:
            print(f"✓ 数据结构正常")
            print(f"  - 时间列: '{time_col}'")
            print(f"  - 品种列: '{inst_col}'")
            print(f"\n建议的因子代码:")
            print(f"  result = df_reset.set_index(['{time_col}', '{inst_col}'])[['FactorName']]")
        else:
            print(f"✗ 数据结构异常")
            print(f"  - 无法找到时间列或品种列")
            print(f"  - 请检查数据文件是否正确生成")

    except FileNotFoundError:
        print(f"\n✗ 错误: 找不到文件 '{filepath}'")
        print(f"  请确认文件路径是否正确")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 错误: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='调试 daily_pv.h5 数据结构')
    parser.add_argument('--file', default='daily_pv.h5', help='数据文件路径')
    args = parser.parse_args()

    debug_data_structure(args.file)
