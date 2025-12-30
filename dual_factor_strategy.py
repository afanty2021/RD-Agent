"""
双因子选股策略 - 完全修复版

基于Qlib源码分析的修复:
1. $amount是Qlib标准字段，可直接使用
2. D.instruments()返回配置字典，D.features()会自动过滤有效股票
3. 日期范围使用正确的边界处理
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


def get_qlib_data(market='csi300', start_date='2024-01-01', end_date=None):
    """
    从Qlib获取数据 - 完全修复版

    修复要点:
    1. $amount是Qlib标准字段，可直接使用
    2. D.features()会自动根据instruments配置过滤有效股票
    3. 使用日频数据，end_date自动使用最后一个交易日
    """
    import qlib
    from qlib.data import D

    # 初始化Qlib
    qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region='cn')

    # 设置结束日期
    if end_date is None:
        # 使用日历的最后一个交易日
        cal = D.calendar(freq='day')
        end_date = pd.Timestamp(cal[-1]).strftime('%Y-%m-%d')
    else:
        # 验证日期
        try:
            end_dt = pd.Timestamp(end_date)
            cal = D.calendar(freq='day')
            cal_last = pd.Timestamp(cal[-1])
            if end_dt > cal_last:
                end_date = cal_last.strftime('%Y-%m-%d')
                print(f"  ⚠️  修正结束日期到最后交易日: {end_date}")
        except Exception as e:
            print(f"  ⚠️  日期处理错误: {e}")

    print(f"  ✓ 股票池: {market.upper()}")
    print(f"  ✓ 查询范围: {start_date} 至 {end_date}")

    # 获取instruments配置（注意：这是配置字典，不是股票列表）
    instruments = D.instruments(market=market)
    print(f"  ✓ Instruments配置类型: {type(instruments)}")

    # 标准字段（$amount是Qlib标准字段）
    fields = ['$open', '$high', '$low', '$close', '$volume', '$amount']

    # 使用D.features获取数据（会自动过滤有效股票）
    print(f"  ✓ 获取数据...")
    df = D.features(
        instruments=instruments,
        fields=fields,
        start_time=start_date,
        end_time=end_date,
        freq='day'
    )
    df.columns = fields
    df = df.reset_index()

    print(f"  ✓ 数据时间范围: {df['datetime'].min()} 至 {df['datetime'].max()}")
    print(f"  ✓ 数据量: {len(df)} 行")
    print(f"  ✓ 股票数量: {df['instrument'].nunique()} 只")
    print(f"  ✓ 数据列: {df.columns.tolist()}")

    return df


# ==================== 因子1: 滚动岭回归因子 ====================

def calculate_feature_VAM_15(df):
    """
    特征1: VAM_15 - 15日波动率调整动量
    公式: VAM_{15} = M_{15} / σ_{15}
    """
    print("  - 计算 VAM_15 (15日波动率调整动量)...")

    df['daily_return'] = df.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=1)
    )
    df['momentum_15'] = df.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=15)
    )
    df['volatility_15'] = df.groupby('instrument')['daily_return'].transform(
        lambda x: x.rolling(window=15, min_periods=15).std()
    )
    df['VAM_15'] = df['momentum_15'] / df['volatility_15'].replace(0, np.nan)

    return df


def calculate_feature_VSVN_5_20(df):
    """
    特征2: VSVN_5_20 - 5日成交量激变归一化
    公式: VSVN_{5,20} = (Volume_t / MA_5(Volume_{t-5:t-1})) / σ_Volume,20
    """
    print("  - 计算 VSVN_5_20 (成交量激变归一化)...")

    df['volume_ma_5'] = df.groupby('instrument')['$volume'].transform(
        lambda x: x.shift(1).rolling(window=5, min_periods=1).mean()
    )
    df['volume_surge'] = df['$volume'] / df['volume_ma_5'].replace(0, np.nan)
    df['volume_volatility_20'] = df.groupby('instrument')['$volume'].transform(
        lambda x: x.rolling(window=20, min_periods=20).std()
    )
    df['VSVN_5_20'] = df['volume_surge'] / df['volume_volatility_20'].replace(0, np.nan)

    return df


def calculate_feature_DDM_20(df):
    """
    特征3: DDM_20 - 20日下行偏差调整动量
    公式: DDM_{20} = M_{20} / DD_{20}
    """
    print("  - 计算 DDM_20 (20日下行偏差调整动量)...")

    df['momentum_20'] = df.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(periods=20)
    )
    df['daily_return'] = df.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change()
    )

    def downside_deviation(returns):
        negative_returns = returns[returns < 0]
        if len(negative_returns) == 0:
            return np.nan
        return np.sqrt((negative_returns ** 2).mean())

    df['downside_deviation_20'] = df.groupby('instrument')['daily_return'].transform(
        lambda x: x.rolling(window=20, min_periods=20).apply(downside_deviation)
    )
    df['DDM_20'] = df['momentum_20'] / df['downside_deviation_20'].replace(0, np.nan)

    return df


def calculate_feature_RSI_10(df):
    """
    特征4: RSI_10 - 10日相对强弱指标
    公式: RSI_{10} = 100 - 100 / (1 + RS)
    """
    print("  - 计算 RSI_10 (10日相对强弱指标)...")

    df['price_change'] = df.groupby('instrument')['$close'].transform(lambda x: x.diff())
    df['gain'] = df['price_change'].apply(lambda x: x if x > 0 else 0)
    df['loss'] = df['price_change'].apply(lambda x: -x if x < 0 else 0)
    df['avg_gain_10'] = df.groupby('instrument')['gain'].transform(
        lambda x: x.rolling(window=10, min_periods=10).mean()
    )
    df['avg_loss_10'] = df.groupby('instrument')['loss'].transform(
        lambda x: x.rolling(window=10, min_periods=10).mean()
    )
    df['RS'] = df['avg_gain_10'] / df['avg_loss_10'].replace(0, np.nan)
    df['RSI_10'] = 100 - 100 / (1 + df['RS'])

    return df


def calculate_ridge_regression_factor(df, lambda_reg=0.1, window=60):
    """
    滚动岭回归因子（年化收益13.31%）

    公式:
        F_t = β_{0,t} + β_{1,t}×VAM_{15,t} + β_{2,t}×VSVN_{5,20,t} + β_{3,t}×DDM_{20,t} + β_{4,t}×RSI_{10,t}

        其中 β_t 通过岭回归估计:
        β_t = (X'X + λI)^(-1) X'Y
    """
    print("\n🧮 计算岭回归因子...")

    df_reset = df.copy()
    df_reset = df_reset.sort_values(['instrument', 'datetime'])

    # 计算四个特征
    df_reset = calculate_feature_VAM_15(df_reset)
    df_reset = calculate_feature_VSVN_5_20(df_reset)
    df_reset = calculate_feature_DDM_20(df_reset)
    df_reset = calculate_feature_RSI_10(df_reset)

    # 目标变量：次日收益率
    df_reset['next_day_return'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change().shift(-1)
    )

    features = ['VAM_15', 'VSVN_5_20', 'DDM_20', 'RSI_10']
    print(f"  - 执行滚动岭回归 (窗口={window}天, λ={lambda_reg})...")

    def rolling_ridge_regression(group):
        group = group.copy()
        group['Ridge_Factor'] = np.nan

        for i in range(window, len(group)):
            X = group[features].iloc[i-window:i].values
            Y = group['next_day_return'].iloc[i-window:i].values

            valid_mask = ~np.isnan(X).any(axis=1) & ~np.isnan(Y)
            X_valid = X[valid_mask]
            Y_valid = Y[valid_mask]

            if len(X_valid) >= 20:
                X_with_intercept = np.column_stack([np.ones(len(X_valid)), X_valid])
                try:
                    XtX = X_with_intercept.T @ X_with_intercept
                    reg_matrix = lambda_reg * np.eye(XtX.shape[0])
                    beta = np.linalg.inv(XtX + reg_matrix) @ X_with_intercept.T @ Y_valid

                    current_features = group[features].iloc[i].values
                    current_with_intercept = np.concatenate([[1], current_features])
                    factor_value = current_with_intercept @ beta
                    group.iloc[i, group.columns.get_loc('Ridge_Factor')] = factor_value
                except:
                    continue

        return group

    df_reset = df_reset.groupby('instrument', group_keys=False).apply(rolling_ridge_regression)
    return df_reset[['datetime', 'instrument', 'Ridge_Factor']]


# ==================== 因子2: XGBoost波动率制度因子 ====================

def calculate_xgboost_volatility_factor(df, max_depth=6, learning_rate=0.1, n_estimators=100):
    """
    XGBoost波动率制度因子（年化收益13.12%）

    方法:
        1. 计算日内波动率 = High - Low
        2. 计算过去20日波动率中位数作为基准
        3. 计算未来5日平均波动率作为目标
        4. 构造30个滞后特征（价格、成交量、动量各10个滞后）
        5. 训练XGBoost分类器预测高/低波动率制度
        6. 输出高波动率制度概率作为因子值
    """
    print("\n🧮 计算XGBoost波动率制度因子...")

    df_reset = df.copy()
    df_reset = df_reset.sort_values(['instrument', 'datetime'])

    df_reset['daily_range'] = df_reset['$high'] - df_reset['$low']
    df_reset['daily_momentum'] = df_reset.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change()
    )

    df_reset['range_median_20d'] = df_reset.groupby('instrument')['daily_range'].transform(
        lambda x: x.rolling(window=20, min_periods=20).median()
    )

    df_reset['range_avg_next_5d'] = df_reset.groupby('instrument')['daily_range'].transform(
        lambda x: x.shift(-5).rolling(window=5, min_periods=5).mean()
    )

    df_reset['target'] = (df_reset['range_avg_next_5d'] > df_reset['range_median_20d']).astype(int)

    print("  - 构造滞后特征 (10个滞后 × 3个变量 = 30个特征)...")
    feature_cols = []

    for lag in range(1, 11):
        df_reset[f'range_lag_{lag}'] = df_reset.groupby('instrument')['daily_range'].transform(
            lambda x: x.shift(lag)
        )
        df_reset[f'volume_lag_{lag}'] = df_reset.groupby('instrument')['$volume'].transform(
            lambda x: x.shift(lag)
        )
        df_reset[f'momentum_lag_{lag}'] = df_reset.groupby('instrument')['daily_momentum'].transform(
            lambda x: x.shift(lag)
        )
        feature_cols.extend([f'range_lag_{lag}', f'volume_lag_{lag}', f'momentum_lag_{lag}'])

    df_features = df_reset.dropna(subset=feature_cols + ['target']).copy()
    df_features = df_features.sort_values('datetime')

    if len(df_features) == 0:
        print("  ✗ 没有有效数据")
        return pd.DataFrame(columns=['datetime', 'instrument', 'XGBoost_Factor'])

    unique_dates = sorted(df_features['datetime'].unique())
    split_idx = int(len(unique_dates) * 0.7)
    train_dates = set(unique_dates[:split_idx])

    train_mask = df_features['datetime'].isin(train_dates)
    X_train = df_features[train_mask][feature_cols]
    y_train = df_features[train_mask]['target']

    print(f"  - 训练集: {len(X_train)} 样本")
    print(f"  - 训练XGBoost模型...")
    model = xgb.XGBClassifier(
        max_depth=max_depth,
        learning_rate=learning_rate,
        n_estimators=n_estimators,
        random_state=42,
        verbosity=0
    )
    model.fit(X_train, y_train)

    df_all_features = df_reset.dropna(subset=feature_cols).copy()
    if len(df_all_features) > 0:
        X_all = df_all_features[feature_cols]
        df_all_features['XGBoost_Factor'] = model.predict_proba(X_all)[:, 1]
        return df_all_features[['datetime', 'instrument', 'XGBoost_Factor']]

    return pd.DataFrame(columns=['datetime', 'instrument', 'XGBoost_Factor'])


# ==================== 因子组合与选股 ====================

def combine_and_standardize_factors(ridge_df, xgb_df, ridge_weight=0.5, xgb_weight=0.5):
    """合并并标准化因子"""
    print("\n📊 合并和标准化因子...")

    combined = pd.merge(ridge_df, xgb_df, on=['datetime', 'instrument'], how='inner')
    print(f"  ✓ 合并后数据量: {len(combined)} 行")

    combined['Ridge_zscore'] = combined.groupby('datetime')['Ridge_Factor'].transform(
        lambda x: (x - x.mean()) / x.std()
    )
    combined['XGBoost_zscore'] = combined.groupby('datetime')['XGBoost_Factor'].transform(
        lambda x: (x - x.mean()) / x.std()
    )

    combined['Ridge_zscore'] = combined['Ridge_zscore'].replace([np.inf, -np.inf], np.nan).fillna(0)
    combined['XGBoost_zscore'] = combined['XGBoost_zscore'].replace([np.inf, -np.inf], np.nan).fillna(0)

    combined['Combined_Factor'] = (
        combined['Ridge_zscore'] * ridge_weight +
        combined['XGBoost_zscore'] * xgb_weight
    )

    return combined


def select_stocks(combined_df, date, top_n=50, min_zscore=0.5):
    """选股"""
    date_data = combined_df[combined_df['datetime'] == date].copy()

    if len(date_data) == 0:
        print(f"\n✗ {date} 没有数据")
        return [], None

    filtered = date_data[date_data['Combined_Factor'] >= min_zscore]

    if len(filtered) == 0:
        filtered = date_data.nlargest(top_n, 'Combined_Factor')
    else:
        filtered = filtered.nlargest(top_n, 'Combined_Factor')

    stocks = filtered['instrument'].tolist()

    print(f"\n{'='*70}")
    print(f"📈 {date} 选股结果 (TOP {len(stocks)})")
    print(f"{'='*70}")
    print(f"  股票池: {len(date_data)} 只 | 符合阈值: {len(date_data[date_data['Combined_Factor'] >= min_zscore])} 只")

    print(f"\n  前20只:")
    for i, (idx, row) in enumerate(filtered.head(20).iterrows(), 1):
        print(f"  {i:2d}. {row['instrument']:10s} - 综合得分: {row['Combined_Factor']:6.2f} (岭回归: {row['Ridge_zscore']:5.2f}, XGBoost: {row['XGBoost_zscore']:5.2f})")

    return stocks, filtered


# ==================== 主程序 ====================

def main():
    print("="*70)
    print("🤖 双因子选股策略（完全修复版）")
    print("="*70)

    # 市场配置
    market = 'all'

    # 1. 获取数据
    print("\n📥 步骤 1/4: 获取Qlib数据...")
    df = get_qlib_data(
        market=market,
        start_date='2024-01-01',
        end_date=None  # 自动使用最后交易日
    )

    # 2. 计算岭回归因子
    print("\n📊 步骤 2/4: 计算岭回归因子...")
    ridge_factor = calculate_ridge_regression_factor(df, lambda_reg=0.1, window=60)

    # 3. 计算XGBoost因子
    print("\n📊 步骤 3/4: 计算XGBoost波动率制度因子...")
    xgb_factor = calculate_xgboost_volatility_factor(df, max_depth=6, learning_rate=0.1, n_estimators=100)

    # 4. 合并因子
    print("\n📊 步骤 4/4: 合并因子并选股...")
    combined = combine_and_standardize_factors(ridge_factor, xgb_factor)

    # 保存结果
    latest_date = combined['datetime'].max()
    combined.to_csv(f'dual_factor_strategy_{market}_{latest_date.strftime("%Y%m%d")}.csv', index=False)
    print(f"\n  ✓ 因子数据已保存: dual_factor_strategy_{market}_{latest_date.strftime('%Y%m%d')}.csv")

    # 选股
    stocks, details = select_stocks(combined, latest_date, top_n=50, min_zscore=0.5)

    if details is not None:
        details.to_csv(f'stock_selection_{market}_{latest_date.strftime("%Y%m%d")}.csv', index=False)

    print("\n" + "="*70)
    print("✅ 选股完成！")
    print("="*70)

    return combined, stocks


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
