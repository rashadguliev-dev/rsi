import pandas as pd
import numpy as np

def calculate_adx(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    up = high - high.shift(1)
    down = low.shift(1) - low

    pos_dm = np.where((up > down) & (up > 0), up, 0)
    neg_dm = np.where((down > up) & (down > 0), down, 0)

    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    pos_di = pd.Series(pos_dm).ewm(alpha=1/period, adjust=False).mean() / atr * 100
    neg_di = pd.Series(neg_dm).ewm(alpha=1/period, adjust=False).mean() / atr * 100

    dx = (pos_di - neg_di).abs() / (pos_di + neg_di) * 100
    adx = dx.ewm(alpha=1/period, adjust=False).mean()
    return adx

def analyze_regime():
    df = pd.read_csv('analysis/BTCUSDT_5m.csv')
    df['open_time'] = pd.to_datetime(df['open_time'])
    trades = pd.read_csv('analysis/backtest_results.csv')
    trades['entry_time'] = pd.to_datetime(trades['entry_time'])

    df['adx'] = calculate_adx(df)

    # Merge ADX
    trades_aug = trades.merge(df[['adx']], left_on='entry_index', right_index=True)
    trades_aug['hour'] = trades_aug['entry_time'].dt.hour

    print("--- Time of Day Analysis ---")
    hourly = trades_aug.groupby('hour')['net_profit_pct'].mean()
    print(hourly * 100)

    print("\n--- ADX Analysis ---")
    bins = [0, 15, 20, 25, 30, 40, 50, 100]
    trades_aug['adx_bin'] = pd.cut(trades_aug['adx'], bins)
    adx_stats = trades_aug.groupby('adx_bin', observed=True)['net_profit_pct'].agg(['count', 'mean'])
    print(adx_stats)

    print("\n--- Best ADX Threshold ---")
    for t in [15, 20, 25, 30]:
        subset = trades_aug[trades_aug['adx'] > t]
        print(f"ADX > {t}: Count={len(subset)}, AvgProfit={subset['net_profit_pct'].mean()*100:.4f}%")

        subset_low = trades_aug[trades_aug['adx'] < t]
        print(f"ADX < {t}: Count={len(subset_low)}, AvgProfit={subset_low['net_profit_pct'].mean()*100:.4f}%")

if __name__ == "__main__":
    analyze_regime()
