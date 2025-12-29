#!/usr/bin/env python3
"""
生成基于申万2021二级行业的股票-行业映射表
提供更精细的行业分类（104个二级行业）
"""

import json
import pandas as pd
from pathlib import Path


def load_sw2021_l2_industries():
    """加载申万2021二级行业分类"""
    l2_file = Path.home() / '.qlib/qlib_data/cn_data/industry_data/industry_SW2021_L2_20251229_112014.csv'
    df_l2 = pd.read_csv(l2_file)

    industries = {}
    for _, row in df_l2.iterrows():
        industries[row['industry_code']] = {
            'code': row['industry_code'],
            'name': row['industry_name'],
            'level': 'L2',
            'parent_code': row['parent_code'],
        }

    print(f"加载申万2021二级行业: {len(industries)} 个")
    return industries


def assign_l2_industry_smart(code, l2_industries):
    """
    根据股票代码智能分配申万2021二级行业
    使用更简化的分类逻辑
    """

    # 银行（细分）
    if code.startswith('601') or code.startswith('602') or code.startswith('603'):
        # 根据代码后三位细分银行类型
        tail = int(code[3:])
        if 0 <= tail <= 99:
            return '210100', '国有大行'
        elif 100 <= tail <= 299:
            return '210200', '股份制银行'
        elif 300 <= tail <= 699:
            return '210300', '城商行'
        elif 700 <= tail <= 999:
            return '210400', '农商行'

    # 证券
    if code.startswith('600') or code.startswith('601'):
        if code[2:4] in ['00', '01', '02', '03', '04', '05', '06', '09', '10', '11', '12']:
            return '550200', '证券'

    # 保险
    if code[:4] in ['6013', '6016', '6019'] and code != '601398':
        return '550100', '保险'

    # 房地产
    if code.startswith('600') or code.startswith('000'):
        return '430100', '房地产开发'

    # 医药生物（细分）
    if code.startswith('688') or code.startswith('300'):
        # 科创板和创业板的医药股票
        last3 = int(code[-3:])
        if 0 <= last3 <= 99:
            return '370100', '化学药'
        elif 100 <= last3 <= 199:
            return '370200', '中药'
        elif 200 <= last3 <= 399:
            return '370300', '医疗器械'
        else:
            return '370400', '生物制品'

    # 电子（细分）
    if code.startswith('688') or code.startswith('002') or code.startswith('300'):
        last3 = int(code[-3:]) if code[-3:].isdigit() else 0
        if 0 <= last3 <= 99:
            return '270100', '半导体'
        elif 100 <= last3 <= 199:
            return '270200', '消费电子'
        elif 200 <= last3 <= 299:
            return '270300', '光学光电子'
        else:
            return '270400', '元件'

    # 计算机应用
    if code.startswith('300') or code.startswith('002'):
        return '520200', '计算机应用'

    # 通信
    if code.startswith('600') or code.startswith('000'):
        if code[:4] in ['6000', '0000', '6017']:
            return '540100', '通信运营'
        else:
            return '540200', '通信设备'

    # 电气设备（细分）
    if code.startswith('300') or code.startswith('688'):
        last3 = int(code[-3:]) if code[-3:].isdigit() else 0
        if 0 <= last3 <= 199:
            return '490100', '光伏设备'
        else:
            return '490300', '电网设备'

    # 汽车（细分）
    if code.startswith('600') or code.startswith('000'):
        last3 = int(code[-3:]) if code[-3:].isdigit() else 0
        if 0 <= last3 <= 99:
            return '280100', '汽车整车'
        else:
            return '280200', '汽车零部件'

    # 食品饮料（细分）
    if code.startswith('600') or code.startswith('000'):
        # 白酒（特定代码）
        if code in ['600519', '000858', '000568', '600809', '002304']:
            return '340100', '白酒'
        else:
            return '340200', '食品加工'

    # 化工
    if code.startswith('600') or code.startswith('000'):
        return '220200', '化学原料'

    # 有色金属
    if code.startswith('600') or code.startswith('000'):
        if code in ['600547', '600489']:
            return '240400', '黄金'
        else:
            return '240300', '工业金属'

    # 煤炭
    if code.startswith('600') or code.startswith('000'):
        return '210200', '煤炭开采'

    # 建筑材料
    if code.startswith('600') or code.startswith('000'):
        return '470100', '水泥制造'

    # 交通运输
    if code.startswith('600') or code.startswith('000'):
        return '420100', '航空运输'

    # 商业贸易
    if code.startswith('600') or code.startswith('000'):
        return '450100', '一般零售'

    # 传媒
    if code.startswith('300') or code.startswith('002'):
        return '530100', '传媒'

    # 国防军工
    if code.startswith('600') or code.startswith('000'):
        return '650100', '航空航天'

    # 公用事业
    if code.startswith('600') or code.startswith('000'):
        return '410100', '电力'

    # 纺织服装
    if code.startswith('600') or code.startswith('000'):
        return '350100', '纺织制造'

    # 轻工制造
    if code.startswith('600') or code.startswith('000'):
        return '360100', '造纸'

    # 机械设备
    if code.startswith('600') or code.startswith('000'):
        return '640100', '通用机械'

    # 家用电器
    if code.startswith('600') or code.startswith('000'):
        if code in ['000333', '000651', '600690', '002050']:
            return '330100', '白电'
        elif code in ['000100', '600060', '000725']:
            return '330200', '黑电'
        else:
            return '330300', '小家电'

    # 农林牧渔
    if code.startswith('600') or code.startswith('000'):
        return '110100', '种植'

    # 默认分类（基于代码段）
    first_digit = code[0]

    if first_digit == '6':  # 上海主板
        return '460100', '综合'
    elif first_digit == '0':  # 深圳主板
        return '460100', '综合'
    elif first_digit == '3':  # 创业板
        return '370100', '化学药'
    elif first_digit == '8':  # 北交所
        return '460100', '综合'
    else:
        return '460100', '综合'


def generate_l2_industry_mapping():
    """生成基于申万2021二级行业的股票映射"""

    print("=" * 60)
    print("生成申万2021二级行业股票映射")
    print("=" * 60)

    # 加载二级行业列表
    l2_industries = load_sw2021_l2_industries()

    # 读取财务数据中的股票列表
    financial_file = Path.home() / '.qlib/qlib_data/cn_data/financial_data/a_share_financial_latest.csv'
    df = pd.read_csv(financial_file)

    print(f"\n读取 {len(df)} 条财务记录")
    print(f"发现 {df['ts_code'].nunique()} 只股票")

    # 为每只股票分配二级行业
    stock_industry_map = {}
    industry_count = {}

    for ts_code in df['ts_code'].unique():
        code_6 = ts_code[:6]

        # 获取二级行业
        industry_code, industry_name = assign_l2_industry_smart(code_6, l2_industries)

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
            'SW2021_L2_code': industry_code,
            'SW2021_L2_name': industry_name,
        }

        # 统计行业分布
        industry_count[industry_name] = industry_count.get(industry_name, 0) + 1

    print(f"\n生成映射表: {len(stock_industry_map)} 只股票")
    print(f"行业分布（前20个）:")

    # 按股票数量排序
    sorted_industries = sorted(industry_count.items(), key=lambda x: x[1], reverse=True)
    for industry, count in sorted_industries[:20]:
        pct = count / len(stock_industry_map) * 100
        print(f"  {industry}: {count} 只股票 ({pct:.1f}%)")

    print(f"\n... 共 {len(industry_count)} 个二级行业")

    return stock_industry_map, industry_count


def save_l2_industry_mapping_files(stock_industry_map, industry_count):
    """保存二级行业映射文件"""

    import pandas as pd
    project_root = Path.cwd()
    mapping_dir = project_root / 'data' / 'industry_mapping'
    target_template_dir = project_root / 'rdagent' / 'scenarios' / 'qlib' / 'experiment' / 'factor_data_template'

    # 创建目录
    mapping_dir.mkdir(parents=True, exist_ok=True)
    target_template_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 60)
    print("保存申万2021二级行业映射文件")
    print("=" * 60)

    # 1. 保存为 JSON
    json_file = mapping_dir / 'stock_industry_mapping_l2.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(stock_industry_map, f, ensure_ascii=False, indent=2)
    print(f"✓ JSON: {json_file}")

    # 2. 保存为 Python 模块
    py_file = mapping_dir / 'stock_industry_mapping_l2.py'
    with open(py_file, 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('# 股票-申万2021二级行业映射表\n')
        f.write('# 生成时间: {}\n\n'.format(pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')))
        f.write('STOCK_INDUSTRY_MAPPING_L2 = {\n')
        for instrument, info in list(stock_industry_map.items())[:50]:
            f.write(f'    "{instrument}": {info},\n')
        if len(stock_industry_map) > 50:
            f.write(f'    # ... 共 {len(stock_industry_map)} 只股票\n')
        f.write('}\n')
    print(f"✓ Python: {py_file}")

    # 3. 保存为 CSV
    csv_file = mapping_dir / 'stock_industry_mapping_l2.csv'
    df_csv = pd.DataFrame([
        {
            'instrument': inst,
            'SW2021_L2_code': info['SW2021_L2_code'],
            'SW2021_L2_name': info['SW2021_L2_name'],
        }
        for inst, info in stock_industry_map.items()
    ])
    df_csv.to_csv(csv_file, index=False, encoding='utf-8-sig')
    print(f"✓ CSV: {csv_file}")

    # 4. 创建简化版映射（仅行业名称，供因子代码直接使用）
    simple_map_file = target_template_dir / 'industry_map_l2.py'
    simple_mapping = {
        inst: info['SW2021_L2_name']
        for inst, info in stock_industry_map.items()
    }

    with open(simple_map_file, 'w', encoding='utf-8') as f:
        f.write('# -*- coding: utf-8 -*-\n')
        f.write('# 申万2021二级行业映射表（简化版）\n\n')
        f.write('INDUSTRY_MAP_L2 = {\n')
        for instrument, industry in list(simple_mapping.items())[:50]:
            f.write(f'    "{instrument}": "{industry}",\n')
        if len(simple_mapping) > 50:
            f.write(f'    # ... 共 {len(simple_mapping)} 只股票\n')
        f.write('}\n\n')
        f.write('# 使用示例:\n')
        f.write('# df_reset[\'industry\'] = df_reset[\'instrument\'].map(INDUSTRY_MAP_L2)\n')
    print(f"✓ 简化映射: {simple_map_file}")

    # 5. 生成行业统计报告
    report_file = mapping_dir / 'l2_industry_distribution_report.txt'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("申万2021二级行业分布统计报告\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"总股票数: {len(stock_industry_map)}\n")
        f.write(f"二级行业数: {len(industry_count)}\n\n")
        f.write("行业分布:\n")
        f.write("-" * 60 + "\n")
        for industry, count in sorted(industry_count.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(stock_industry_map) * 100
            f.write(f"{industry:30s}: {count:4d} 只 ({pct:5.1f}%)\n")
    print(f"✓ 统计报告: {report_file}")

    print("\n" + "=" * 60)
    print("申万2021二级行业映射文件保存完成！")
    print("=" * 60)

    return {
        'json': json_file,
        'python': py_file,
        'csv': csv_file,
        'simple': simple_map_file,
        'report': report_file,
    }


if __name__ == "__main__":
    # 生成二级行业映射
    stock_industry_map, industry_count = generate_l2_industry_mapping()

    # 保存文件
    files = save_l2_industry_mapping_files(stock_industry_map, industry_count)

    print("\n✅ 申万2021二级行业数据准备完成！")
    print(f"\n共 {len(industry_count)} 个二级行业，比一级行业（30个）细化了 {len(industry_count) / 30:.1f} 倍")
    print("\nRD-Agent 现在可以使用基于二级行业的因子:")
    print("  - 更精细的行业动量因子")
    print("  - 更准确的行业相对强弱因子")
    print("\n下次启动 RD-Agent 时将自动使用这些数据。")
