import pandas as pd
import numpy as np

def calculate_rma(series, period):
    return series.ewm(alpha=1/period, adjust=False).mean()

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_ultimate_rsi(df, rsi_length=14, ema_length=14):
    # Upper and Lower (Highest High, Lowest Low)
    df['upper'] = df['close'].rolling(window=rsi_length).max()
    df['lower'] = df['close'].rolling(window=rsi_length).min()

    df['r'] = df['upper'] - df['lower']
    df['d'] = df['close'] - df['close'].shift(1)

    # Diff calculation
    # diff = upper > upper[1] ? r : lower < lower[1] ? -r : d

    diffs = []
    # We need to iterate because of the dependency on previous row's upper/lower
    # Actually, we can vectorize this condition using shift

    upper_prev = df['upper'].shift(1)
    lower_prev = df['lower'].shift(1)

    # Conditions
    cond1 = df['upper'] > upper_prev
    cond2 = df['lower'] < lower_prev

    # Vectorized 'diff'
    # np.select(conditions, choices, default)
    # choices: r, -r, d

    df['diff'] = np.select(
        [cond1, cond2],
        [df['r'], -df['r']],
        default=df['d']
    )

    # RMA of diff and abs(diff)
    # Note: RMA needs to handle NaN at start
    df['num'] = calculate_rma(df['diff'], rsi_length)
    df['den'] = calculate_rma(df['diff'].abs(), rsi_length)

    # Ultimate RSI
    df['ultimate_rsi'] = (df['num'] / df['den']) * 50 + 50

    # Signal Line (EMA of RSI)
    df['signal_line'] = calculate_ema(df['ultimate_rsi'], ema_length)

    return df

def run_backtest(df):
    # Logic
    df = calculate_ultimate_rsi(df)

    # Signals
    # Long: Crossover (RSI crosses above EMA)
    # Short: Crossunder (RSI crosses below EMA)

    df['long_signal'] = (df['ultimate_rsi'] > df['signal_line']) & (df['ultimate_rsi'].shift(1) <= df['signal_line'].shift(1))
    df['short_signal'] = (df['ultimate_rsi'] < df['signal_line']) & (df['ultimate_rsi'].shift(1) >= df['signal_line'].shift(1))

    # Extract trades
    trades = []
    current_trade = None

    # Iterating rows for trade logic
    # Assume we enter on the OPEN of the NEXT bar after signal

    for i in range(1, len(df) - 1):
        # Check for signals at index i
        # If signal at i, we enter at i+1

        row = df.iloc[i]
        next_row = df.iloc[i+1]

        # Close current trade if reverse signal
        if current_trade:
            if current_trade['type'] == 'long' and row['short_signal']:
                # Close Long
                exit_price = next_row['open']
                current_trade['exit_price'] = exit_price
                current_trade['exit_time'] = next_row['open_time']
                current_trade['exit_index'] = i+1

                # Calculate Max Excursion
                # From entry_index to exit_index-1 (the bars held)
                # Actually held from entry_index (Open) to exit_index (Open)
                # So we look at Highs/Lows of bars: entry_index to i

                trade_slice = df.iloc[current_trade['entry_index'] : i+1]
                max_price = trade_slice['high'].max()
                current_trade['max_excursion'] = max_price
                current_trade['max_profit_pct'] = (max_price - current_trade['entry_price']) / current_trade['entry_price']

                current_trade['net_profit_pct'] = (exit_price - current_trade['entry_price']) / current_trade['entry_price'] - 0.001 # 0.1% cost

                trades.append(current_trade)
                current_trade = None

                # Reverse to Short
                current_trade = {
                    'type': 'short',
                    'entry_price': next_row['open'],
                    'entry_time': next_row['open_time'],
                    'entry_index': i+1
                }

            elif current_trade['type'] == 'short' and row['long_signal']:
                # Close Short
                exit_price = next_row['open']
                current_trade['exit_price'] = exit_price
                current_trade['exit_time'] = next_row['open_time']
                current_trade['exit_index'] = i+1

                trade_slice = df.iloc[current_trade['entry_index'] : i+1]
                min_price = trade_slice['low'].min()
                current_trade['max_excursion'] = min_price
                current_trade['max_profit_pct'] = (current_trade['entry_price'] - min_price) / current_trade['entry_price']

                current_trade['net_profit_pct'] = (current_trade['entry_price'] - exit_price) / current_trade['entry_price'] - 0.001

                trades.append(current_trade)
                current_trade = None

                # Reverse to Long
                current_trade = {
                    'type': 'long',
                    'entry_price': next_row['open'],
                    'entry_time': next_row['open_time'],
                    'entry_index': i+1
                }

        else:
            # No current trade, check for new signals
            if row['long_signal']:
                current_trade = {
                    'type': 'long',
                    'entry_price': next_row['open'],
                    'entry_time': next_row['open_time'],
                    'entry_index': i+1
                }
            elif row['short_signal']:
                current_trade = {
                    'type': 'short',
                    'entry_price': next_row['open'],
                    'entry_time': next_row['open_time'],
                    'entry_index': i+1
                }

    return pd.DataFrame(trades)

if __name__ == "__main__":
    df = pd.read_csv('analysis/BTCUSDT_5m.csv')
    df['open_time'] = pd.to_datetime(df['open_time'])

    trades = run_backtest(df)

    if not trades.empty:
        print(f"Total Trades: {len(trades)}")
        print(f"Average Net Profit: {trades['net_profit_pct'].mean() * 100:.4f}%")
        print(f"Win Rate: {(trades['net_profit_pct'] > 0).mean() * 100:.2f}%")

        trades.to_csv('analysis/backtest_results.csv', index=False)
        print("Saved trades to analysis/backtest_results.csv")
    else:
        print("No trades generated.")
