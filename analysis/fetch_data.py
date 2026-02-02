import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import os

BASE_URL = 'https://api.binance.us'
SYMBOL = 'BTCUSDT'
TIMEFRAMES = ['5m', '15m']
DAYS = 365
LIMIT = 1000

def fetch_klines(symbol, interval, start_time, end_time=None):
    url = f"{BASE_URL}/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_time,
        'limit': LIMIT
    }
    if end_time:
        params['endTime'] = end_time

    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Request failed: {e}")
        return []

def get_data(symbol, interval, days):
    end_time = int(time.time() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)

    all_klines = []
    current_start = start_time

    print(f"Fetching {interval} data for {symbol}...")

    while current_start < end_time:
        klines = fetch_klines(symbol, interval, current_start)
        if not klines:
            break

        all_klines.extend(klines)

        # Update start time to the close time of the last candle + 1ms
        last_close_time = klines[-1][6]
        current_start = last_close_time + 1

        # Sleep to respect rate limits slightly
        time.sleep(0.1)

        # Progress indicator (simple)
        # print(f"Fetched up to {datetime.fromtimestamp(last_close_time/1000)}")

        if len(klines) < LIMIT:
            break

    df = pd.DataFrame(all_klines, columns=[
        'open_time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])

    # Convert types
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, axis=1)
    df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')

    return df

if __name__ == "__main__":
    if not os.path.exists('analysis'):
        os.makedirs('analysis')

    for tf in TIMEFRAMES:
        df = get_data(SYMBOL, tf, DAYS)
        filename = f"analysis/{SYMBOL}_{tf}.csv"
        df.to_csv(filename, index=False)
        print(f"Saved {len(df)} rows to {filename}")
