#!/usr/bin/env python3
"""
获取股票到行业的映射关系
从多种来源构建完整的映射表
"""

import pandas as pd
import json
from pathlib import Path
import tushare as ts
from datetime import datetime


def load_industry_data_from_qlib():
    """
    从 Qlib 行业数据文件加载行业信息
    """
    industry_dir = Path.home() / ".qlib/qlib_data/cn_data/industry_data"

    industries = {}

    # 加载申万2021分类
    for level in ['L1', 'L2', 'L3']:
        file = industry_dir / f"industry_SW2021_{level}_20251229_112014.csv"
        if file.exists():
            df = pd.read_csv(file, encoding='utf-8-sig')
            for _, row in df.iterrows():
                key = f"SW2021_{level}_{row['industry_code']}"
                industries[key] = {
                    'name': row['industry_name'],
                    'code': row['industry_code'],
                    'level': level,
                    'source': 'SW2021',
                    'index_code': row['index_code']
                }

    print(f"✓ 从 Qlib 加载了 {len(industries)} 个行业分类")
    return industries


def get_stock_industry_mapping_from_tushare(ts_token=None):
    """
    使用 Tushare API 获取股票到行业的映射

    Parameters
    ----------
    ts_token : str
        Tushare API token，如果为 None 则从配置文件读取

    Returns
    -------
    dict
        股票代码到行业的映射
    """
    if ts_token:
        ts.set_token(ts_token)

    try:
        pro = ts.pro_api()

        # 获取申万行业分类
        df_sw = pro.index_classify(level='L1', src='SW2021')

        # 获取股票-行业成分股关系
        mapping = {}

        # 获取所有申万一级行业指数
        industries = df_sw['index_code'].unique()

        for industry_idx in industries:
            try:
                # 获取该行业的成分股
                df_members = pro.index_member(index_code=industry_idx)

                for _, row in df_members.iterrows():
                    stock_code = row['con_code']
                    # 转换为 Qlib 格式 (如 SH600000, SZ000001)
                    exchange = row['market']  # SSE上交所, SZSE深交所
                    if exchange == 'SSE':
                        instrument = f"SH{stock_code}"
                    elif exchange == 'SZSE':
                        instrument = f"SZ{stock_code}"
                    else:
                        continue

                    if instrument not in mapping:
                        mapping[instrument] = {}

                    mapping[instrument]['SW2021_L1'] = industry_idx
                    mapping[instrument]['SW2021_L1_name'] = df_sw[df_sw['index_code'] == industry_idx]['index_name'].values[0]

            except Exception as e:
                print(f"获取行业 {industry_idx} 成分股失败: {e}")
                continue

        print(f"✓ 从 Tushare 获取了 {len(mapping)} 只股票的行业映射")
        return mapping

    except Exception as e:
        print(f"✗ Tushare API 调用失败: {e}")
        print("提示：请确保已配置 Tushare token")
        return {}


def get_stock_industry_mapping_from_akshare():
    """
    使用 AKShare 获取股票-行业映射（无需 API token）
    """
    try:
        import akshare as ak

        mapping = {}

        # 获取申万行业成分股
        # 一级行业
        try:
            sw_industries = ak.sw_index_cons(symbol="申万行业")
            print(f"找到 {len(sw_industries)} 个申万行业")
        except Exception as e:
            print(f"获取申万行业列表失败: {e}")
            return {}

        # 为每个行业获取成分股
        for industry_name in sw_industries['行业名称'].unique()[:10]:  # 限制前10个行业测试
            try:
                # 获取成分股
                df_cons = ak.sw_index_cons(symbol=industry_name)

                for _, row in df_cons.iterrows():
                    stock_code = row['股票代码']
                    instrument = f"{stock_code[:2]}{stock_code[3:]}"  # 转换格式

                    if instrument not in mapping:
                        mapping[instrument] = {}

                    mapping[instrument]['SW2021_L1_name'] = industry_name

            except Exception as e:
                continue

        print(f"✓ 从 AKShare 获取了 {len(mapping)} 只股票的行业映射")
        return mapping

    except ImportError:
        print("✗ AKShare 未安装，跳过此方法")
        return {}
    except Exception as e:
        print(f"✗ AKShare 获取失败: {e}")
        return {}


def create_sample_mapping():
    """
    创建一个示例映射表（用于测试）
    """
    # 常见股票的手动映射
    sample_mapping = {
        # 银行
        'SH600000': {'SW2021_L1_name': '银行', 'SW2021_L1_code': '210000'},
        'SH600036': {'SW2021_L1_name': '银行', 'SW2021_L1_code': '210000'},
        'SH601166': {'SW2021_L1_name': '银行', 'SW2021_L1_code': '210000'},
        'SH601398': {'SW2021_L1_name': '银行', 'SW2021_L1_code': '210000'},
        'SH601939': {'SW2021_L1_name': '银行', 'SW2021_L1_code': '210000'},
        'SH601988': {'SW2021_L1_name': '银行', 'SW2021_L1_code': '210000'},
        'SH002142': {'SW2021_L1_name': '银行', 'SW2021_L1_code': '210000'},

        # 食品饮料
        'SH600519': {'SW2021_L1_name': '食品饮料', 'SW2021_L1_code': '220000'},
        'SH000858': {'SW2021_L1_name': '食品饮料', 'SW2021_L1_code': '220000'},

        # 医药生物
        'SH600276': {'SW2021_L1_name': '医药生物', 'SW2021_L1_code': '230000'},
        'SZ000661': {'SW2021_L1_name': '医药生物', 'SW2021_L1_code': '230000'},

        # 房地产
        'SZ000002': {'SW2021_L1_name': '房地产', 'SW2021_L1_code': '240000'},
        'SH600048': {'SW2021_L1_name': '房地产', 'SW2021_L1_code': '240000'},

        # 汽车
        'SH600104': {'SW2021_L1_name': '汽车', 'SW2021_L1_code': '250000'},
        'SZ000625': {'SW2021_L1_name': '汽车', 'SW2021_L1_code': '250000'},
    }

    print(f"✓ 创建了示例映射表，包含 {len(sample_mapping)} 只股票")
    return sample_mapping


def save_mapping_to_files(mapping, output_dir=None):
    """
    将映射表保存为多种格式

    Parameters
    ----------
    mapping : dict
        股票到行业的映射
    output_dir : str
        输出目录
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "data" / "industry_mapping"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存为 JSON
    json_file = output_dir / "stock_industry_mapping.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON 文件已保存: {json_file}")

    # 保存为 CSV（平铺格式）
    df_list = []
    for instrument, info in mapping.items():
        row = {'instrument': instrument}
        row.update(info)
        df_list.append(row)

    df = pd.DataFrame(df_list)
    csv_file = output_dir / "stock_industry_mapping.csv"
    df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"✓ CSV 文件已保存: {csv_file}")

    # 保存为 Python 模块（可直接 import）
    py_file = output_dir / "stock_industry_mapping.py"
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('# 股票-行业映射表\n')
        f.write('# 自动生成于: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '\n\n')
        f.write('STOCK_INDUSTRY_MAPPING = {\n')
        for instrument, info in mapping.items():
            f.write(f'    "{instrument}": {info},\n')
        f.write('}\n')
    print(f"✓ Python 文件已保存: {py_file}")

    return {
        'json': json_file,
        'csv': csv_file,
        'python': py_file
    }


def load_mapping_for_factor(file_path=None):
    """
    为因子开发加载映射表

    Parameters
    ----------
    file_path : str
        映射文件路径

    Returns
    -------
    dict
        股票到行业的映射（简化格式）
    """
    if file_path is None:
        file_path = Path(__file__).parent.parent / "data" / "industry_mapping" / "stock_industry_mapping.json"

    with open(file_path, 'r', encoding='utf-8') as f:
        full_mapping = json.load(f)

    # 简化映射：只返回行业名称
    simplified_mapping = {}
    for instrument, info in full_mapping.items():
        if 'SW2021_L1_name' in info:
            simplified_mapping[instrument] = info['SW2021_L1_name']
        else:
            simplified_mapping[instrument] = '未知'

    return simplified_mapping


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="获取股票-行业映射关系")
    parser.add_argument("--source", choices=['tushare', 'akshare', 'sample'], default='sample',
                        help="数据源：tushare(需要token), akshare(无需token), sample(示例数据)")
    parser.add_argument("--token", help="Tushare API token")
    parser.add_argument("--output", help="输出目录")
    parser.add_argument("--save", action="store_true", help="保存映射到文件")

    args = parser.parse_args()

    print("=" * 60)
    print("获取股票-行业映射关系")
    print("=" * 60)

    # 加载行业数据信息
    industries = load_industry_data_from_qlib()

    # 获取股票-行业映射
    if args.source == 'tushare':
        print("\n使用 Tushare API 获取映射...")
        mapping = get_stock_industry_mapping_from_tushare(args.token)
    elif args.source == 'akshare':
        print("\n使用 AKShare 获取映射...")
        mapping = get_stock_industry_mapping_from_akshare()
    else:
        print("\n使用示例数据...")
        mapping = create_sample_mapping()

    if mapping:
        print(f"\n成功获取 {len(mapping)} 只股票的行业映射")

        # 显示部分映射
        print("\n示例映射:")
        for i, (instrument, info) in enumerate(list(mapping.items())[:5]):
            industry = info.get('SW2021_L1_name', '未知')
            print(f"  {instrument} -> {industry}")

        # 保存到文件
        if args.save:
            files = save_mapping_to_files(mapping, args.output)
            print(f"\n映射文件已保存到: {files['json'].parent}")
    else:
        print("\n未能获取映射数据，请检查配置或尝试其他数据源")
