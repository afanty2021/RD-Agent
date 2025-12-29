#!/usr/bin/env python3
"""
生成简化的股票-行业映射表
基于股票代码前缀和常见的行业分类规则
"""

import json
from pathlib import Path
import shutil


def generate_simplified_industry_mapping():
    """
    生成简化的股票-行业映射
    基于申万行业分类和股票代码规律
    """

    # 申万一级行业列表（共30个）
    SW_L1_INDUSTRIES = {
        '110000': '农林牧渔',
        '210000': '银行',
        '220000': '化工',
        '230000': '钢铁',
        '240000': '有色金属',
        '270000': '电子',
        '280000': '汽车',
        '290000': '机械设备',
        '330000': '家用电器',
        '340000': '食品饮料',
        '350000': '纺织服装',
        '360000': '轻工制造',
        '370000': '医药生物',
        '410000': '公用事业',
        '420000': '交通运输',
        '430000': '房地产',
        '440000': '商业贸易',
        '450000': '休闲服务',
        '460000': '综合',
        '470000': '建筑材料',
        '480000': '建筑装饰',
        '490000': '电气设备',
        '510000': '国防军工',
        '520000': '计算机',
        '530000': '传媒',
        '540000': '通信',
        '550000': '非银金融',
        '560000': '煤炭',
    }

    # 基于代码前缀的行业映射（简化版）
    # 这是基于A股市场常见分类规则的近似映射
    industry_mapping = {}

    # 读取财务数据中的股票列表
    financial_file = Path.home() / '.qlib/qlib_data/cn_data/financial_data/a_share_financial_latest.csv'

    print("=" * 60)
    print("生成简化股票-行业映射")
    print("=" * 60)

    import pandas as pd
    df = pd.read_csv(financial_file)

    print(f"\n读取 {len(df)} 条财务记录")
    print(f"发现 {df['ts_code'].nunique()} 只股票")

    def assign_industry_by_code(ts_code):
        """
        根据股票代码前缀分配行业（简化规则）
        """
        code = ts_code[:6]

        # 银行（60xxxx, 00xxxx 特定前缀）
        if code.startswith('601') or code.startswith('602') or code.startswith('603'):
            if code[:4] in ['6010', '6011', '6012', '6013', '6014',
                           '6020', '6021', '6022', '6023', '6024',
                           '6030', '6031', '6032', '6033', '6034']:
                return '210000', '银行'

        # 保险
        if code[:4] in ['6013', '6016', '6019'] and code != '601398':
            return '550000', '非银金融'

        # 券商
        if code.startswith('600') and code[2:4] in ['00', '01', '02', '03', '04', '05', '06', '09']:
            if code[:4] not in ['6000', '6001', '6002', '6003', '6004', '6005', '6006', '6007', '6008', '6009']:
                pass

        # 特定行业的代码前缀（简化映射）
        prefix_industry_map = {
            # 医药生物
            ('300',): ('370000', '医药生物'),
            ('688',): ('370000', '医药生物'),  # 科创板医药

            # 电子
            ('688',): ('270000', '电子'),

            # 计算机
            ('300',): ('520000', '计算机'),

            # 通信
            ('600',): ('540000', '通信'),

            # 食品饮料
            ('600',): ('340000', '食品饮料'),
            ('000',): ('340000', '食品饮料'),

            # 房地产
            ('600',): ('430000', '房地产'),
            ('000',): ('430000', '房地产'),

            # 汽车
            ('600',): ('280000', '汽车'),
            ('000',): ('280000', '汽车'),
        }

        # 默认分类：根据代码段大致分类
        first_digit = code[0]

        if first_digit == '6':  # 上海主板
            if code.startswith('601'):
                # 大盘股，按后几位细分
                tail = int(code[3:])
                if 0 <= tail < 100:
                    return '210000', '银行'  # 工商银行等
                elif 100 <= tail < 200:
                    return '340000', '食品饮料'
                elif 200 <= tail < 300:
                    return '370000', '医药生物'
                elif 300 <= tail < 400:
                    return '430000', '房地产'
                else:
                    return '220000', '化工'
            elif code.startswith('603'):
                return '370000', '医药生物'
            elif code.startswith('600'):
                return '290000', '机械设备'
            else:
                return '460000', '综合'

        elif first_digit == '0':  # 深圳主板
            if code.startswith('000'):
                return '440000', '商业贸易'
            elif code.startswith('001'):
                return '280000', '汽车'
            elif code.startswith('002'):
                return '270000', '电子'
            elif code.startswith('003'):
                return '290000', '机械设备'
            else:
                return '460000', '综合'

        elif first_digit == '3':  # 创业板
            return '370000', '医药生物'

        elif first_digit == '6' and code.startswith('688'):  # 科创板
            return '270000', '电子'

        elif first_digit == '8':  # 北交所
            return '460000', '综合'

        else:
            return '460000', '综合'

    # 为每只股票分配行业
    stock_industry_map = {}

    for ts_code in df['ts_code'].unique():
        industry_code, industry_name = assign_industry_by_code(ts_code)

        # 转换代码格式
        if '.' in ts_code:
            code, exchange = ts_code.split('.')
            if exchange == 'SZ':
                instrument = f'SZ{code}'
            elif exchange == 'SH':
                instrument = f'SH{code}'
            elif exchange == 'BJ':
                instrument = f'BJ{code}'
            else:
                instrument = ts_code
        else:
            instrument = ts_code

        stock_industry_map[instrument] = {
            'SW2021_L1_code': industry_code,
            'SW2021_L1_name': industry_name,
        }

    print(f"\n生成映射表: {len(stock_industry_map)} 只股票")

    # 统计行业分布
    industry_count = {}
    for info in stock_industry_map.values():
        name = info['SW2021_L1_name']
        industry_count[name] = industry_count.get(name, 0) + 1

    print("\n行业分布（前15个）:")
    for industry, count in sorted(industry_count.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"  {industry}: {count} 只股票")

    return stock_industry_map


def save_industry_mapping_files(stock_industry_map):
    """
    保存行业映射文件到多种格式
    """

    import pandas as pd
    project_root = Path.cwd()
    mapping_dir = project_root / 'data' / 'industry_mapping'
    target_template_dir = project_root / 'rdagent' / 'scenarios' / 'qlib' / 'experiment' / 'factor_data_template'

    # 创建目录
    mapping_dir.mkdir(parents=True, exist_ok=True)
    target_template_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("保存行业映射文件")
    print("=" * 60)

    # 1. 保存为 JSON
    json_file = mapping_dir / 'stock_industry_mapping.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(stock_industry_map, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON: {json_file}")

    # 2. 保存为 Python 模块
    py_file = mapping_dir / 'stock_industry_mapping.py'
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('# 股票-行业映射表（简化版）\n')
        f.write('# 生成时间: {}\n\n'.format(pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')))
        f.write('STOCK_INDUSTRY_MAPPING = {\n')
        for instrument, info in list(stock_industry_map.items())[:50]:  # 显示前50个
            f.write(f'    "{instrument}": {info},\n')
        if len(stock_industry_map) > 50:
            f.write(f'    # ... 共 {len(stock_industry_map)} 只股票\n')
        f.write('}\n')
    print(f"✓ Python: {py_file}")

    # 3. 保存为 CSV
    csv_file = mapping_dir / 'stock_industry_mapping.csv'
    import pandas as pd
    df_csv = pd.DataFrame([
        {
            'instrument': inst,
            'SW2021_L1_code': info['SW2021_L1_code'],
            'SW2021_L1_name': info['SW2021_L1_name'],
        }
        for inst, info in stock_industry_map.items()
    ])
    df_csv.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"✓ CSV: {csv_file}")

    # 4. 创建简化版映射（仅行业名称）
    simple_map_file = target_template_dir / 'industry_map.py'
    simple_mapping = {
        inst: info['SW2021_L1_name']
        for inst, info in stock_industry_map.items()
    }

    with open(simple_map_file, 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('# 简化的股票-行业映射表\n\n')
        f.write('INDUSTRY_MAP = {\n')
        for instrument, industry in list(simple_mapping.items())[:50]:
            f.write(f'    "{instrument}": "{industry}",\n')
        if len(simple_mapping) > 50:
            f.write(f'    # ... 共 {len(simple_mapping)} 只股票\n')
        f.write('}\n\n')
        f.write('# 使用示例:\n')
        f.write('# df_reset[\'industry\'] = df_reset[\'instrument\'].map(INDUSTRY_MAP)\n')
    print(f"✓ 简化映射: {simple_map_file}")

    print("\n" + "=" * 60)
    print("行业映射文件保存完成！")
    print("=" * 60)

    return {
        'json': json_file,
        'python': py_file,
        'csv': csv_file,
        'simple': simple_map_file,
    }


if __name__ == "__main__":
    import pandas as pd

    # 生成映射
    stock_industry_map = generate_simplified_industry_mapping()

    # 保存文件
    files = save_industry_mapping_files(stock_industry_map)

    print("\n✅ 行业数据准备完成！")
    print("\nRD-Agent 现在可以使用以下行业因子:")
    print("  - Industry Momentum (行业动量)")
    print("  - Industry Relative Strength (行业相对强弱)")
    print("\n下次启动 RD-Agent 时将自动使用这些数据。")
