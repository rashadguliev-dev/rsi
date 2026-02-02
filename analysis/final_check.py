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

def final_check():
    df = pd.read_csv('analysis/BTCUSDT_5m.csv')
    df['open_time'] = pd.to_datetime(df['open_time'])
    trades = pd.read_csv('analysis/backtest_results.csv')
    trades['entry_time'] = pd.to_datetime(trades['entry_time'])

    df['atr'] = calculate_atr(df)
    df['atr_pct'] = df['atr'] / df['close'] * 100
    df['vol_sma'] = df['volume'].rolling(20).mean()
    df['rel_vol'] = df['volume'] / df['vol_sma']

    trades_aug = trades.merge(df[['atr_pct', 'rel_vol']], left_on='entry_index', right_index=True)
    trades_aug['hour'] = trades_aug['entry_time'].dt.hour

    # Filter: ATR > 0.3 AND Vol > 1.0
    good_trades = trades_aug[(trades_aug['atr_pct'] > 0.3) & (trades_aug['rel_vol'] > 1.0)]

    print(f"Filtered Trades: {len(good_trades)}")
    print(f"Avg Profit: {good_trades['net_profit_pct'].mean() * 100:.4f}%")
    print(f"Win Rate: {(good_trades['net_profit_pct'] > 0).mean() * 100:.2f}%")

    print("\n--- Hourly Performance of Filtered Trades ---")
    hourly = good_trades.groupby('hour')['net_profit_pct'].agg(['count', 'mean'])
    print(hourly)

if __name__ == "__main__":
    final_check()
