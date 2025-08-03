def count_intervals(df, price_col='close', threshold=0.01, window=10):
    """
    Counts the number of intervals where the price moves up or down by at least 'threshold' (as a fraction, e.g. 0.01 for 1%)
    over a rolling window of N rows.
    Returns: (up_count, down_count)
    """
    if price_col not in df.columns:
        print(f"Column {price_col} not found in DataFrame.")
        return 0, 0
    prices = df[price_col].to_numpy()
    up_count = 0
    down_count = 0
    for i in range(len(prices) - window):
        start = prices[i]
        end = prices[i + window]
        change = (end - start) / start if start != 0 else 0
        if change >= threshold:
            up_count += 1
        elif change <= -threshold:
            down_count += 1
    return up_count, down_count

def summary(df):
    """
    Returns a dictionary with summary statistics:
    min_price, max_price, min_price_date, max_price_date,
    open_price, open_price_date, close_price, close_price_date
    """
    from datetime import datetime
    def to_py_datetime(val):
        if hasattr(val, 'to_pydatetime'):
            return val.to_pydatetime()
        elif isinstance(val, (int, float)):
            return datetime.fromtimestamp(val // 1000)
        return val
    result = {}
    # Open price (first row)
    if 'open' in df.columns:
        result['open_price'] = df['open'][0]
        if 'open_time' in df.columns:
            result['open_price_date'] = to_py_datetime(df['open_time'][0])
        elif 'close_time' in df.columns:
            result['open_price_date'] = to_py_datetime(df['close_time'][0])
    # Close price (last row)
    if 'close' in df.columns:
        result['close_price'] = df['close'][-1]
        if 'open_time' in df.columns:
            result['close_price_date'] = to_py_datetime(df['open_time'][-1])
        elif 'close_time' in df.columns:
            result['close_price_date'] = to_py_datetime(df['close_time'][-1])
    # Min/max price from 'high' and 'low' columns
    if 'high' in df.columns:
        result['max_price'] = df['high'].max()
        max_idx = df['high'].arg_max()
        if 'open_time' in df.columns:
            result['max_price_date'] = to_py_datetime(df['open_time'][max_idx])
        elif 'close_time' in df.columns:
            result['max_price_date'] = to_py_datetime(df['close_time'][max_idx])
    if 'low' in df.columns:
        result['min_price'] = df['low'].min()
        min_idx = df['low'].arg_min()
        if 'open_time' in df.columns:
            result['min_price_date'] = to_py_datetime(df['open_time'][min_idx])
        elif 'close_time' in df.columns:
            result['min_price_date'] = to_py_datetime(df['close_time'][min_idx])
    # Date range
    if 'open_time' in df.columns:
        result['min_date'] = to_py_datetime(df['open_time'].min())
        result['max_date'] = to_py_datetime(df['open_time'].max())
    elif 'close_time' in df.columns:
        result['min_date'] = to_py_datetime(df['close_time'].min())
        result['max_date'] = to_py_datetime(df['close_time'].max())
    result['total_rows'] = df.height
    return result
