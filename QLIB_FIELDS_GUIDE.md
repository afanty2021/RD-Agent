# Qlib 字段说明与使用指南

> **重要更新**: 本文档基于Qlib源码分析完成，确认了`$amount`字段的可用性

## 📋 核心字段（可直接使用）

| 字段名 | 说明 | 数据类型 | 示例值 | 备注 |
|--------|------|----------|--------|------|
| `$open` | 开盘价 | float | 10.50 | 原始价格 |
| `$high` | 最高价 | float | 10.80 | 当日最高价 |
| `$low` | 最低价 | float | 10.30 | 当日最低价 |
| `$close` | 收盘价 | float | 10.65 | 当日收盘价 |
| `$volume` | 成交量 | float | 1000000 | 单位通常是"手"（100股） |
| **`$amount`** | **成交额** | float | 10500000 | **单位是千元（需×1000转换）** |
| `$vwap` | 成交量加权平均价 | float | 10.55 | 部分数据源提供 |
| `$factor` | 复权因子 | float | 1.234 | 用于复权计算 |

## 🔍 源码验证

### 1. $amount 字段确认

通过对 Qlib 源码的分析，确认 `$amount` 是标准字段：

**文件**: `/Users/berton/Github/qlib/qlib/contrib/data/tushare/field_mapping.py`
```python
# 第40行
"amount": "amount",  # 成交额（千元）

# 第73行 - 数值型字段列表
NUMERIC_FIELDS = {
    "volume", "amount", "adj_factor", ...
}

# 第91行 - 字段单位映射
FIELD_UNITS = {
    "volume": 100,    # 手转换为股
    "amount": 1000,   # 千元转换为元
    ...
}
```

### 2. 数据文件确认

```bash
$ ls ~/.qlib/qlib_data/cn_data/features/sz002790/
amount.day.bin       # 成交额数据文件存在！
close.day.bin
high.day.bin
low.day.bin
open.day.bin
volume.day.bin
...
```

### 3. API 实现分析

**LocalFeatureProvider.feature()** 方法 (`data.py:816`):
```python
def feature(self, instrument, field, start_index, end_index, freq):
    # validate
    field = str(field)[1:]  # 去掉$符号
    # $amount -> amount -> 读取 amount.day.bin
    return self.backend_obj(instrument=instrument, field=field, freq=freq)[...]
```

## ⚠️ 不存在的字段

以下字段在 Qlib 标准 API 中**不存在**，需要自己计算：

| 字段名 | 说明 | 计算方法 |
|--------|------|----------|
| `$turnover` | 换手率 | `$volume / float_shares * 100` |
| `$change` | 涨跌额 | `$close - $open` |
| `$pct_chg` | 涨跌幅 | `($close - $open) / $open` |

## 📝 正确的使用方式

### 方法1：直接使用 $amount（推荐）

```python
from qlib.data import D
import qlib

# 初始化
qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region='cn')

# 直接使用 $amount 字段
fields = ['$open', '$high', '$low', '$close', '$volume', '$amount']

df = D.features(
    instruments=instruments,
    fields=fields,
    start_time='2024-01-01',
    end_time='2024-12-31',
    freq='day'
)
df.columns = fields
df = df.reset_index()

# $amount 的单位是千元，需要转换为元
df['$amount_yuan'] = df['$amount'] * 1000
```

### 方法2：使用核心字段 + 自己计算

```python
from qlib.data import D

# 获取核心字段
fields = ['$open', '$high', '$low', '$close', '$volume']

df = D.features(instruments, fields, ...)
df.columns = fields
df = df.reset_index()

# 自己计算成交额（单位：元）
# 注意：$volume 单位是"手"（100股），需要乘以100
df['$amount_calculated'] = df['$close'] * df['$volume'] * 100
```

### 方法3：使用 D.instruments() 的正确方式

```python
from qlib.data import D

# D.instruments() 返回的是配置字典，不是股票列表
instruments = D.instruments(market='csi300')
# 返回: {'market': 'csi300', 'filter_pipe': []}

# D.features() 会自动根据配置过滤有效股票
df = D.features(
    instruments=instruments,  # 直接使用配置字典
    fields=fields,
    start_time='2024-01-01',
    end_time='2024-12-31',
    freq='day'
)

# 无需手动过滤股票，Qlib会自动处理
```

## 📊 成交量 vs 成交额

### 成交量（Volume）

```python
$volume  # 成交量，单位是"手"
# 1手 = 100股
# 例如：$volume = 10000 表示 10000手 = 1000000股
```

### 成交额（Amount）

```python
# 从 API 直接获取
$amount  # 成交额，单位是"千元"
# 需要乘以1000转换为元

# 示例：
# $close = 10.50元
# $volume = 10000手 = 1000000股
# $amount = 10.50 × 1000000 / 1000 = 10500千元 = 10500000元

# 自己计算（验证）
$amount_calculated = $close × $volume × 100  # 单位：元
$amount_from_api = $amount × 1000  # 单位：元
# 两者应该相等（可能有微小差异）
```

## 🔍 完整示例

```python
import qlib
from qlib.data import D
import pandas as pd

# 初始化 Qlib
qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region='cn')

# 获取 instruments 配置
instruments = D.instruments(market='csi300')
print(f"Instruments类型: {type(instruments)}")
# 输出: <class 'dict'>

# 定义完整字段（包括 $amount）
fields = ['$open', '$high', '$low', '$close', '$volume', '$amount']

# 获取数据
df = D.features(
    instruments=instruments,
    fields=fields,
    start_time='2024-01-01',
    end_time=None,  # None 表示使用最后交易日
    freq='day'
)
df.columns = fields
df = df.reset_index()

print(f"数据列: {df.columns.tolist()}")
print(f"股票数量: {df['instrument'].nunique()}")

# 检查 $amount 数据
print("\n$amount 统计:")
print(df['$amount'].describe())

# 验证计算
df['$amount_verify'] = df['$close'] * df['$volume'] * 100  # 单位：元
df['$diff'] = (df['$amount'] * 1000) - df['$amount_verify']
print(f"\n计算差异（应该接近0）: {df['$diff'].abs().max():.2f} 元")
```

## ⚠️ 常见错误

### 错误1：使用不存在的 $turnover 字段

```python
# ❌ 错误
fields = ['$open', '$high', '$low', '$close', '$volume', '$turnover']
df = D.features(instruments, fields, ...)
# 报错: Field $turnover not found

# ✓ 正确
fields = ['$open', '$high', '$low', '$close', '$volume', '$amount']
```

### 错误2：误解 D.instruments() 的返回值

```python
# ❌ 错误
instruments = D.instruments(market='csi300')
print(len(instruments))  # TypeError: object of type 'dict' has no len()

# ✓ 正确
instruments = D.instruments(market='csi300')
print(instruments)  # {'market': 'csi300', 'filter_pipe': []}
# 直接传递给 D.features()，它会自动处理股票过滤
```

### 错误3：忽略 $amount 的单位

```python
# ❌ 错误
amount_yuan = df['$amount']  # 这还是千元！

# ✓ 正确
amount_yuan = df['$amount'] * 1000  # 转换为元
```

### 错误4：手动过滤股票

```python
# ❌ 不必要
instruments = D.instruments(market='csi300')
# 手动读取 csi300.txt 文件过滤股票...

# ✓ 正确
instruments = D.instruments(market='csi300')
df = D.features(instruments=instruments, ...)
# Qlib 会自动根据日期范围过滤有效股票
```

## 📚 推荐字段组合

### 组合1：基本价格数据

```python
fields = ['$open', '$high', '$low', '$close', '$volume']
```

### 组合2：完整 OHLCVA

```python
fields = ['$open', '$high', '$low', '$close', '$volume', '$amount']
```

### 组合3：技术分析完整版

```python
fields = ['$open', '$high', '$low', '$close', '$volume', '$amount', '$vwap', '$factor']
```

## 🔗 参考链接

- [Qlib 官方文档 - 数据 API](https://qlib.readthedocs.io/en/latest/component/data.html)
- [Qlib 源码 - data.py](https://github.com/microsoft/qlib/blob/main/qlib/data/data.py)
- [Qlib 源码 - field_mapping.py](https://github.com/microsoft/qlib/blob/main/qlib/contrib/data/tushare/field_mapping.py)

## 📝 版本说明

- **Qlib 版本**: 基于最新源码分析
- **更新日期**: 2025-12-30
- **验证方法**: 源码分析 + 数据文件验证
