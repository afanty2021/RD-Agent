# 通达信（TDX）公式转 Qlib 因子完整指南

## 📚 目录
1. [概述](#概述)
2. [语法对比](#语法对比)
3. [常见指标转换示例](#常见指标转换示例)
4. [方法一：使用 Qlib 表达式](#方法一使用-qlib-表达式)
5. [方法二：使用 Python 代码](#方法二使用-python-代码)
6. [方法三：在 RD-Agent 中使用](#方法三在-rd-agent-中使用)
7. [实战案例](#实战案例)
8. [常见问题](#常见问题)

---

## 概述

### 通达信公式简介

通达信（TDX）是中国流行的股票分析软件，拥有丰富的技术指标公式语言。常见公式包括：
- MACD、KDJ、RSI、BOLL 等经典指标
- 自定义技术指标
- 选股公式
- 交易系统公式

### Qlib 因子简介

Qlib 是微软开源的量化投资平台，支持：
- 表达式引擎（类似 SQL 的表达式语言）
- Python 自定义因子
- 因子回测和评估
- 与 RD-Agent 集成

### 转换目标

将通达信公式转换为 Qlib 可用的因子，用于：
1. 量化回测
2. 因子研究
3. 机器学习特征
4. RD-Agent 自动因子生成

---

## 语法对比

### 基础数据字段映射

| 通达信 | Qlib 表达式 | 说明 |
|--------|------------|------|
| `CLOSE` 或 `C` | `$close` | 收盘价 |
| `OPEN` 或 `O` | `$open` | 开盘价 |
| `HIGH` 或 `H` | `$high` | 最高价 |
| `LOW` 或 `L` | `$low` | 最低价 |
| `VOL` 或 `V` | `$volume` | 成交量 |
| `AMOUNT` | `$money` | 成交额 |

### 时间序列函数映射

| 通达信 | Qlib 表达式 | 说明 |
|--------|------------|------|
| `REF(X, N)` | `Ref(X, N)` | N周期前的值 |
| `MA(X, N)` | `Mean(X, N)` | N日简单移动平均 |
| `EMA(X, N)` | `EMA(X, N)` | N日指数移动平均 |
| `SMA(X, N, M)` | 不支持 | 需用 Python 实现 |
| `MAX(X, N)` | `Max(X, N)` | N日内最大值 |
| `MIN(X, N)` | `Min(X, N)` | N日内最小值 |
| `HHV(X, N)` | `Max(X, N)` | N日内最高值 |
| `LLV(X, N)` | `Min(X, N)` | N日内最低值 |
| `STD(X, N)` | `Std(X, N)` | N日标准差 |
| `SUM(X, N)` | `Sum(X, N)` | N日累加 |
| `ABS(X)` | `Abs(X)` | 绝对值 |
| `CROSS(A, B)` | 需用 Python 实现 | 金叉（A上穿B）|
| `BARSLAST(X)` | 需用 Python 实现 | 上次条件成立距今天数 |

### 数学函数映射

| 通达信 | Qlib 表达式 | 说明 |
|--------|------------|------|
| `SQRT(X)` | `Sqrt(X)` | 平方根 |
| `LN(X)` | `Log(X)` | 自然对数 |
| `EXP(X)` | `Exp(X)` | 指数 |
| `POWER(X, N)` | `Pow(X, N)` | X的N次方 |
| `IF(COND, A, B)` | `If(Cond, A, B)` | 条件函数 |

---

## 常见指标转换示例

### 1. MACD 指标

#### 通达信公式
```
DIF:EMA(CLOSE,12)-EMA(CLOSE,26);
DEA:EMA(DIF,9);
MACD:(DIF-DEA)*2,COLORSTICK;
```

#### Qlib 表达式方式
```python
# 方法1: 使用表达式
features = [
    "DIF = EMA($close, 12) - EMA($close, 26)",
    "DEA = EMA(DIF, 9)",
    "MACD = (DIF - DEA) * 2"
]
```

#### Python 代码方式
```python
import pandas as pd
import numpy as np

def calculate_MACD(df, short=12, long=26, signal=9):
    """
    计算 MACD 指标
    df: 包含 $close 列的 DataFrame
    """
    # 计算 DIF
    ema_short = df['$close'].ewm(span=short, adjust=False).mean()
    ema_long = df['$close'].ewm(span=long, adjust=False).mean()
    dif = ema_short - ema_long

    # 计算 DEA (信号线)
    dea = dif.ewm(span=signal, adjust=False).mean()

    # 计算 MACD 柱状图
    macd = (dif - dea) * 2

    return macd
```

---

### 2. KDJ 指标

#### 通达信公式
```
RSV:(CLOSE-LLV(LOW,9))/(HHV(HIGH,9)-LLV(LOW,9))*100;
K:SMA(RSV,3,1);
D:SMA(K,3,1);
J:3*K-2*D;
```

#### Qlib 表达式方式
```python
# KDJ 的 RSV 部分
RSV = ($close - Min($low, 9)) / (Max($high, 9) - Min($low, 9)) * 100

# SMA 需要用 Python 实现（Qlib 表达式不直接支持 SMA）
# 参考 Python 实现方式
```

#### Python 代码方式
```python
def calculate_KDJ(df, n=9, m1=3, m2=3):
    """
    计算 KDJ 指标
    """
    # 计算 RSV
    low_min = df['$low'].rolling(window=n).min()
    high_max = df['$high'].rolling(window=n).max()
    rsv = (df['$close'] - low_min) / (high_max - low_min) * 100

    # 计算 K (SMA)
    k = rsv.ewm(alpha=1/m1, adjust=False).mean()

    # 计算 D
    d = k.ewm(alpha=1/m2, adjust=False).mean()

    # 计算 J
    j = 3 * k - 2 * d

    return k, d, j
```

---

### 3. RSI 指标

#### 通达信公式
```
LC:=REF(CLOSE,1);
RSI:SMA(MAX(CLOSE-LC,0),6,1)/SMA(ABS(CLOSE-LC),6,1)*100;
```

#### Qlib 表达式方式
```python
# RSI 需要自定义，Qlib 表达式不直接支持
# 使用 Python 实现
```

#### Python 代码方式
```python
def calculate_RSI(df, period=6):
    """
    计算 RSI 指标
    """
    # 计算价格变化
    delta = df['$close'].diff()

    # 分离涨跌
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    # 计算平均涨跌幅
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    # 计算 RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi
```

---

### 4. BOLL 布林带

#### 通达信公式
```
MID:MA(CLOSE,20);
UPPER:MID+2*STD(CLOSE,20);
LOWER:MID-2*STD(CLOSE,20);
```

#### Qlib 表达式方式
```python
features = [
    "MID = Mean($close, 20)",
    "UPPER = MID + 2 * Std($close, 20)",
    "LOWER = MID - 2 * Std($close, 20)"
]
```

#### Python 代码方式
```python
def calculate_BOLL(df, n=20, k=2):
    """
    计算布林带
    """
    mid = df['$close'].rolling(window=n).mean()
    std = df['$close'].rolling(window=n).std()

    upper = mid + k * std
    lower = mid - k * std

    return upper, mid, lower
```

---

### 5. 均线系统

#### 通达信公式
```
MA5:MA(CLOSE,5);
MA10:MA(CLOSE,10);
MA20:MA(CLOSE,20);
MA60:MA(CLOSE,60);
```

#### Qlib 表达式方式
```python
features = [
    "MA5 = Mean($close, 5)",
    "MA10 = Mean($close, 10)",
    "MA20 = Mean($close, 20)",
    "MA60 = Mean($close, 60)"
]
```

#### Python 代码方式
```python
def calculate_MA(df, periods=[5, 10, 20, 60]):
    """
    计算移动平均线
    """
    mas = {}
    for period in periods:
        mas[f'MA{period}'] = df['$close'].rolling(window=period).mean()
    return mas
```

---

## 方法一：使用 Qlib 表达式

### 基本语法

```python
from qlib.expression import expression

# 定义因子表达式
features = [
    "$close",  # 收盘价
    "$volume",  # 成交量
    "Ref($close, 1)",  # 昨收盘价
    "Mean($close, 5)",  # 5日均线的因子计算
]
```

### 复杂表达式示例

```python
# 动量因子
momentum = "Ref($close, 5) / $close - 1"

# 波动率因子
volatility = "Std($close / Ref($close, 1) - 1, 20)"

# 成交量变化率
volume_change = "$volume / Mean($volume, 20) - 1"

# 价格位置
price_position = "($close - Min($low, 20)) / (Max($high, 20) - Min($low, 20))"
```

### 在数据加载中使用

```python
from qlib.data.dataset import DatasetH
from qlib.data.dataset.loader import Alpha158DL

# 使用自定义表达式
loader = Alpha158DL(
    config={
        "label": ["Ref($close, -2) / Ref($close, 1) - 1"],
        "feature": [
            "Ref($close, 5) / $close - 1",  # 5日动量
            "Std($close, 20) / $close",      # 20日波动率
            "$volume / Mean($volume, 20)",   # 成交量比率
            "($close - Ref($close, 1)) / Ref($close, 1)",  # 日收益率
        ]
    }
)
```

---

## 方法二：使用 Python 代码

### 标准模板

```python
import pandas as pd
import numpy as np

def calculate_TDX_FACTOR_NAME():
    """计算通达信因子"""
    # 加载数据
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()
    df_reset = df_reset.rename(columns={'date': 'datetime'})

    # 【在此处添加您的因子计算逻辑】
    # 示例：5日动量
    df_reset['FACTOR_NAME'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(5)
    )

    # 恢复 MultiIndex
    result = df_reset.set_index(['datetime', 'instrument'])[['FACTOR_NAME']]
    result.to_hdf('result.h5', key='data')

if __name__ == '__main__':
    calculate_TDX_FACTOR_NAME()
```

### 完整示例：转换通达信 MACD

```python
import pandas as pd
import numpy as np

def calculate_TDX_MACD():
    """通达信 MACD 指标转换"""
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()
    df_reset = df_reset.rename(columns={'date': 'datetime'})

    # 计算每个股票的 MACD
    def calc_macd(group):
        close = group['$close']

        # EMA(CLOSE, 12) 和 EMA(CLOSE, 26)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()

        # DIF = EMA12 - EMA26
        dif = ema12 - ema26

        # DEA = EMA(DIF, 9)
        dea = dif.ewm(span=9, adjust=False).mean()

        # MACD = (DIF - DEA) * 2
        macd = (dif - dea) * 2

        return macd

    df_reset['MACD'] = df_reset.groupby('instrument', group_keys=False).apply(calc_macd)

    # 恢复 MultiIndex
    result = df_reset.set_index(['datetime', 'instrument'])[['MACD']]
    result.to_hdf('result.h5', key='data')

if __name__ == '__main__':
    calculate_TDX_MACD()
```

---

## 方法三：在 RD-Agent 中使用

### 方式 1：作为自定义因子库

创建自定义因子文件：

```python
# tdx_factors.py
from typing import List
from qlib.expression import expression

class TDXFactors:
    """通达信常用因子库"""

    @staticmethod
    def get_macd_features() -> List[str]:
        """MACD 相关因子"""
        return [
            "EMA12 = EMA($close, 12)",
            "EMA26 = EMA($close, 26)",
            "DIF = EMA12 - EMA26",
            "DEA = EMA(DIF, 9)",
            "MACD = (DIF - DEA) * 2",
        ]

    @staticmethod
    def get_kdj_features() -> List[str]:
        """KDJ 相关因子"""
        return [
            "LOW_MIN = Min($low, 9)",
            "HIGH_MAX = Max($high, 9)",
            "RSV = ($close - LOW_MIN) / (HIGH_MAX - LOW_MIN) * 100",
        ]

    @staticmethod
    def get_ma_features() -> List[str]:
        """均线系统因子"""
        return [
            "MA5 = Mean($close, 5)",
            "MA10 = Mean($close, 10)",
            "MA20 = Mean($close, 20)",
            "MA60 = Mean($close, 60)",
            "MA_TREND = (MA5 - MA20) / MA20",  # 均线趋势
        ]
```

在 RD-Agent 中使用：

```python
# 在实验配置中导入
from tdx_factors import TDXFactors

# 使用通达信因子
features = TDXFactors.get_macd_features() + TDXFactors.get_ma_features()
```

### 方式 2：作为提示词模板

编辑 `rdagent/components/coder/factor_coder/prompts.yaml`，添加通达信公式示例：

```yaml
evolving_strategy_factor_implementation_v1_system: |-
  ...
  EXAMPLE 5 - TDX MACD Factor:
  ```python
  def calculate_MACD():
      import pandas as pd
      import numpy as np

      df = pd.read_hdf('daily_pv.h5', key='data')
      df_reset = df.reset_index()

      # 通达信公式:
      # DIF:EMA(CLOSE,12)-EMA(CLOSE,26);
      # DEA:EMA(DIF,9);
      # MACD:(DIF-DEA)*2;

      close = df_reset['$close']
      ema12 = close.ewm(span=12).mean()
      ema26 = close.ewm(span=26).mean()
      dif = ema12 - ema26
      dea = dif.ewm(span=9).mean()
      df_reset['MACD'] = (dif - dea) * 2

      result = df_reset.set_index(['datetime', 'instrument'])[['MACD']]
      result.to_hdf('result.h5', key='data')
  ```
```

---

## 实战案例

### 案例 1：转换通达信选股公式

#### 通达信公式
```
XG:RSI>80 AND K>D AND MACD>0;
```
（选出 RSI > 80 且 K > D 且 MACD > 0 的股票）

#### Qlib 实现方式 1：使用因子筛选

```python
import pandas as pd
import numpy as np

def tdx_stock_selection(df):
    """
    实现通达信选股公式
    """
    # 计算 RSI(6)
    delta = df['$close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(6).mean()
    avg_loss = loss.rolling(6).mean()
    rsi = 100 - (100 / (1 + avg_gain / avg_loss))

    # 计算 KDJ
    low_min = df['$low'].rolling(9).min()
    high_max = df['$high'].rolling(9).max()
    rsv = (df['$close'] - low_min) / (high_max - low_min) * 100
    k = rsv.ewm(alpha=1/3).mean()
    d = k.ewm(alpha=1/3).mean()

    # 计算 MACD
    ema12 = df['$close'].ewm(12).mean()
    ema26 = df['$close'].ewm(26).mean()
    dif = ema12 - ema26
    dea = dif.ewm(9).mean()
    macd = dif - dea

    # 选股条件
    selected = (rsi > 80) & (k > d) & (macd > 0)

    return selected
```

#### Qlib 实现方式 2：使用因子组合

```python
from qlib.contrib.strategy.signal_strategy import TopkDropoutStrategy

# 构建组合因子信号
signal = (
    (rsi > 80).astype(int) +  # RSI > 80
    (k > d).astype(int) +      # K > D
    (macd > 0).astype(int)      # MACD > 0
)

# 选择满足所有条件的股票
strategy = TopkDropoutStrategy(
    signal=signal,
    topk=50,  # 选择前50只
    n_drop=5
)
```

---

### 案例 2：转换通达信交易系统

#### 通达信交易系统公式
```
{多头买入}
LONG:CROSS(MA(CLOSE,5),MA(CLOSE,20));  {5日均线上穿20日均线}

{多头卖出}
SHORT:CROSS(MA(CLOSE,20),MA(CLOSE,5));  {5日均线下穿20日均线}
```

#### Qlib 实现方式

```python
import pandas as pd
import numpy as np

def calculate_MA_CROSS_Signal():
    """计算均线交叉信号"""
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    def calc_signal(group):
        ma5 = group['$close'].rolling(5).mean()
        ma20 = group['$close'].rolling(20).mean()

        # 金叉：MA5 上穿 MA20
        # 逻辑：昨天 MA5 <= MA20，今天 MA5 > MA20
        golden_cross = (ma5 > ma20) & (ma5.shift(1) <= ma20.shift(1))

        # 死叉：MA5 下穿 MA20
        death_cross = (ma5 < ma20) & (ma5.shift(1) >= ma20.shift(1))

        # 信号：1=买入，-1=卖出，0=持有
        signal = pd.Series(0, index=group.index)
        signal[golden_cross] = 1
        signal[death_cross] = -1

        return signal

    df_reset['SIGNAL'] = df_reset.groupby('instrument', group_keys=False).apply(calc_signal)

    result = df_reset.set_index(['datetime', 'instrument'])[['SIGNAL']]
    result.to_hdf('result.h5', key='data')
```

---

### 案例 3：高级因子 - 量价配合

#### 通达信公式
```
OBV:SUM(IF(CLOSE>REF(CLOSE,1),VOL,IF(CLOSE<REF(CLOSE,1),-VOL,0)),0);
VOL_OBV_RATIO:OBV/MA(OBV,20);
```
（OBV 能量潮指标及其20日均线比率）

#### Qlib 实现

```python
def calculate_OBV():
    """计算 OBV 能量潮指标"""
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()

    def calc_obv(group):
        price_change = group['$close'].diff()

        # 计算每日 OBV 变化
        obv_change = group['$volume'].copy()
        obv_change[price_change > 0] = group['$volume'][price_change > 0]   # 上涨：+成交量
        obv_change[price_change < 0] = -group['$volume'][price_change < 0] # 下跌：-成交量
        obv_change[price_change == 0] = 0  # 平盘：0

        # 累计 OBV
        obv = obv_change.cumsum()

        # OBV 20日均线
        obv_ma = obv.rolling(20).mean()

        # OBV 比率
        obv_ratio = obv / obv_ma

        return obv_ratio

    df_reset['VOL_OBV_RATIO'] = df_reset.groupby('instrument', group_keys=False).apply(calc_obv)

    result = df_reset.set_index(['datetime', 'instrument'])[['VOL_OBV_RATIO']]
    result.to_hdf('result.h5', key='data')
```

---

## 常见问题

### Q1：通达信的 `SMA(X, N, M)` 如何实现？

**通达信 SMA**：
```
SMA(X, N, M) = (M*X + (N-M)*SMA(REF, 1)) / N
```

**Python 实现**：
```python
def sma(series, n, m):
    """
    通达信 SMA 函数
    series: 数据序列
    n: 总周期
    m: 权重
    """
    result = [np.nan] * len(series)
    alpha = m / n

    for i in range(1, len(series)):
        if np.isnan(result[i-1]):
            result[i] = series[i]
        else:
            result[i] = (alpha * series[i] + (1 - alpha) * result[i-1])

    return pd.Series(result, index=series.index)
```

### Q2：通达信的 `CROSS(A, B)` 如何实现？

**通达信 CROSS**：A 上穿 B（昨天 A<=B，今天 A>B）

**Python 实现**：
```python
def cross(series_a, series_b):
    """金叉"""
    return (series_a > series_b) & (series_a.shift(1) <= series_b.shift(1))

def cross_reverse(series_a, series_b):
    """死叉（A 下穿 B）"""
    return (series_a < series_b) & (series_a.shift(1) >= series_b.shift(1))
```

### Q3：如何在 RD-Agent 中使用这些因子？

**方法 1**：修改提示词，添加通达信公式示例

```yaml
# prompts.yaml
EXAMPLE 6 - TDX Style Factor:
"""
通达信公式：
  RSI6: SMA(MAX(CLOSE-LC,0),6,1)/SMA(ABS(CLOSE-LC),6,1)*100;

Python 实现：
```python
def calculate_RSI6():
    delta = df['$close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(6).mean()
    avg_loss = loss.rolling(6).mean()
    rsi = 100 - (100 / (1 + avg_gain / avg_loss))
    return rsi
```
"""
```

**方法 2**：直接在实验中手动编写因子代码

```bash
# 创建自定义因子
python rdagent/app/qlib_rd_loop/factor.py

# 在生成因子时，RD-Agent 会根据您的提示词生成代码
# 在提示词中明确指定使用通达信公式的转换
```

### Q4：如何批量转换多个通达信公式？

创建批量转换脚本：

```python
# tdx_batch_converter.py

tdx_formulas = {
    "MA5": "MA(CLOSE,5)",
    "MA10": "MA(CLOSE,10)",
    "RSI6": "SMA(MAX(CLOSE-LC,0),6,1)/SMA(ABS(CLOSE-LC),6,1)*100",
    "KDJ_K": "SMA((CLOSE-LLV(LOW,9))/(HHV(HIGH,9)-LLV(LOW,9))*100,3,1)",
    # 添加更多公式...
}

def convert_tdx_to_python(formula_name, formula):
    """将通达信公式转换为 Python 代码"""
    # 实现转换逻辑
    pass

# 批量转换
for name, formula in tdx_formulas.items():
    python_code = convert_tdx_to_python(name, formula)
    with open(f"{name}.py", 'w') as f:
        f.write(python_code)
```

---

## 转换速查表

| 通达信函数 | Python/Qlib 实现 |
|-----------|-----------------|
| `MA(X, N)` | `X.rolling(N).mean()` 或 `Mean(X, N)` |
| `EMA(X, N)` | `X.ewm(span=N).mean()` 或 `EMA(X, N)` |
| `REF(X, N)` | `X.shift(N)` 或 `Ref(X, N)` |
| `MAX/MIN(X, N)` | `X.rolling(N).max()/min()` |
| `STD(X, N)` | `X.rolling(N).std()` 或 `Std(X, N)` |
| `SUM(X, N)` | `X.rolling(N).sum()` 或 `Sum(X, N)` |
| `ABS(X)` | `abs(X)` 或 `Abs(X)` |
| `CROSS(A,B)` | `(A>B) & (A.shift(1)<=B.shift(1))` |
| `BARSLAST(X)` | 手动实现累计 |
| `SMA(X,N,M)` | 手动实现加权平均 |

---

## 总结

### 转换流程

1. **理解通达信公式**：分析公式逻辑和参数
2. **选择实现方式**：
   - 简单公式 → Qlib 表达式
   - 复杂公式 → Python 代码
3. **编写转换代码**：参考本文示例
4. **验证结果**：对比通达信和 Qlib 输出
5. **集成到 RD-Agent**：通过提示词或自定义因子

### 推荐工具

1. **Qlib 官方文档**：https://qlib.readthedocs.io/
2. **通达信公式编辑器**：测试公式逻辑
3. **Jupyter Notebook**：验证转换结果
4. **RD-Agent 提示词**：让 AI 自动生成代码

### 快速开始

```bash
# 1. 准备通达信公式
tdx_formula = "MA(CLOSE,5)"

# 2. 转换为 Python
python_code = f"""
df['MA5'] = df['$close'].rolling(5).mean()
"""

# 3. 在 RD-Agent 中使用
python rdagent/app/qlib_rd_loop/factor.py --loop_n 10

# 4. 在提示词中提供公式和转换示例
```

---

## 附录：完整的转换示例库

完整的通达信公式到 Qlib 转换示例库：
```bash
# 查看完整示例
cat /Users/berton/Github/RD-Agent/TDX_TO_QLIB_EXAMPLES.md
```

祝您转换顺利！🚀
