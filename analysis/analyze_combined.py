import pandas as pd
import numpy as np

def calculate_atr(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr

def analyze_combined():
    df = pd.read_csv('analysis/BTCUSDT_5m.csv')
    df['open_time'] = pd.to_datetime(df['open_time'])
    trades = pd.read_csv('analysis/backtest_results.csv')

    df['atr'] = calculate_atr(df)
    df['atr_pct'] = df['atr'] / df['close'] * 100
    df['vol_sma'] = df['volume'].rolling(20).mean()
    df['rel_vol'] = df['volume'] / df['vol_sma']

    trades_aug = trades.merge(df[['atr_pct', 'rel_vol']], left_on='entry_index', right_index=True)
    trades_aug['success'] = trades_aug['net_profit_pct'] >= 0.002

    # Test Combined Filter
    # ATR > X AND RelVol > Y

    print("Testing Combined Filters...")

    atr_thresholds = [0.2, 0.25, 0.3]
    vol_thresholds = [0.5, 0.8, 1.0, 1.2]

    for a in atr_thresholds:
        for v in vol_thresholds:
            subset = trades_aug[(trades_aug['atr_pct'] > a) & (trades_aug['rel_vol'] > v)]
            if len(subset) > 30:
                wr = subset['success'].mean()
                avg_profit = subset['net_profit_pct'].mean()
                print(f"ATR>{a}% & Vol>{v}: Count={len(subset)}, WinRate={wr*100:.2f}%, AvgProfit={avg_profit*100:.4f}%")

if __name__ == "__main__":
    analyze_combined()
