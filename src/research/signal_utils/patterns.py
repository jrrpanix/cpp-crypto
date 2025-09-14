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

def profit_from_pattern(df, price_col='close', window=60, threshold=0.03, up_prob_threshold=0.7, investment=1000):
    """
    Simulate investing 'investment' amount every time the up interval probability exceeds up_prob_threshold.
    Returns total profit and number of such opportunities.
    """
    prices = df[price_col]
    shifted = prices.shift(-window)
    pct_change = (shifted - prices) / prices
    up_mask = pct_change >= threshold
    # Remove None/NaN values from up_mask
    up_mask_np = up_mask.to_numpy()
    up_mask_np = up_mask_np.astype(float)  # convert to float to handle None/NaN
    up_mask_np = (up_mask_np == 1).astype(int)  # convert True to 1, False/NaN to 0
    # Use a rolling window to calculate up interval probability
    from numpy.lib.stride_tricks import sliding_window_view
    if len(up_mask_np) < window:
        return 0, 0
    roll = sliding_window_view(up_mask_np, window_shape=window)
    up_probs = roll.mean(axis=1)
    # Find indices where up probability exceeds threshold
    import numpy as np
    invest_indices = np.where(up_probs >= up_prob_threshold)[0]
    total_profit = 0
    for idx in invest_indices:
        idx = int(idx)  # Cast to Python int for Polars indexing
        buy = float(prices[idx])
        sell = float(prices[idx+window])
        profit = investment * (sell - buy) / buy
        total_profit += profit
    return total_profit, len(invest_indices)

def windowed_up_down_probabilities(
    df, price_col='close', threshold=0.01, window=10, lookaheads=[1, 5, 10, 30, 60], investment=1000, non_overlapping=True
):
    """
    For each up/down event (price moves up/down by at least 'threshold' over 'window'),
    count how many times the price moves up or down (any direction, not using threshold) at +lookahead*window rows ahead.
    If non_overlapping=True, only count non-overlapping events (skip ahead by window after each event).
    For each up event, report probability of up and down at lookahead; for each down event, report both as well.
    Also compute total profit/loss for each window: if up, simulate buy/hold; if down, simulate sell/short.
    Returns: dict with probabilities and total profit/loss for each lookahead for up and down events, including event count.
    """
    if price_col not in df.columns:
        print(f"Column {price_col} not found in DataFrame.")
        return {}
    prices = df[price_col]
    shifted = prices.shift(-window)
    pct_change = (shifted - prices) / prices
    up_mask = pct_change >= threshold
    down_mask = pct_change <= -threshold
    # Get indices for non-overlapping events
    def get_non_overlapping_indices(mask, window):
        idxs = mask.to_numpy().nonzero()[0]
        non_overlap = []
        last_idx = -window
        for i in idxs:
            if i >= last_idx + window:
                non_overlap.append(i)
                last_idx = i
        return non_overlap
    if non_overlapping:
        up_idx = get_non_overlapping_indices(up_mask, window)
        down_idx = get_non_overlapping_indices(down_mask, window)
    else:
        up_idx = up_mask.to_numpy().nonzero()[0]
        down_idx = down_mask.to_numpy().nonzero()[0]
    results = {'up': {}, 'down': {}}
    for look in lookaheads:
        look_offset = look * window
        # For up events
        up_follow_up = 0
        up_follow_down = 0
        up_total = 0
        up_profit = 0
        for i in up_idx:
            idx = int(i + look_offset)
            if idx < len(prices):
                future_change = prices[idx] - prices[int(i)]
                up_total += 1
                if future_change > 0:
                    up_follow_up += 1
                elif future_change < 0:
                    up_follow_down += 1
                up_profit += investment * (prices[idx] - prices[int(i)]) / prices[int(i)]
        # If threshold is very small, up/down should be close to 50/50
        # If up_total > 0, but all future_change == 0, count as neither up nor down
        up_prob_up = up_follow_up / up_total if up_total > 0 else 0
        up_prob_down = up_follow_down / up_total if up_total > 0 else 0
        results['up'][look] = {'up': up_prob_up, 'down': up_prob_down, 'profit': up_profit, 'n_events': up_total}
        # For down events
        down_follow_up = 0
        down_follow_down = 0
        down_total = 0
        down_profit = 0
        for i in down_idx:
            idx = int(i + look_offset)
            if idx < len(prices):
                future_change = prices[idx] - prices[int(i)]
                down_total += 1
                if future_change > 0:
                    down_follow_up += 1
                elif future_change < 0:
                    down_follow_down += 1
                down_profit += investment * (prices[int(i)] - prices[idx]) / prices[int(i)]
        down_prob_up = down_follow_up / down_total if down_total > 0 else 0
        down_prob_down = down_follow_down / down_total if down_total > 0 else 0
        results['down'][look] = {'up': down_prob_up, 'down': down_prob_down, 'profit': down_profit, 'n_events': down_total}
    # Print diagnostic for small threshold
    if threshold < 0.001:
        print(f"[DIAG] Small threshold: up/down probabilities should be close to 50/50 if data is random.")
        print(f"[DIAG] up_idx count: {len(up_idx)}, down_idx count: {len(down_idx)}")
    return results
