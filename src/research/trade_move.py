import polars as pl
from typing import List

def trade_move(
    df: pl.DataFrame,
    end_df: pl.DataFrame,
    window: int = 1,
    holding_horizon: int = 1,
    entry_price_type: str = "close",
    exit_price_type: str = "close",
    trade_type: str = "buy",
    dollar_amount: float = 1000.0,
    transaction_cost: float = 0.005,
):
    """
    Simulate trades after each ending time in end_df, using the original kline df.
    Returns a clean DataFrame with columns:
      ['trigger_time', 'open_trade_time', 'entry_price', 'close_trade_time', 'close_trade_price', 'profit', 'direction', 'quantity', 'holding_horizon', 'transaction_fee']
    """
    results = []
    n = len(df)
    for i in range(end_df.height):
        # Find the index in df that matches the end_df row
        if 'open_time' in df.columns and 'open_time' in end_df.columns:
            end_time = end_df['open_time'][i]
            entry_idx = int((df['open_time'] > end_time).arg_max())
        else:
            entry_idx = i + 1
        entry_idx_w = entry_idx + window - 1
        exit_idx = entry_idx_w + holding_horizon
        if entry_idx_w >= n or exit_idx >= n:
            continue
        entry_row = df[entry_idx_w]
        exit_row = df[exit_idx]
        # Entry price
        if entry_price_type == "open":
            entry_price = entry_row['open'].item()
        elif entry_price_type == "close":
            entry_price = entry_row['close'].item()
        elif entry_price_type == "high":
            entry_price = entry_row['high'].item()
        elif entry_price_type == "low":
            entry_price = entry_row['low'].item()
        elif entry_price_type == "worst":
            entry_price = entry_row['high'].item() if trade_type == "buy" else entry_row['low'].item()
        else:
            entry_price = entry_row['close'].item()
        # Exit price
        if exit_price_type == "open":
            exit_price = exit_row['open'].item()
        elif exit_price_type == "close":
            exit_price = exit_row['close'].item()
        elif exit_price_type == "high":
            exit_price = exit_row['high'].item()
        elif exit_price_type == "low":
            exit_price = exit_row['low'].item()
        elif exit_price_type == "worst":
            exit_price = exit_row['low'].item() if trade_type == "buy" else exit_row['high'].item()
        else:
            exit_price = exit_row['close'].item()
        # Compute profit
        if trade_type == "buy":
            profit = dollar_amount * (exit_price - entry_price) / entry_price
            quantity = dollar_amount / entry_price
        else:
            profit = dollar_amount * (entry_price - exit_price) / entry_price
            quantity = dollar_amount / entry_price
        # Transaction fees
        entry_transaction_fee = dollar_amount * transaction_cost
        exit_transaction_fee = quantity * exit_price * transaction_cost
        # Dollar amounts
        dollar_amount_entry = dollar_amount
        dollar_amount_exit = quantity * exit_price
        # Fix open_trade_time and close_trade_time to extract scalar if Series
        open_trade_time = entry_row['open_time']
        if hasattr(open_trade_time, 'item'):
            open_trade_time = open_trade_time.item()
        close_trade_time = exit_row['open_time']
        if hasattr(close_trade_time, 'item'):
            close_trade_time = close_trade_time.item()
        results.append({
            'trigger_time': end_df['open_time'][i] if 'open_time' in end_df.columns else int(entry_idx),
            'open_trade_time': open_trade_time,
            'entry_price': float(entry_price),
            'close_trade_time': close_trade_time,
            'close_trade_price': float(exit_price),
            'profit': float(profit),
            'direction': trade_type,
            'quantity': float(quantity),
            'holding_horizon': holding_horizon,
            'entry_transaction_fee': float(entry_transaction_fee),
            'exit_transaction_fee': float(exit_transaction_fee),
            'dollar_amount_entry': float(dollar_amount_entry),
            'dollar_amount_exit': float(dollar_amount_exit)
        })
    return pl.DataFrame(results)
