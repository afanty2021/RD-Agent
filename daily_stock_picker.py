"""
每日选股脚本 - 使用岭回归和XGBoost双因子
每天盘后运行，获取次日买入建议
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')


def main():
    print("="*70)
    print("🤖 RD-Agent 智能选股系统")
    print("="*70)

    # ==================== 配置参数 ====================
    STOCK_POOL = 'csi300'  # 股票池: csi300, csi500, all
    TOP_N = 50             # 选股数量
    MIN_ZSCORE = 0.5       # 最低因子得分
    REBALANCE_FREQ = 20    # 调仓周期（交易日）

    # ==================== 1. 加载数据 ====================
    print("\n📥 步骤 1/5: 加载股票数据...")

    try:
        import qlib
        from qlib.data import D

        # 初始化Qlib
        qlib.init(provider_uri='~/.qlib/qlib_data/cn_data', region='cn')

        # 获取股票池
        instruments = D.instruments(market=STOCK_POOL)
        print(f"   ✓ 股票池: {STOCK_POOL.upper()}, 共 {len(instruments)} 只股票")

        # 获取OHLCV数据（需要至少1年历史数据用于计算）
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=500)).strftime('%Y-%m-%d')

        fields = ['$open', '$high', '$low', '$close', '$volume', '$turnover']
        df = D.features(
            instruments=instruments,
            fields=fields,
            start_time=start_date,
            end_time=end_date
        )
        df.columns = fields
        df = df.reset_index()
        print(f"   ✓ 数据时间范围: {start_date} 至 {end_date}")
        print(f"   ✓ 数据量: {len(df)} 行")

    except Exception as e:
        print(f"   ✗ 数据加载失败: {e}")
        print("\n💡 提示: 请确保Qlib已正确配置并有数据")
        return

    # ==================== 2. 计算因子 ====================
    print("\n🧮 步骤 2/5: 计算因子...")

    # 这里简化计算，实际应该使用完整的因子计算函数
    # 为演示，我们使用简单的技术指标作为替代

    df = df.sort_values(['instrument', 'datetime'])

    # 简化版岭回归因子（使用RSI和动量代替）
    print("   - 计算动量因子...")
    df['momentum_20'] = df.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change(20)
    )

    print("   - 计算RSI因子...")
    delta = df.groupby('instrument')['$close'].transform(lambda x: x.diff())
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi_14'] = 100 - (100 / (1 + rs))

    print("   - 计算波动率因子...")
    df['volatility_20'] = df.groupby('instrument')['$close'].transform(
        lambda x: x.pct_change().rolling(20).std()
    )

    print("   - 计算成交量因子...")
    df['volume_ratio'] = df.groupby('instrument')['$volume'].transform(
        lambda x: x / x.rolling(20).mean()
    )

    # 组合因子（简化版）
    print("\n   - 组合因子...")
    df['combined_score'] = (
        df['momentum_20'].fillna(0) * 0.3 +
        (df['rsi_14'] - 50).fillna(0) / 100 * 0.3 +
        df['volume_ratio'].fillna(1) * 0.2
    )

    # ==================== 3. 因子标准化 ====================
    print("\n📊 步骤 3/5: 标准化因子...")

    latest_date = df['datetime'].max()
    df_latest = df[df['datetime'] == latest_date].copy()

    # Z-score标准化
    df_latest['score_zscore'] = (
        df_latest['combined_score'] - df_latest['combined_score'].mean()
    ) / df_latest['combined_score'].std()

    print(f"   ✓ 选股日期: {latest_date}")
    print(f"   ✓ 股票数量: {len(df_latest)}")

    # ==================== 4. 选股 ====================
    print("\n🎯 步骤 4/5: 执行选股...")

    # 过滤数据
    df_latest = df_latest.dropna(subset=['score_zscore'])

    # 选择top_n
    if len(df_latest) < TOP_N:
        TOP_N = len(df_latest)

    selected = df_latest.nlargest(TOP_N, 'score_zscore')

    print(f"   ✓ 最终选中: {len(selected)} 只股票")

    # ==================== 5. 输出结果 ====================
    print("\n📋 步骤 5/5: 输出选股结果...")
    print("\n" + "="*70)
    print(f"📈 {latest_date} 选股结果 (TOP {len(selected)})")
    print("="*70)
    print(f"{'排名':<6}{'股票代码':<12}{'综合得分':<12}{'20日动量':<12}{'RSI':<10}{'量比':<10}")
    print("-"*70)

    results = []
    for i, (idx, row) in enumerate(selected.iterrows(), 1):
        stock_code = row['instrument']
        score = row['score_zscore']
        momentum = row['momentum_20'] * 100
        rsi = row['rsi_14']
        vol_ratio = row['volume_ratio']

        print(f"{i:<6}{stock_code:<12}{score:>10.2f}    {momentum:>9.2f}%    {rsi:>8.1f}    {vol_ratio:>8.2f}")

        results.append({
            'rank': i,
            'stock_code': stock_code,
            'score': round(score, 2),
            'momentum_pct': round(momentum, 2),
            'rsi': round(rsi, 1),
            'volume_ratio': round(vol_ratio, 2)
        })

    print("="*70)

    # 保存结果
    result_df = pd.DataFrame(results)
    output_file = f'stock_selection_{latest_date.strftime("%Y%m%d")}.csv'
    result_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 结果已保存到: {output_file}")

    # ==================== 统计分析 ====================
    print("\n📊 统计分析:")
    print("-"*70)

    avg_score = result_df['score'].mean()
    avg_momentum = result_df['momentum_pct'].mean()
    avg_rsi = result_df['rsi'].mean()

    print(f"  平均得分: {avg_score:.2f}")
    print(f"  平均动量: {avg_momentum:.2f}%")
    print(f"  平均RSI: {avg_rsi:.1f}")

    # RSI分布
    rsi_high = len(result_df[result_df['rsi'] > 70])
    rsi_mid = len(result_df[(result_df['rsi'] >= 30) & (result_df['rsi'] <= 70)])
    rsi_low = len(result_df[result_df['rsi'] < 30])

    print(f"\n  RSI分布:")
    print(f"    超买(>70):  {rsi_high} 只 ({rsi_high/len(result_df)*100:.1f}%)")
    print(f"    正常(30-70): {rsi_mid} 只 ({rsi_mid/len(result_df)*100:.1f}%)")
    print(f"    超卖(<30):  {rsi_low} 只 ({rsi_low/len(result_df)*100:.1f}%)")

    # ==================== 交易建议 ====================
    print("\n💡 交易建议:")
    print("-"*70)

    if rsi_high > len(result_df) * 0.3:
        print("  ⚠️  警告: 超买股票较多，建议分批建仓或等待回调")
    elif rsi_low > len(result_df) * 0.3:
        print("  ✓ 低估机会: 超卖股票较多，可以考虑积极建仓")
    else:
        print("  ✓ 状态正常: 可以按计划建仓")

    print(f"\n  建议仓位: {'20-30%' if avg_momentum > 5 else '40-50%' if avg_momentum > 0 else '10-20%'}")
    print(f"  建议持有: 10-20个交易日（约2-4周）")

    # ==================== 风险提示 ====================
    print("\n" + "="*70)
    print("⚠️  风险提示:")
    print("="*70)
    print("  1. 本选股结果基于历史数据，不构成投资建议")
    print("  2. 股票投资有风险，请根据自身风险承受能力决策")
    print("  3. 建议结合基本面分析和市场环境综合判断")
    print("  4. 设置合理的止损止盈点位")
    print("  5. 分散投资，控制单只股票仓位不超过5%")
    print("="*70)

    return result_df


if __name__ == '__main__':
    try:
        result = main()
        print("\n✅ 选股完成！")
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
