#!/usr/bin/env python3
"""
通达信公式转换为 RD-Agent 因子的实战示例

本脚本演示如何将通达信（TDX）技术指标公式转换为可在 RD-Agent 中使用的因子代码。
"""

import pandas as pd
import numpy as np

# ============================================================================
# 示例 1：MACD 指标（最常用的趋势指标）
# ============================================================================

def tdx_macd_to_qlib():
    """
    通达信公式:
        DIF:EMA(CLOSE,12)-EMA(CLOSE,26);
        DEA:EMA(DIF,9);
        MACD:(DIF-DEA)*2,COLORSTICK;

    Qlib 因子实现:
    """
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()
    df_reset = df_reset.rename(columns={'date': 'datetime'})

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

    result = df_reset.set_index(['datetime', 'instrument'])[['MACD']]
    result.to_hdf('result.h5', key='data')


# ============================================================================
# 示例 2：KDJ 指标（超买超卖指标）
# ============================================================================

def tdx_kdj_to_qlib():
    """
    通达信公式:
        RSV:(CLOSE-LLV(LOW,9))/(HHV(HIGH,9)-LLV(LOW,9))*100;
        K:SMA(RSV,3,1);
        D:SMA(K,3,1);
        J:3*K-2*D;

    Qlib 因子实现:
    """
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()
    df_reset = df_reset.rename(columns={'date': 'datetime'})

    def calc_kdj(group):
        high = group['$high']
        low = group['$low']
        close = group['$close']

        # RSV 计算
        low_min = low.rolling(window=9).min()
        high_max = high.rolling(window=9).max()
        rsv = (close - low_min) / (high_max - low_min) * 100

        # K = SMA(RSV, 3, 1) - 即 EMA(RSV, 3)
        k = rsv.ewm(alpha=1/3, adjust=False).mean()

        # D = SMA(K, 3, 1)
        d = k.ewm(alpha=1/3, adjust=False).mean()

        # J = 3*K - 2*D
        j = 3 * k - 2 * d

        return k, d, j

    result = df_reset.groupby('instrument').apply(calc_kdj)
    df_reset['KDJ_K'] = result.map(lambda x: x[0])
    df_reset['KDJ_D'] = result.map(lambda x: x[1])
    df_reset['KDJ_J'] = result.map(lambda x: x[2])

    output = df_reset.set_index(['datetime', 'instrument'])[['KDJ_K', 'KDJ_D', 'KDJ_J']]
    output.to_hdf('result.h5', key='data')


# ============================================================================
# 示例 3：RSI 指标（相对强弱指标）
# ============================================================================

def tdx_rsi_to_qlib():
    """
    通达信公式:
        LC:=REF(CLOSE,1);
        RSI:SMA(MAX(CLOSE-LC,0),6,1)/SMA(ABS(CLOSE-LC),6,1)*100;

    Qlib 因子实现:
    """
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()
    df_reset = df_reset.rename(columns={'date': 'datetime'})

    def calc_rsi(group):
        close = group['$close']

        # LC := REF(CLOSE, 1)
        lc = close.shift(1)

        # CLOSE - LC
        change = close - lc

        # MAX(CLOSE-LC, 0) - 上涨时的幅度
        gain = change.where(change > 0, 0)

        # ABS(CLOSE-LC) - 绝对变化
        abs_change = change.abs()

        # SMA(MAX(CLOSE-LC,0), 6, 1) - 即 EMA(gain, 6)
        avg_gain = gain.ewm(alpha=1/6, adjust=False).mean()

        # SMA(ABS(CLOSE-LC), 6, 1) - 即 EMA(abs_change, 6)
        avg_abs_change = abs_change.ewm(alpha=1/6, adjust=False).mean()

        # RSI
        rsi = avg_gain / avg_abs_change * 100

        return rsi

    df_reset['RSI6'] = df_reset.groupby('instrument', group_keys=False).apply(calc_rsi)

    result = df_reset.set_index(['datetime', 'instrument'])[['RSI6']]
    result.to_hdf('result.h5', key='data')


# ============================================================================
# 示例 4：布林带 BOLL（波动率指标）
# ============================================================================

def tdx_boll_to_qlib():
    """
    通达信公式:
        MID:MA(CLOSE,20);
        UPPER:MID+2*STD(CLOSE,20);
        LOWER:MID-2*STD(CLOSE,20);

    Qlib 因子实现:
    """
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()
    df_reset = df_reset.rename(columns={'date': 'datetime'})

    def calc_boll(group):
        close = group['$close']

        # MID = MA(CLOSE, 20)
        mid = close.rolling(window=20).mean()

        # STD(CLOSE, 20)
        std = close.rolling(window=20).std()

        # UPPER = MID + 2*STD
        upper = mid + 2 * std

        # LOWER = MID - 2*STD
        lower = mid - 2 * std

        # 布林带宽度（用于衡量波动率）
        boll_width = (upper - lower) / mid

        # 价格在布林带中的位置
        boll_position = (close - lower) / (upper - lower)

        return boll_position

    df_reset['BOLL_POSITION'] = df_reset.groupby('instrument', group_keys=False).apply(calc_boll)

    result = df_reset.set_index(['datetime', 'instrument'])[['BOLL_POSITION']]
    result.to_hdf('result.h5', key='data')


# ============================================================================
# 示例 5：OBV 能量潮（量价配合指标）
# ============================================================================

def tdx_obv_to_qlib():
    """
    通达信公式:
        OBV:SUM(IF(CLOSE>REF(CLOSE,1),VOL,IF(CLOSE<REF(CLOSE,1),-VOL,0)),0);
        VOL_OBV_RATIO:OBV/MA(OBV,20);

    Qlib 因子实现:
    """
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()
    df_reset = df_reset.rename(columns={'date': 'datetime'})

    def calc_obv(group):
        close = group['$close']
        volume = group['$volume']

        # 价格变化
        price_change = close.diff()

        # 每日 OBV 变化
        obv_change = volume.copy()
        obv_change[price_change > 0] = volume[price_change > 0]   # 上涨：+成交量
        obv_change[price_change < 0] = -volume[price_change < 0] # 下跌：-成交量
        obv_change[price_change == 0] = 0  # 平盘：0

        # 累计 OBV
        obv = obv_change.cumsum()

        # OBV 20日均线
        obv_ma = obv.rolling(20).mean()

        # OBV 比率
        obv_ratio = obv / obv_ma

        return obv_ratio

    df_reset['OBV_RATIO'] = df_reset.groupby('instrument', group_keys=False).apply(calc_obv)

    result = df_reset.set_index(['datetime', 'instrument'])[['OBV_RATIO']]
    result.to_hdf('result.h5', key='data')


# ============================================================================
# 示例 6：金叉死叉信号（交易信号）
# ============================================================================

def txd_cross_signal_to_qlib():
    """
    通达信公式:
        MA5:MA(CLOSE,5);
        MA20:MA(CLOSE,20);
        BUY_SIGNAL:CROSS(MA5, MA20);
        SELL_SIGNAL:CROSS(MA20, MA5);

    Qlib 因子实现:
    """
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()
    df_reset = df_reset.rename(columns={'date': 'datetime'})

    def calc_cross_signal(group):
        close = group['$close']

        # MA5 和 MA20
        ma5 = close.rolling(window=5).mean()
        ma20 = close.rolling(window=20).mean()

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

    df_reset['CROSS_SIGNAL'] = df_reset.groupby('instrument', group_keys=False).apply(calc_cross_signal)

    result = df_reset.set_index(['datetime', 'instrument'])[['CROSS_SIGNAL']]
    result.to_hdf('result.h5', key='data')


# ============================================================================
# 示例 7：自定义综合因子
# ============================================================================

def tdx_composite_factor_to_qlib():
    """
    通达信公式（自定义多因子组合）:
        # 趋势因子
        MA_TREND := (MA(CLOSE,5) - MA(CLOSE,20)) / MA(CLOSE,20);

        # 波动率因子
        VOLATILITY := STD(CLOSE/REF(CLOSE,1)-1, 20);

        # 动量因子
        MOMENTUM := CLOSE / REF(CLOSE, 10) - 1;

        # 量价关系因子
        VOLUME_PRICE := (CLOSE-OPEN) / OPEN * VOLUME;

        # 综合评分
        SCORE := MA_TREND * 0.3 + MOMENTUM * 0.3 + VOLATILITY * 0.2 + VOLUME_PRICE * 0.2;

    Qlib 因子实现:
    """
    df = pd.read_hdf('daily_pv.h5', key='data')
    df_reset = df.reset_index()
    df_reset = df_reset.rename(columns={'date': 'datetime'})

    def calc_composite_factor(group):
        close = group['$close']
        high = group['$high']
        low = group['$low']
        open_ = group['$open']
        volume = group['$volume']

        # 1. 趋势因子
        ma5 = close.rolling(5).mean()
        ma20 = close.rolling(20).mean()
        ma_trend = (ma5 - ma20) / ma20

        # 2. 波动率因子
        returns = close.pct_change()
        volatility = returns.rolling(20).std()

        # 3. 动量因子
        momentum = close / close.shift(10) - 1

        # 4. 量价关系因子
        volume_price = ((close - open_) / open_) * volume

        # 标准化（z-score）
        def zscore(x):
            return (x - x.mean()) / x.std()

        # 归一化后组合
        ma_trend_norm = zscore(ma_trend).fillna(0)
        momentum_norm = zscore(momentum).fillna(0)
        volatility_norm = zscore(volatility).fillna(0)
        volume_price_norm = zscore(volume_price).fillna(0)

        # 综合评分
        score = (ma_trend_norm * 0.3 +
                 momentum_norm * 0.3 +
                 volatility_norm * 0.2 +
                 volume_price_norm * 0.2)

        return score

    df_reset['COMPOSITE_SCORE'] = df_reset.groupby('instrument', group_keys=False).apply(calc_composite_factor)

    result = df_reset.set_index(['datetime', 'instrument'])[['COMPOSITE_SCORE']]
    result.to_hdf('result.h5', key='data')


# ============================================================================
# 主函数：运行所有示例
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("通达信公式转换为 RD-Agent 因子 - 实战示例")
    print("=" * 80)

    examples = {
        '1. MACD 指标': tdx_macd_to_qlib,
        '2. KDJ 指标': tdx_kdj_to_qlib,
        '3. RSI 指标': tdx_rsi_to_qlib,
        '4. 布林带 BOLL': tdx_boll_to_qlib,
        '5. OBV 能量潮': tdx_obv_to_qlib,
        '6. 金叉死叉信号': txd_cross_signal_to_qlib,
        '7. 综合因子': tdx_composite_factor_to_qlib,
    }

    print("\n可用的示例：")
    for name, func in examples.items():
        print(f"  - {name}")

    print("\n使用方法：")
    print("  import tdx_examples")
    print("  tdx_examples.tdx_macd_to_qlib()  # 运行 MACD 示例")

    print("\n" + "=" * 80)
    print("提示：这些示例可以直接集成到 RD-Agent 的因子生成流程中！")
    print("=" * 80)
