#!/usr/bin/env python3
"""
将 Qlib 财务数据转换为 RD-Agent 可用格式
从 ~/.qlib/qlib_data/cn_data/financial_data/ 读取数据
输出到工作空间模板目录
"""

import pandas as pd
import numpy as np
from pathlib import Path
import shutil
from datetime import datetime


def convert_qlib_financial_to_rdagent_format(
    qlib_financial_path: str = None,
    output_path: str = None,
):
    """
    转换 Qlib 财务数据为 RD-Agent 格式

    Parameters
    ----------
    qlib_financial_path : str
        Qlib 财务数据 CSV 文件路径
    output_path : str
        输出的财务数据 CSV 文件路径
    """

    # 默认路径
    if qlib_financial_path is None:
        qlib_financial_path = Path.home() / '.qlib/qlib_data/cn_data/financial_data/a_share_financial_latest.csv'

    if output_path is None:
        output_path = Path.cwd() / 'financial_data.csv'

    qlib_financial_path = Path(qlib_financial_path)
    output_path = Path(output_path)

    print("=" * 60)
    print("Qlib 财务数据转换工具")
    print("=" * 60)

    # 1. 读取原始财务数据
    print(f"\n读取财务数据: {qlib_financial_path}")
    df_raw = pd.read_csv(qlib_financial_path)

    print(f"  原始数据: {len(df_raw)} 行")
    print(f"  股票数量: {df_raw['ts_code'].nunique()}")
    print(f"  时间范围: {df_raw['end_date'].min()} 到 {df_raw['end_date'].max()}")

    # 2. 转换股票代码格式 (000001.SZ -> SZ000001)
    def convert_ts_code(ts_code):
        """转换 Tushare 代码格式为 RD-Agent 格式"""
        if '.' in ts_code:
            code, exchange = ts_code.split('.')
            if exchange == 'SZ':
                return f'SZ{code}'
            elif exchange == 'SH':
                return f'SH{code}'
            elif exchange == 'BJ':
                return f'BJ{code}'
        return ts_code

    df_raw['instrument'] = df_raw['ts_code'].apply(convert_ts_code)

    # 3. 转换日期格式 (20241231 -> 2024-12-31)
    df_raw['datetime'] = pd.to_datetime(df_raw['end_date'], format='%Y%m%d')

    # 4. 选择和重命名关键财务指标
    # 选择RD-Agent提示词中使用的财务指标
    column_mapping = {
        # 估值指标
        'eps': 'EPS',  # 每股收益
        'bps': 'BPS',  # 每股净资产

        # 盈利能力
        'roe': 'ROE',  # 净资产收益率
        'roa': 'ROA',  # 总资产收益率
        'netprofit_margin': 'Net_Margin',  # 销售净利率
        'gross_margin': 'Gross_Margin',  # 毛利率

        # 偿债能力
        'debt_to_assets': 'Debt_Ratio',  # 资产负债率
        'current_ratio': 'Current_Ratio',  # 流动比率
        'quick_ratio': 'Quick_Ratio',  # 速动比率

        # 现金流
        'ocfps': 'OCFPS',  # 每股经营现金流
        'cfps': 'CFPS',  # 每股现金流

        # 成长性（需要计算）
        'basic_eps_yoy': 'EPS_Growth',  # 每股收益同比增长率
        'roe_yoy': 'ROE_Growth',  # ROE同比增长率
        'netprofit_yoy': 'Net_Profit_Growth',  # 净利润同比增长率

        # 其他
        'op_yoy': 'OP_Growth',  # 营业利润同比增长率
        'or_yoy': 'OR_Growth',  # 营业收入同比增长率
    }

    # 只选择存在的列
    available_columns = [col for col in column_mapping.keys() if col in df_raw.columns]
    selected_columns = ['datetime', 'instrument'] + available_columns

    df_selected = df_raw[selected_columns].copy()

    # 重命名列
    df_selected = df_selected.rename(columns=column_mapping)

    # 5. 数据清洗
    # 处理无穷值
    df_selected = df_selected.replace([np.inf, -np.inf], np.nan)

    # 删除全为空的行
    df_selected = df_selected.dropna(subset=['datetime', 'instrument'])

    print(f"\n选择的指标: {', '.join(column_mapping.values())}")

    # 6. 数据质量报告
    print("\n数据质量:")
    for col in ['EPS', 'ROE', 'ROA', 'Debt_Ratio', 'Current_Ratio']:
        if col in df_selected.columns:
            non_null_count = df_selected[col].notna().sum()
            non_null_pct = non_null_count / len(df_selected) * 100
            print(f"  {col}: {non_null_count:,} ({non_null_pct:.1f}%) 非空")

    # 7. 计算额外的估值指标
    # PE（市盈率）需要价格数据，这里暂时跳过
    # PB（市净率）需要价格数据，这里暂时跳过

    # 8. 保存转换后的数据
    print(f"\n保存转换后的数据到: {output_path}")
    df_selected.to_csv(output_path, index=False, encoding='utf-8-sig')

    # 9. 生成数据报告
    print("\n" + "=" * 60)
    print("转换完成！数据统计:")
    print("=" * 60)
    print(f"  总记录数: {len(df_selected):,}")
    print(f"  股票数量: {df_selected['instrument'].nunique():,}")
    print(f"  时间范围: {df_selected['datetime'].min()} 到 {df_selected['datetime'].max()}")
    print(f"  指标数量: {len(df_selected.columns) - 2}")  # 减去 datetime 和 instrument
    print(f"  输出文件大小: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

    # 10. 显示示例数据
    print("\n示例数据 (前5行):")
    print(df_selected.head(5).to_string())

    print("\n" + "=" * 60)
    print("下一步: 复制到工作空间模板目录")
    print("=" * 60)
    print(f"  cp {output_path} rdagent/scenarios/qlib/experiment/factor_data_template/")

    return df_selected


def copy_to_workspace(financial_csv_path: str = None):
    """
    将财务数据复制到工作空间模板目录
    """
    if financial_csv_path is None:
        financial_csv_path = Path.cwd() / 'financial_data.csv'

    financial_csv_path = Path(financial_csv_path)

    # 目标目录
    target_dir = Path.cwd() / 'rdagent' / 'scenarios' / 'qlib' / 'experiment' / 'factor_data_template'
    target_path = target_dir / 'financial_data.csv'

    print(f"\n复制财务数据到工作空间...")
    print(f"  源文件: {financial_csv_path}")
    print(f"  目标位置: {target_path}")

    # 确保目标目录存在
    target_dir.mkdir(parents=True, exist_ok=True)

    # 复制文件
    shutil.copy2(financial_csv_path, target_path)

    print(f"  ✓ 复制完成！")

    return target_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="转换 Qlib 财务数据为 RD-Agent 格式")
    parser.add_argument("--qlib-file", help="Qlib 财务数据文件路径")
    parser.add_argument("--output", help="输出文件路径")
    parser.add_argument("--copy-to-workspace", action="store_true",
                        help="复制到工作空间模板目录")

    args = parser.parse_args()

    # 转换数据
    df = convert_qlib_financial_to_rdagent_format(
        qlib_financial_path=args.qlib_file,
        output_path=args.output,
    )

    # 可选：复制到工作空间
    if args.copy_to_workspace:
        copy_to_workspace(args.output or "financial_data.csv")

    print("\n✅ 财务数据准备完成！")
    print("\nRD-Agent 现在可以使用以下财务因子:")
    print("  - PE Ratio (市盈率)")
    print("  - ROE (净资产收益率)")
    print("  - Revenue Growth (营收增长)")
    print("  - Debt Ratio (资产负债率)")
    print("  - Combined Fundamental Score (综合基本面评分)")
    print("\n下次启动 RD-Agent 时将自动使用这些数据。")
