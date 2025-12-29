# 在 RD-Agent 中使用行业板块数据指南

## 概述

本指南说明如何在 RD-Agent 因子开发训练中使用 ~/.qlib 目录下的行业板块数据。

## 数据位置

```
~/.qlib/qlib_data/cn_data/industry_data/
├── industry_SW2021_L1_*.csv     # 申万2021一级行业（约30个行业）
├── industry_SW2021_L2_*.csv     # 申万2021二级行业（约100个行业）
├── industry_SW2021_L3_*.csv     # 申万2021三级行业（约300个行业）
├── industry_CITIC_L1_*.csv      # 中信一级行业
├── industry_CITIC_L2_*.csv      # 中信二级行业
├── industry_CITIC_L3_*.csv      # 中信三级行业
├── industry_ZJH_L1_*.csv        # 证监会一级行业
├── industry_ZJH_L2_*.csv        # 证监会二级行业
├── industry_ZJH_L3_*.csv        # 证监会三级行业
├── industry__latest.csv         # 最新行业数据
└── industry__latest.json        # 最新行业数据（JSON格式）
```

## 快速开始

### 步骤1：获取股票-行业映射

```bash
# 使用示例数据（包含常见股票的手动映射）
python scripts/get_stock_industry_mapping.py --source sample --save

# 或使用 AKShare（无需 API token，需要安装 akshare）
pip install akshare
python scripts/get_stock_industry_mapping.py --source akshare --save

# 或使用 Tushare（需要 API token）
pip install tushare
python scripts/get_stock_industry_mapping.py --source tushare --token YOUR_TOKEN --save
```

生成的文件保存在 `data/industry_mapping/` 目录：
- `stock_industry_mapping.json` - JSON 格式
- `stock_industry_mapping.csv` - CSV 格式
- `stock_industry_mapping.py` - Python 模块

### 步骤2：查看行业因子示例

```bash
# 查看内置的行业因子示例
python scripts/generate_industry_factor_data.py --action examples
```

### 步骤3：运行 RD-Agent 因子开发

RD-Agent 的提示词已经更新，现在包含了行业数据的使用说明和示例。RD-Agent 会自动生成包含行业因素的因子。

```bash
# 启动因子开发循环
python -m rdagent.app.qlib_rd_loop.factor --loop_n 30
```

## 已集成的功能

### 1. 提示词增强

在 `rdagent/components/coder/factor_coder/prompts.yaml` 中添加了：

- **示例4：行业动量因子**
  - 计算行业内所有股票的平均收益率
  - 捕捉整个行业的趋势

- **示例5：行业相对强弱因子**
  - 计算股票相对所属行业的表现
  - 识别行业内表现优异的股票

- **行业数据说明**
  - 数据位置和格式
  - 可用的分类体系

### 2. 辅助脚本

#### generate_industry_factor_data.py

```bash
# 生成包含行业信息的数据文件
python scripts/generate_industry_factor_data.py --action generate

# 创建行业查找表
python scripts/generate_industry_factor_data.py --action lookup

# 显示行业因子示例
python scripts/generate_industry_factor_data.py --action examples
```

#### get_stock_industry_mapping.py

```bash
# 从不同数据源获取股票-行业映射
python scripts/get_stock_industry_mapping.py --source [sample|akshare|tushare] --save
```

## 行业因子类型

### 1. 行业动量因子

**原理**：特定行业的平均收益率

**公式**：
```python
Industry_Momentum = mean(stock_returns_in_industry)
```

**用途**：
- 捕捉行业轮动机会
- 识别热门行业
- 行业配置策略

### 2. 行业相对强弱因子

**原理**：股票相对所属行业的超额收益

**公式**：
```python
Relative_Strength = stock_return - industry_average_return
```

**用途**：
- 识别行业内强势股票
- 选股时考虑行业因素
- 构建行业中性组合

### 3. 行业集中度因子

**原理**：投资组合在特定行业的暴露程度

**公式**：
```python
Industry_Concentration = sum(abs(weight_in_industry))
```

**用途**：
- 风险管理
- 行业分散度控制

### 4. 跨行业动量因子

**原理**：不同行业间的相对表现

**公式**：
```python
Cross_Industry_Momentum = industry_A_return - industry_B_return
```

**用途**：
- 行业轮动策略
- 配对交易

## 在因子代码中使用行业数据

### 方式1：使用内置映射表

```python
def calculate_Industry_Factor():
    import pandas as pd
    import numpy as np
    from data.industry_mapping.stock_industry_mapping import STOCK_INDUSTRY_MAPPING

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 使用预加载的映射表
    df_reset['industry'] = df_reset['instrument'].map(
        lambda x: STOCK_INDUSTRY_MAPPING.get(x, {}).get('SW2021_L1_name', '未知')
    )

    # 计算因子...
    result = df_reset.set_index(['datetime', 'instrument'])[['FactorName']]
    result.to_hdf('result.h5', key='data')
```

### 方式2：运行时加载映射

```python
def calculate_Industry_Factor():
    import pandas as pd
    import numpy as np
    import json

    # 加载映射表
    with open('data/industry_mapping/stock_industry_mapping.json', 'r') as f:
        mapping = json.load(f)

    # 简化映射
    industry_map = {k: v.get('SW2021_L1_name', '未知') for k, v in mapping.items()}

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()
    df_reset['industry'] = df_reset['instrument'].map(industry_map)

    # 计算因子...
```

### 方式3：手动定义映射

```python
def calculate_Industry_Factor():
    import pandas as pd
    import numpy as np

    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    # 手动定义关键股票的行业
    industry_map = {
        'SH600000': '银行',
        'SH600519': '食品饮料',
        # ... 添加更多映射
    }
    df_reset['industry'] = df_reset['instrument'].map(industry_map)

    # 计算因子...
```

## 申万一级行业分类列表

| 代码 | 行业名称 | 英文名称 |
|------|---------|----------|
| 210000 | 银行 | Banking |
| 220000 | 食品饮料 | Food & Beverage |
| 230000 | 医药生物 | Healthcare |
| 240000 | 房地产 | Real Estate |
| 250000 | 汽车 | Automobile |
| 260000 | 电子 | Electronics |
| 270000 | 计算机 | Computer |
| 280000 | 传媒 | Media |
| 290000 | 通信 | Telecommunication |
| 300000 | 电气设备 | Electrical Equipment |
| ... | ... | ... |

## 最佳实践

### 1. 数据准备

- **完整的映射表**：确保所有股票都有行业分类
- **定期更新**：行业分类可能变化，定期更新映射表
- **多级别使用**：根据需要选择 L1/L2/L3 级别

### 2. 因子开发

- **行业中性化**：减去行业均值以避免行业偏差
- **分组计算**：使用 `groupby('industry')` 进行行业内计算
- **动态行业**：考虑行业分类随时间的变化

### 3. 风险控制

- **行业暴露控制**：限制单一行业的最大权重
- **行业分散度**：确保组合在多个行业分散
- **行业风格**：考虑行业风格因子（价值、成长等）

## 故障排除

### 问题1：股票没有行业映射

**解决方案**：
```python
# 检查未映射的股票
unmapped = df_reset[~df_reset['instrument'].isin(industry_map.keys())]
print(f"未映射的股票数量: {len(unmapped)}")

# 设置默认行业
df_reset['industry'] = df_reset['instrument'].map(industry_map).fillna('其他')
```

### 问题2：行业数据文件不存在

**解决方案**：
```bash
# 检查数据文件
ls -la ~/.qlib/qlib_data/cn_data/industry_data/

# 如果不存在，从原始数据生成
python scripts/generate_industry_factor_data.py --action lookup
```

### 问题3：因子代码生成错误

**解决方案**：
- 确保使用 `reset_index()` 后再进行 `groupby` 操作
- 检查行业映射是否正确加载
- 验证数据列名是否正确

## 进阶用法

### 1. 动态行业权重

```python
# 计算行业的市值权重
industry_market_cap = df_reset.groupby(['datetime', 'industry'])['market_cap'].sum()
industry_market_cap = industry_market_cap.groupby(level=0).apply(lambda x: x / x.sum())
```

### 2. 行业因子回归

```python
# 计算行业纯因子
from sklearn.linear_model import LinearRegression

# 对每个时点进行行业回归
for date in df_reset['datetime'].unique():
    df_date = df_reset[df_reset['datetime'] == date]

    # 创建行业哑变量
    industry_dummies = pd.get_dummies(df_date['industry'])

    # 回归得到行业因子
    model = LinearRegression()
    model.fit(industry_dummies, df_date['return'])
```

### 3. 行业动量策略

```python
# 计算行业动量排序
industry_momentum = df_reset.groupby(['datetime', 'industry'])['return'].mean().reset_index()
industry_momentum['rank'] = industry_momentum.groupby('datetime')['return'].rank(ascending=False)

# 选择排名前N的行业
top_industries = industry_momentum[industry_momentum['rank'] <= 5]
```

## 参考资料

- [Qlib 文档](https://qlib.readthedocs.io/)
- [申万行业分类标准](https://www.swindex.com.cn/)
- [RD-Agent 文档](https://github.com/microsoft/RD-Agent)

## 变更记录

- 2025-12-29: 初始版本，添加行业数据集成支持
- 集成了申万2021、中信、证监会行业分类
- 添加了行业动量和相对强弱因子示例
