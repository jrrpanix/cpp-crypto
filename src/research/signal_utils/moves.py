import polars as pl

def trigger(df: pl.DataFrame, window: int, threshold: float, overlap: bool = False):
    """
    For each possible window in the kline DataFrame, find all places where
    (lastwindow_price - beginwindow_price) / beginwindow_price > threshold (if threshold > 0)
    or < threshold (if threshold < 0).
    If overlap=False, remove overlapping triggers (i.e., if a trigger's window overlaps with the next trigger's start, skip the next trigger).
    Returns two DataFrames:
      - start_df: rows where the window starts and the condition is met
      - end_df: rows where the window ends and the condition is met
    """
    if 'close' not in df.columns:
        raise ValueError("DataFrame must have a 'close' column")
    prices = df['close']
    # Compute windowed returns
    begin_prices = prices[:-window]
    end_prices = prices[window:]
    returns = (end_prices - begin_prices) / begin_prices
    # Find indices where condition is met
    if threshold > 0:
        trigger_idx = (returns > threshold).to_numpy().nonzero()[0]
    else:
        trigger_idx = (returns < threshold).to_numpy().nonzero()[0]
    # Remove overlaps if requested
    if not overlap and len(trigger_idx) > 0:
        non_overlap_idx = []
        last_end = -1
        for idx in trigger_idx:
            if idx > last_end:
                non_overlap_idx.append(idx)
                last_end = idx + window - 1
        trigger_idx = pl.Series(non_overlap_idx).to_numpy()
    # Start rows: at trigger_idx
    if len(trigger_idx) == 0:
        start_df = df.head(0)
    else:
        start_df = df[trigger_idx]
    # End rows: at trigger_idx + window
    end_idx = trigger_idx + window
    end_idx = end_idx[end_idx < len(df)]  # avoid out-of-bounds
    if len(end_idx) == 0:
        end_df = df.head(0)
    else:
        end_df = df[end_idx]
    return start_df, end_df
