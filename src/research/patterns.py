def count_intervals(df, price_col='close', threshold=0.01, window=10, non_overlapping=False, follow_window=1):
    """
    Counts the number of intervals where the price moves up or down by at least 'threshold' (as a fraction, e.g. 0.01 for 1%)
    over a rolling window of N rows using Polars vectorized operations.
    If non_overlapping=True, only non-overlapping intervals are counted.
    Additionally, counts the number of times a positive interval is followed by another positive, and negative by another negative (follow_window).
    Returns: (up_count, down_count, up_follow_count, down_follow_count)
    """
    if price_col not in df.columns:
        print(f"Column {price_col} not found in DataFrame.")
        return 0, 0, 0, 0
    prices = df[price_col]
    if non_overlapping:
        # Only check every window-th row
        idx = range(0, len(prices) - window, window)
        start_prices = prices.take(idx)
        end_prices = prices.shift(-window).take(idx)
        pct_change = (end_prices - start_prices) / start_prices
    else:
        shifted = prices.shift(-window)
        pct_change = (shifted - prices) / prices
    up_mask = pct_change >= threshold
    down_mask = pct_change <= -threshold
    up_count = up_mask.sum()
    down_count = down_mask.sum()
    # For follow counts, check next interval after a positive/negative
    up_follow_count = 0
    down_follow_count = 0
    up_idx = up_mask.to_numpy().nonzero()[0]
    down_idx = down_mask.to_numpy().nonzero()[0]
    # Convert indices to Python int for Polars indexing
    for i in up_idx:
        idx = int(i + follow_window)
        if idx < len(pct_change):
            if pct_change[idx] >= threshold:
                up_follow_count += 1
    for i in down_idx:
        idx = int(i + follow_window)
        if idx < len(pct_change):
            if pct_change[idx] <= -threshold:
                down_follow_count += 1
    return up_count, down_count, up_follow_count, down_follow_count

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
