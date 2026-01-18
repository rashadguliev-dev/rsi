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

def analyze_failures():
    # Load data
    df = pd.read_csv('analysis/BTCUSDT_5m.csv')
    df['open_time'] = pd.to_datetime(df['open_time'])

    trades = pd.read_csv('analysis/backtest_results.csv')
    trades['entry_time'] = pd.to_datetime(trades['entry_time'])

    # Calculate Indicators on full DF
    df['atr'] = calculate_atr(df)
    df['atr_pct'] = df['atr'] / df['close'] * 100
    df['vol_sma'] = df['volume'].rolling(20).mean()
    df['rel_vol'] = df['volume'] / df['vol_sma']

    # We need to map indicators to trades based on entry_index
    # The trade entry_index corresponds to the bar index in df

    # Merge using entry_index
    trades_aug = trades.merge(df[['atr_pct', 'rel_vol']], left_on='entry_index', right_index=True)

    # Define "Success" as Net Profit >= 0.2%
    trades_aug['success'] = trades_aug['net_profit_pct'] >= 0.002

    print(f"Total Trades: {len(trades_aug)}")
    print(f"Successful Trades (>= 0.2%): {trades_aug['success'].sum()} ({trades_aug['success'].mean()*100:.2f}%)")

    # Analysis 1: ATR Threshold
    print("\n--- ATR Analysis ---")
    bins = [0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.5, 1.0]
    trades_aug['atr_bin'] = pd.cut(trades_aug['atr_pct'], bins)
    stats = trades_aug.groupby('atr_bin', observed=True)['success'].agg(['count', 'mean'])
    print(stats)

    # Find optimal threshold
    # We want a threshold that keeps most successes but removes most failures.
    # Or ensures that if we trade, the success rate is higher.

    # Let's try cumulative logic: Filter trades where ATR < X
    thresholds = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3]
    best_threshold = 0
    best_wr = 0
    best_profit = -100

    for t in thresholds:
        subset = trades_aug[trades_aug['atr_pct'] > t]
        if len(subset) > 50:
            wr = subset['success'].mean()
            avg_profit = subset['net_profit_pct'].mean()
            print(f"ATR > {t:.2f}%: Count={len(subset)}, WinRate={wr*100:.2f}%, AvgProfit={avg_profit*100:.4f}%")

            if avg_profit > best_profit:
                best_profit = avg_profit
                best_threshold = t
                best_wr = wr

    print(f"\nOptimal ATR Threshold: > {best_threshold:.2f}% (Avg Profit: {best_profit*100:.4f}%)")

    # Analysis 2: Volume Analysis
    print("\n--- Volume Analysis ---")
    trades_aug['vol_bin'] = pd.cut(trades_aug['rel_vol'], [0, 0.5, 1, 1.5, 2, 5, 10])
    stats_vol = trades_aug.groupby('vol_bin', observed=True)['success'].agg(['count', 'mean'])
    print(stats_vol)

if __name__ == "__main__":
    analyze_failures()
