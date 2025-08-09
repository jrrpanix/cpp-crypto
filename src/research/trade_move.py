import polars as pl
import os
from moves import trigger
from patterns import summary

def symbol_trade_move(parquet_dir, symbol, window, threshold, holding_horizon, price_type):
    files = [f for f in os.listdir(parquet_dir) if f.startswith(symbol) and f.endswith('.parquet')]
    if not files:
        raise FileNotFoundError(f"No parquet file found for symbol {symbol} in {parquet_dir}")
    parquet_file = os.path.join(parquet_dir, files[0])
    df = pl.read_parquet(parquet_file)
    if df is None or df.height == 0:
        raise ValueError("No parquet data loaded.")
    stats = summary(df)
    start_df, end_df = trigger(df, window, threshold)
    from trade_move import trade_move
    trade_type = "buy" if threshold > 0 else "sell"
    trade_df = trade_move(
        df, end_df,
        window=window,
        holding_horizon=holding_horizon,
        entry_price_type=price_type,
        exit_price_type=price_type,
        trade_type=trade_type,
        dollar_amount=1000.0
    )
    # Compute summary stats (raw numbers)
    total_profit_before_fees = trade_df['profit'].sum() if 'profit' in trade_df.columns else 0.0
    total_entry_fees = trade_df['entry_transaction_fee'].sum() if 'entry_transaction_fee' in trade_df.columns else 0.0
    total_exit_fees = trade_df['exit_transaction_fee'].sum() if 'exit_transaction_fee' in trade_df.columns else 0.0
    total_fees = total_entry_fees + total_exit_fees
    total_profit_after_fees = total_profit_before_fees - total_fees
    total_dollar_entry = trade_df['dollar_amount_entry'].sum() if 'dollar_amount_entry' in trade_df.columns else 0.0
    total_dollar_exit = trade_df['dollar_amount_exit'].sum() if 'dollar_amount_exit' in trade_df.columns else 0.0
    num_trades = trade_df.height
    num_winners = (trade_df['profit'] > 0).sum()
    num_losers = (trade_df['profit'] < 0).sum()
    win_loss_ratio = num_winners / num_losers if num_losers > 0 else float('inf')
    avg_profit_before_fees = total_profit_before_fees / num_trades if num_trades > 0 else 0.0
    avg_profit_after_fees = total_profit_after_fees / num_trades if num_trades > 0 else 0.0
    total_dollar_volume = total_dollar_entry + total_dollar_exit
    summary_dict = {
        "summary_stats": stats,
        "num_triggers": start_df.height,
        "total_profit_before_fees": total_profit_before_fees,
        "total_transaction_fees": total_fees,
        "total_profit_after_fees": total_profit_after_fees,
        "total_dollar_entry": total_dollar_entry,
        "total_dollar_exit": total_dollar_exit,
        "total_dollar_volume": total_dollar_volume,
        "num_trades": num_trades,
        "num_winners": num_winners,
        "num_losers": num_losers,
        "win_loss_ratio": win_loss_ratio,
        "avg_profit_before_fees": avg_profit_before_fees,
        "avg_profit_after_fees": avg_profit_after_fees,
    }
    return trade_df, summary_dict

def trade_move(
    df: pl.DataFrame,
    end_df: pl.DataFrame,
    window: int = 1,
    holding_horizon: int = 1,
    entry_price_type: str = "close",
    exit_price_type: str = "close",
    trade_type: str = "buy",
    dollar_amount: float = 1000.0,
    transaction_cost: float = 0.0002,  # Binance maker fee as of Aug 2025
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
