#!/usr/bin/env python3
"""
Window-based trade simulator using polars.

Simulates a trading strategy based on price movements within a time window.
If price increases by threshold within detection_window, enters a position
and holds for hold_window periods.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl


def calculate_returns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculate returns for each window.

    Args:
        df: DataFrame with 'open' and 'close' columns

    Returns:
        DataFrame with added 'return' column
    """
    return df.with_columns(
        [
            (pl.col("close") / pl.col("open") - 1).alias("return"),
        ]
    )


def detect_signals(
    df: pl.DataFrame,
    up_threshold: float,
    down_threshold: float,
    detection_window: int = 5,
) -> pl.DataFrame:
    """
    Detect when price change exceeds thresholds within detection window.
    
    For each bar, calculates return from the open of the bar detection_window periods ago
    to the close of the current bar. Signals when this return exceeds threshold.

    Args:
        df: DataFrame with 'timestamp', 'open', and 'close' columns
        up_threshold: Minimum return to trigger buy signal (e.g., 0.01 for 1%)
        down_threshold: Maximum return to trigger sell signal (e.g., -0.01 for -1%)
        detection_window: Number of periods to look back (e.g., 5 means compare current close to open from 5 bars ago)

    Returns:
        DataFrame with additional 'signal_up' and 'signal_down' columns
    """
    # Get the open price from detection_window periods ago
    df = df.with_columns(
        [
            pl.col("open").shift(detection_window).alias("window_start_open"),
        ]
    )

    # Calculate return from window start to current close
    # return = (current_close - open_N_periods_ago) / open_N_periods_ago
    df = df.with_columns(
        [
            (
                (pl.col("close") - pl.col("window_start_open")) / pl.col("window_start_open")
            ).alias("window_return")
        ]
    )

    # Create signal flags
    df = df.with_columns(
        [
            (pl.col("window_return") > up_threshold).alias("signal_up"),
            (pl.col("window_return") < down_threshold).alias("signal_down"),
        ]
    )

    return df


def simulate_trades(
    df: pl.DataFrame, hold_window: int, position_size: float, position_limit: int = 1, fee_rate: float = 0.001, num_accounts: int = 1, up_direction: str = "B", down_direction: str = "S"
) -> tuple[pl.DataFrame, dict]:
    """
    Simulate trades based on up and down signals.

    Args:
        df: DataFrame with 'signal_up' and 'signal_down' columns
        hold_window: Number of periods to hold position
        position_size: Dollar amount to invest per trade
        position_limit: Maximum number of concurrent positions allowed (both long and short combined)
        fee_rate: Transaction fee rate applied to both entry and exit (default: 0.001 = 0.1%)
        num_accounts: Number of accounts (1=single account with position reversal, 2=separate long/short accounts)
        up_direction: Trade direction for UP threshold: 'B'=Buy/Long, 'S'=Sell/Short (default: 'B')
        down_direction: Trade direction for DOWN threshold: 'B'=Buy/Long, 'S'=Sell/Short (default: 'S')

    Returns:
        Tuple of (DataFrame with trade results, summary statistics dict)
    """
    # Check for up signals
    up_signals_df = df.filter(pl.col("signal_up") == True)
    up_signal_indices = up_signals_df.select(pl.col("index")).to_series().to_list() if len(up_signals_df) > 0 else []

    # Check for down signals
    down_signals_df = df.filter(pl.col("signal_down") == True)
    down_signal_indices = down_signals_df.select(pl.col("index")).to_series().to_list() if len(down_signals_df) > 0 else []

    if len(up_signal_indices) == 0 and len(down_signal_indices) == 0:
        return pl.DataFrame(), {
            "num_trades": 0,
            "rejected_up_signals": 0,
            "rejected_down_signals": 0,
            "position_limit": position_limit,
            "num_accounts": num_accounts,
            "fee_rate": fee_rate,
            "total_fees": 0.0,
            "trade_size": position_size,
            "max_long_exposure": 0.0,
            "max_short_exposure": 0.0,
            "num_long_trades": 0,
            "num_short_trades": 0,
            "gross_long_profit": 0.0,
            "long_fees": 0.0,
            "net_long_profit": 0.0,
            "gross_short_profit": 0.0,
            "short_fees": 0.0,
            "net_short_profit": 0.0,
            "gross_profit": 0.0,
            "net_profit": 0.0,
            "gross_profit_pct": 0.0,
            "net_profit_pct": 0.0,
            "gross_roi": 0.0,
            "net_roi": 0.0,
            "avg_net_profit": 0.0,
            "avg_profit_pct": 0.0,
            "win_rate": 0.0,
            "num_winners": 0,
            "num_losers": 0,
            "gross_sharpe_ratio": 0.0,
            "net_sharpe_ratio": 0.0,
            "date_range": "N/A",
            "num_days": 0,
            "avg_trades_per_day": 0.0,
        }

    trades = []
    rejected_up_signals = 0
    rejected_down_signals = 0
    
    # Combine and sort all signals by index
    all_signals = []
    for idx in up_signal_indices:
        all_signals.append((idx, "UP", up_direction))
    for idx in down_signal_indices:
        all_signals.append((idx, "DOWN", down_direction))
    
    # Sort by signal index (chronological order)
    all_signals.sort(key=lambda x: x[0])
    
    # Track open positions differently based on num_accounts
    if num_accounts == 1:
        # Single account: track net position (long=positive, short=negative)
        # List of (entry_idx, exit_idx, direction, entry_time, exit_time)
        open_positions = []
    else:
        # Multiple accounts: track long and short separately
        # List of (entry_idx, exit_idx, direction)
        open_positions = []
    
    max_concurrent_positions = 0
    
    # Process every signal with position limit enforcement
    for signal_idx, signal_type, trade_direction in all_signals:
        # Entry: next bar after signal (signal_idx + 1)
        entry_idx = signal_idx + 1

        # Exit: hold_window bars after entry
        exit_idx = entry_idx + hold_window

        # Check if we have enough data
        if exit_idx >= len(df):
            continue

        if num_accounts == 1:
            # Single account logic: close opposite positions and reverse
            # Remove positions that have already exited  
            open_positions = [(e_idx, x_idx, d, e_time, x_time) for e_idx, x_idx, d, e_time, x_time in open_positions if x_idx > entry_idx]
            
            # Check if we have opposite direction positions
            opposite_direction = "S" if trade_direction == "B" else "B"
            opposite_positions = [p for p in open_positions if p[2] == opposite_direction]
            same_direction_positions = [p for p in open_positions if p[2] == trade_direction]
            
            if opposite_positions:
                # Close opposite positions and reverse
                for opp_entry_idx, opp_exit_idx, opp_dir, opp_entry_time, opp_exit_time in opposite_positions:
                    # Find and update the existing trade record for this position
                    # The trade was already added to the trades list when it was opened
                    # We need to update its exit_idx and recalculate profit
                    for trade in trades:
                        if (trade["entry_idx"] == opp_entry_idx and 
                            trade["direction"] == opp_dir and
                            trade["exit_idx"] == opp_exit_idx):  # Match the original scheduled exit
                            # Update to early exit
                            entry_row_for_early = df.row(entry_idx, named=True)
                            early_exit_price = entry_row_for_early["open"]
                            
                            # Get original entry price
                            opp_entry_row = df.row(opp_entry_idx, named=True)
                            opp_entry_price = opp_entry_row["open"]
                            
                            # Calculate fees for early exit
                            entry_fee = position_size * fee_rate
                            exit_fee = position_size * fee_rate
                            total_fees = entry_fee + exit_fee
                            
                            if opp_dir == "B":
                                # Long trade being closed: profit = (exit - entry) / entry
                                profit_pct = (early_exit_price / opp_entry_price) - 1
                                gross_profit_dollars = position_size * profit_pct
                                net_profit_dollars = gross_profit_dollars - total_fees
                                net_profit_pct = net_profit_dollars / position_size
                            else:  # "S" - Short trade
                                # Short trade being closed: profit = (entry - exit) / entry
                                profit_pct = (opp_entry_price / early_exit_price) - 1
                                gross_profit_dollars = position_size * profit_pct
                                net_profit_dollars = gross_profit_dollars - total_fees
                                net_profit_pct = net_profit_dollars / position_size
                            
                            # Update the existing trade record
                            trade["exit_idx"] = entry_idx  # Early exit
                            trade["exit_time"] = entry_row_for_early["open_time"]
                            trade["exit_price"] = early_exit_price
                            trade["profit_pct"] = profit_pct
                            trade["net_profit_pct"] = net_profit_pct
                            trade["gross_profit_dollars"] = gross_profit_dollars
                            trade["fees"] = total_fees
                            trade["net_profit_dollars"] = net_profit_dollars
                            break  # Found and updated the trade
                
                # Remove all opposite positions
                open_positions = same_direction_positions
            else:
                # No opposite positions, just keep same direction
                open_positions = same_direction_positions
            
            # DETECTION: Log state right before limit check
            check_count = len(open_positions)
            will_reject = check_count >= position_limit
            
            # Check position limit for same direction
            if check_count >= position_limit:
                if signal_type == "UP":
                    rejected_up_signals += 1
                else:
                    rejected_down_signals += 1
                continue
            
            # DETECTION: If we get here, we're accepting the trade
            # Store this info for breach detection
            accepted_with_count = check_count
                
        else:
            # Multiple accounts logic: original behavior
            # Close any positions that have already exited
            open_positions = [(e_idx, x_idx, d) for e_idx, x_idx, d in open_positions if x_idx > entry_idx]
            
            # Check position limit - reject trade if at limit
            if len(open_positions) >= position_limit:
                if signal_type == "UP":
                    rejected_up_signals += 1
                else:
                    rejected_down_signals += 1
                continue

        # Get entry and exit prices
        entry_row = df.row(entry_idx, named=True)
        exit_row = df.row(exit_idx, named=True)

        entry_price = entry_row["open"]
        exit_price = exit_row["close"]

        # Calculate transaction fees (applied to both entry and exit)
        entry_fee = position_size * fee_rate
        exit_fee = position_size * fee_rate
        total_fees = entry_fee + exit_fee

        if trade_direction == "B":
            # Calculate profit for long trade (buy low, sell high)
            profit_pct = (exit_price / entry_price) - 1
            gross_profit_dollars = position_size * profit_pct
            net_profit_dollars = gross_profit_dollars - total_fees
            net_profit_pct = net_profit_dollars / position_size
        else:  # trade_direction == "S"
            # Calculate profit for short trade (sell high, buy low)
            profit_pct = (entry_price / exit_price) - 1
            gross_profit_dollars = position_size * profit_pct
            net_profit_dollars = gross_profit_dollars - total_fees
            net_profit_pct = net_profit_dollars / position_size

        # Add to open positions
        if num_accounts == 1:
            open_positions.append((entry_idx, exit_idx, trade_direction, entry_row["open_time"], exit_row["close_time"]))
            
            # DETECTION: Check if we've exceeded the limit for this direction (should never happen)
            same_dir_in_list = [p for p in open_positions if p[2] == trade_direction]
            if len(same_dir_in_list) > position_limit:
                print(f"\n⚠️  BREACH! {trade_direction} positions: {len(same_dir_in_list)} > limit {position_limit} at entry_idx={entry_idx}\n")
        else:
            open_positions.append((entry_idx, exit_idx, trade_direction))
        
        # Track maximum concurrent positions
        if len(open_positions) > max_concurrent_positions:
            max_concurrent_positions = len(open_positions)

        trades.append(
            {
                "signal_idx": signal_idx,
                "entry_idx": entry_idx,
                "exit_idx": exit_idx,
                "entry_time": entry_row["open_time"],
                "exit_time": exit_row["open_time"],  # Use open_time: position exits at start of exit bar
                "signal_type": signal_type,
                "direction": trade_direction,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "profit_pct": profit_pct,
                "net_profit_pct": net_profit_pct,
                "gross_profit_dollars": gross_profit_dollars,
                "fees": total_fees,
                "net_profit_dollars": net_profit_dollars,
                "position_size": position_size,
            }
        )

    if not trades:
        return pl.DataFrame(), {
            "num_trades": 0,
            "rejected_up_signals": rejected_up_signals,
            "rejected_down_signals": rejected_down_signals,
            "position_limit": position_limit,
            "num_accounts": num_accounts,
            "fee_rate": fee_rate,
            "total_fees": 0.0,
            "trade_size": position_size,
            "max_long_exposure": 0.0,
            "max_short_exposure": 0.0,
            "num_up_trades": 0,
            "num_down_trades": 0,
            "gross_up_profit": 0.0,
            "up_fees": 0.0,
            "net_up_profit": 0.0,
            "gross_down_profit": 0.0,
            "down_fees": 0.0,
            "net_down_profit": 0.0,
            "gross_profit": 0.0,
            "net_profit": 0.0,
            "gross_profit_pct": 0.0,
            "net_profit_pct": 0.0,
            "gross_roi": 0.0,
            "net_roi": 0.0,
            "avg_net_profit": 0.0,
            "avg_profit_pct": 0.0,
            "win_rate": 0.0,
            "num_winners": 0,
            "num_losers": 0,
            "sharpe_ratio": 0.0,
            "date_range": "N/A",
            "num_days": 0,
            "avg_trades_per_day": 0.0,
        }

    # Create trades DataFrame
    trades_df = pl.DataFrame(trades)
    
    print(f"DEBUG: Position limit: {position_limit}, Max concurrent during execution: {max_concurrent_positions}")

    # Calculate date range
    first_date = trades_df["entry_time"].min()
    last_date = trades_df["exit_time"].max()
    date_range = f"{first_date} to {last_date}"
    
    # Calculate number of days
    num_days = (last_date - first_date).days if hasattr((last_date - first_date), 'days') else 0
    if num_days == 0:  # Less than a day or same day
        num_days = 1
    
    # Calculate maximum exposure (long and short positions) efficiently
    # Create events for entry (+1) and exit (-1) for each direction
    # Use bar indices instead of timestamps to match execution logic
    long_events = []
    short_events = []
    
    num_long_in_trades = sum(1 for t in trades if t["direction"] == "B")
    num_short_in_trades = sum(1 for t in trades if t["direction"] == "S")
    print(f"DEBUG PRE: Long (B) trades in list: {num_long_in_trades}, Short (S) trades in list: {num_short_in_trades}")
    
    for trade in trades:
        if trade["direction"] == "B":
            long_events.append((trade["entry_idx"], 1, trade["entry_time"]))    # Long entry
            long_events.append((trade["exit_idx"], -1, trade["exit_time"]))      # Long exit
        else:  # "S"
            short_events.append((trade["entry_idx"], 1, trade["entry_time"]))   # Short entry
            short_events.append((trade["exit_idx"], -1, trade["exit_time"]))    # Short exit
    
    print(f"DEBUG POST: Long events created: {len(long_events)}, Short events created: {len(short_events)}")
    print(f"DEBUG POST: Expected long: {num_long_in_trades * 2}, Expected short: {num_short_in_trades * 2}")
    
    # Debug: Count entries vs exits
    long_entries = sum(1 for idx, delta, time in long_events if delta == 1)
    long_exits = sum(1 for idx, delta, time in long_events if delta == -1)
    short_entries = sum(1 for idx, delta, time in short_events if delta == 1)
    short_exits = sum(1 for idx, delta, time in short_events if delta == -1)
    print(f"DEBUG: Long entries: {long_entries}, exits: {long_exits}")
    print(f"DEBUG: Short entries: {short_entries}, exits: {short_exits}")
    
    # Sort events by bar index, with exits before entries at same index
    # This matches the execution logic where we filter out positions with exit_idx >= entry_idx
    long_events.sort(key=lambda x: (x[0], x[1]))  # Sort by (index, delta)
    short_events.sort(key=lambda x: (x[0], x[1]))
    
    # Calculate max long exposure
    max_long_exposure = 0.0
    current_long_count = 0
    max_long_count = 0
    max_long_time = None
    
    # Debug: check for negative counts
    min_long_count = 0
    
    for idx, delta, time in long_events:
        current_long_count += delta
        if current_long_count < min_long_count:
            min_long_count = current_long_count
        if current_long_count > max_long_count:
            max_long_count = current_long_count
            max_long_time = time
        current_exposure = current_long_count * position_size
        if current_exposure > max_long_exposure:
            max_long_exposure = current_exposure
    
    # Calculate max short exposure
    max_short_exposure = 0.0
    current_short_count = 0
    max_short_count = 0
    max_short_time = None
    
    # Debug: check for negative counts
    min_short_count = 0
    
    for idx, delta, time in short_events:
        current_short_count += delta
        if current_short_count < min_short_count:
            min_short_count = current_short_count
        if current_short_count > max_short_count:
            max_short_count = current_short_count
            max_short_time = time
        current_exposure = current_short_count * position_size
        if current_exposure > max_short_exposure:
            max_short_exposure = current_exposure
    
    # Debug: print max counts
    print(f"DEBUG: Max long count: {max_long_count} (min: {min_long_count}) at {max_long_time}")
    print(f"DEBUG: Max short count: {max_short_count} (min: {min_short_count}) at {max_short_time}")
    print(f"DEBUG: Long events: {len(long_events)}, Short events: {len(short_events)}")
    
    # Debug: Find which trades were active at max times
    if max_long_time:
        overlapping_longs = [t for t in trades if t["direction"] == "B" and t["entry_time"] <= max_long_time < t["exit_time"]]
        print(f"DEBUG: Trades active at max long time (showing all {len(overlapping_longs)}):")
        for i, t in enumerate(overlapping_longs):
            print(f"  Trade {i+1}: entry_idx={t['entry_idx']}, exit_idx={t['exit_idx']}, entry_time={t['entry_time']}, exit_time={t['exit_time']}")
    
    if max_short_time:
        overlapping_shorts = [t for t in trades if t["direction"] == "S" and t["entry_time"] <= max_short_time < t["exit_time"]]
        print(f"DEBUG: Trades active at max short time:")
        for i, t in enumerate(overlapping_shorts[:5]):  # Show first 5
            print(f"  Trade {i+1}: entry_idx={t['entry_idx']}, exit_idx={t['exit_idx']}, entry_time={t['entry_time']}, exit_time={t['exit_time']}")
    
    # Debug: Count active trades at max times
    if max_long_time and max_short_time:
        # Count how many trades were actually active at max_long_time
        active_long_at_max = sum(1 for t in trades if t["direction"] == "B" and t["entry_time"] <= max_long_time < t["exit_time"])
        active_short_at_max_long = sum(1 for t in trades if t["direction"] == "S" and t["entry_time"] <= max_long_time < t["exit_time"])
        print(f"DEBUG: At max long time ({max_long_time}): {active_long_at_max} long, {active_short_at_max_long} short")
        
        # Count how many trades were actually active at max_short_time  
        active_short_at_max = sum(1 for t in trades if t["direction"] == "S" and t["entry_time"] <= max_short_time < t["exit_time"])
        active_long_at_max_short = sum(1 for t in trades if t["direction"] == "B" and t["entry_time"] <= max_short_time < t["exit_time"])
        print(f"DEBUG: At max short time ({max_short_time}): {active_long_at_max_short} long, {active_short_at_max} short")
    
    # Debug: Sample some trades to verify direction
    sample_long = [t for t in trades if t["direction"] == "B"][:3]
    sample_short = [t for t in trades if t["direction"] == "S"][:3]
    print(f"DEBUG: Sample Long (B) trade directions: {[t['direction'] for t in sample_long]}")
    print(f"DEBUG: Sample Short (S) trade directions: {[t['direction'] for t in sample_short]}")
    
    # Calculate summary statistics overall
    total_gross_profit = trades_df["gross_profit_dollars"].sum()
    total_net_profit = trades_df["net_profit_dollars"].sum()
    avg_net_profit = trades_df["net_profit_dollars"].mean()
    avg_profit_pct = trades_df["profit_pct"].mean()
    num_trades = len(trades_df)
    num_winners = (trades_df["net_profit_dollars"] > 0).sum()
    num_losers = (trades_df["net_profit_dollars"] < 0).sum()
    win_rate = num_winners / num_trades if num_trades > 0 else 0.0
    avg_trades_per_day = num_trades / num_days

    # Calculate total return on investment (ROI)
    # Assumes position_size is invested per trade
    total_invested = position_size * num_trades
    gross_roi = (total_gross_profit / total_invested * 100) if total_invested > 0 else 0.0
    net_roi = (total_net_profit / total_invested * 100) if total_invested > 0 else 0.0

    # Calculate Sharpe ratios (gross and net)
    # Sharpe = mean(returns) / std(returns) * sqrt(252)
    # Using profit_pct as gross returns, net_profit_pct as net returns
    # Annualized with sqrt(252) for trading days per year
    std_gross_return = trades_df["profit_pct"].std()
    gross_sharpe_ratio = (avg_profit_pct / std_gross_return * (252 ** 0.5)) if (std_gross_return is not None and std_gross_return > 0) else 0.0
    
    avg_net_profit_pct = trades_df["net_profit_pct"].mean()
    std_net_return = trades_df["net_profit_pct"].std()
    net_sharpe_ratio = (avg_net_profit_pct / std_net_return * (252 ** 0.5)) if (std_net_return is not None and std_net_return > 0) else 0.0

    # Calculate statistics by direction
    long_trades = trades_df.filter(pl.col("direction") == "B")
    short_trades = trades_df.filter(pl.col("direction") == "S")
    
    num_long_trades = len(long_trades)
    num_short_trades = len(short_trades)
    
    # Long trades: gross, fees, net
    gross_long_profit = long_trades["gross_profit_dollars"].sum() if num_long_trades > 0 else 0.0
    long_fees = long_trades["fees"].sum() if num_long_trades > 0 else 0.0
    net_long_profit = long_trades["net_profit_dollars"].sum() if num_long_trades > 0 else 0.0
    
    # Short trades: gross, fees, net
    gross_short_profit = short_trades["gross_profit_dollars"].sum() if num_short_trades > 0 else 0.0
    short_fees = short_trades["fees"].sum() if num_short_trades > 0 else 0.0
    net_short_profit = short_trades["net_profit_dollars"].sum() if num_short_trades > 0 else 0.0
    
    # Calculate total fees
    total_fees = trades_df["fees"].sum()

    summary = {
        "num_trades": num_trades,
        "rejected_up_signals": rejected_up_signals,
        "rejected_down_signals": rejected_down_signals,
        "position_limit": position_limit,
        "num_accounts": num_accounts,
        "fee_rate": fee_rate,
        "total_fees": total_fees,
        "trade_size": position_size,
        "max_long_exposure": max_long_exposure,
        "max_short_exposure": max_short_exposure,
        "num_long_trades": num_long_trades,
        "num_short_trades": num_short_trades,
        # Long trades breakdown
        "gross_long_profit": gross_long_profit,
        "long_fees": long_fees,
        "net_long_profit": net_long_profit,
        # Short trades breakdown
        "gross_short_profit": gross_short_profit,
        "short_fees": short_fees,
        "net_short_profit": net_short_profit,
        # Overall totals
        "gross_profit": total_gross_profit,
        "net_profit": total_net_profit,
        "gross_profit_pct": (total_gross_profit / (position_size * num_trades)) * 100,
        "net_profit_pct": (total_net_profit / (position_size * num_trades)) * 100,
        "gross_roi": gross_roi,
        "net_roi": net_roi,
        "avg_net_profit": avg_net_profit,
        "avg_profit_pct": avg_profit_pct * 100,
        "win_rate": win_rate * 100,
        "num_winners": num_winners,
        "num_losers": num_losers,
        "gross_sharpe_ratio": gross_sharpe_ratio,
        "net_sharpe_ratio": net_sharpe_ratio,
        "date_range": date_range,
        "num_days": num_days,
        "avg_trades_per_day": avg_trades_per_day,
    }

    return trades_df, summary


def plot_cumulative_pnl(trades_df: pl.DataFrame, symbol: str) -> None:
    """
    Plot cumulative PnL over time and save to file.

    Args:
        trades_df: DataFrame with trade results including exit_time and profit_dollars
        symbol: Symbol name for the plot title and filename (e.g., 'btc', 'eth')
    """
    # Sort by exit time to get chronological order
    trades_df = trades_df.sort("exit_time")

    # Calculate cumulative PnL
    trades_df = trades_df.with_columns(
        [pl.col("net_profit_dollars").cum_sum().alias("cumulative_pnl")]
    )

    # Use symbol directly for output
    crypto_name = symbol.lower()

    # Create the plot
    plt.figure(figsize=(12, 6))
    
    # Convert exit_time to list for plotting
    exit_times = trades_df["exit_time"].to_list()
    cum_pnl = trades_df["cumulative_pnl"].to_list()
    
    plt.plot(exit_times, cum_pnl, linewidth=2, color="steelblue")
    plt.axhline(y=0, color="red", linestyle="--", alpha=0.5, linewidth=1)
    
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Cumulative PnL ($)", fontsize=12)
    plt.title(f"Cumulative PnL - {crypto_name.upper()}", fontsize=14, fontweight="bold")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save to file
    output_filename = f"{crypto_name}_cumpnl.png"
    plt.savefig(output_filename, dpi=300, bbox_inches="tight")
    plt.close()
    
    print(f"Cumulative PnL chart saved to: {output_filename}")


def run_simulation(
    df: pl.DataFrame,
    up_threshold: float,
    up_direction: str,
    down_threshold: float,
    down_direction: str,
    detection_window: int,
    hold_window: int,
    position_size: float,
    position_limit: int = 1,
    fee_rate: float = 0.001,
    num_accounts: int = 1,
    verbose: bool = True,
    symbol: str = None,
) -> tuple[pl.DataFrame, dict]:
    """
    Run the complete trading simulation on a DataFrame.

    Args:
        df: Polars DataFrame with kline data (must have 'open_time', 'open', 'close' columns)
        up_threshold: Price movement threshold for UP signal (e.g., 0.01 for 1%)
        up_direction: Trade direction for UP threshold: 'B'=Buy/Long, 'S'=Sell/Short
        down_threshold: Price movement threshold for DOWN signal (e.g., -0.01 for -1%)
        down_direction: Trade direction for DOWN threshold: 'B'=Buy/Long, 'S'=Sell/Short
        detection_window: Number of periods to detect signal over
        hold_window: Number of periods to hold position
        position_size: Dollar amount to invest per trade
        position_limit: Maximum number of concurrent positions allowed (default: 1)
        fee_rate: Transaction fee rate applied to both entry and exit (default: 0.001 = 0.1%)
        num_accounts: Number of accounts (1=single account with position reversal, 2=separate long/short accounts, default: 1)
        verbose: Print results if True
        symbol: Optional symbol name for display purposes (default: None)

    Returns:
        Tuple of (trades DataFrame, summary statistics dict)
    """
    # Validate input DataFrame
    required_columns = ['open_time', 'open', 'close']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"DataFrame missing required columns: {missing_columns}")
    
    if len(df) == 0:
        raise ValueError("DataFrame is empty")

    # Add index column for reference if not present
    if "index" not in df.columns:
        df = df.with_row_index("index")
    
    # Capture data range info
    data_start_date = df["open_time"].min()
    data_end_date = df["open_time"].max()
    num_rows = len(df)

    # Detect signals
    df = detect_signals(df, up_threshold, down_threshold, detection_window)

    # Simulate trades
    trades_df, summary = simulate_trades(df, hold_window, position_size, position_limit, fee_rate, num_accounts, up_direction, down_direction)
    
    # Add data range info to summary
    summary["data_start_date"] = data_start_date
    summary["data_end_date"] = data_end_date
    summary["num_data_rows"] = num_rows

    # Create cumulative PnL plot if we have trades and verbose mode is on
    if len(trades_df) > 0 and symbol and verbose:
        plot_cumulative_pnl(trades_df, symbol)

    if verbose:
        # Count total signals detected
        num_up_signals = df.filter(pl.col("signal_up") == True).height
        num_down_signals = df.filter(pl.col("signal_down") == True).height
        
        print("\n" + "=" * 80)
        print("TRADE SIMULATION RESULTS")
        print("=" * 80)
        if symbol:
            print(f"\nSymbol: {symbol.upper()}")
        print(f"\nParameters:")
        print(f"  Up threshold: {up_threshold:.4f} ({up_threshold*100:.2f}%) → {up_direction} ({'Buy/Long' if up_direction == 'B' else 'Sell/Short'})")
        print(f"  Down threshold: {down_threshold:.4f} ({down_threshold*100:.2f}%) → {down_direction} ({'Buy/Long' if down_direction == 'B' else 'Sell/Short'})")
        print(f"  Detection window: {detection_window} periods")
        print(f"  Hold window: {hold_window} periods")
        print(f"  Position size: ${position_size:,.2f}")
        print(f"  Position limit: {summary['position_limit']} concurrent trades (max exposure: ${summary['position_limit'] * position_size:,.2f})")
        print(f"  Number of accounts: {summary['num_accounts']} {'(position reversal)' if summary['num_accounts'] == 1 else '(separate long/short)'}")
        print(f"  Fee rate: {summary['fee_rate']:.4f} ({summary['fee_rate']*100:.2f}%)")
        print(f"\nSignals Detected:")
        print(f"  UP signals: {num_up_signals}")
        print(f"  DOWN signals: {num_down_signals}")
        print(f"  Total signals: {num_up_signals + num_down_signals}")
        print(f"  Rejected UP (at limit): {summary['rejected_up_signals']}")
        print(f"  Rejected DOWN (at limit): {summary['rejected_down_signals']}")
        print(f"  Total rejected: {summary['rejected_up_signals'] + summary['rejected_down_signals']}")
        print(f"\nTrades Executed:")
        print(f"  Date range: {summary['date_range']}")
        print(f"  Number of days: {summary['num_days']}")
        print(f"  Total trades: {summary['num_trades']}")
        print(f"  Trade size: ${summary['trade_size']:,.2f}")
        print(f"  Max long exposure: ${summary['max_long_exposure']:,.2f}")
        print(f"  Max short exposure: ${summary['max_short_exposure']:,.2f}")
        print(f"\nTrade Breakdown (Gross / Fees / Net):")
        print(f"  Long trades (B): {summary['num_long_trades']}")
        print(f"    Gross profit: ${summary['gross_long_profit']:,.2f}")
        print(f"    Fees paid:    ${summary['long_fees']:,.2f}")
        print(f"    Net profit:   ${summary['net_long_profit']:,.2f}")
        print(f"  Short trades (S): {summary['num_short_trades']}")
        print(f"    Gross profit: ${summary['gross_short_profit']:,.2f}")
        print(f"    Fees paid:    ${summary['short_fees']:,.2f}")
        print(f"    Net profit:   ${summary['net_short_profit']:,.2f}")
        print(f"  Average trades per day: {summary['avg_trades_per_day']:.2f}")
        print(f"\nPerformance Summary:")
        print(f"  Analysis period:")
        print(f"    Start date: {summary['data_start_date']}")
        print(f"    End date:   {summary['data_end_date']}")
        print(f"    Data rows:  {summary['num_data_rows']:,}")
        print(f"  Gross profit:     ${summary['gross_profit']:,.2f}")
        print(f"  Total fees:       ${summary['total_fees']:,.2f}")
        print(f"  Net profit:       ${summary['net_profit']:,.2f}")
        print(f"  Gross profit %:   {summary['gross_profit_pct']:.2f}%")
        print(f"  Net profit %:     {summary['net_profit_pct']:.2f}%")
        print(f"  Gross ROI:        {summary['gross_roi']:.2f}%")
        print(f"  Net ROI:          {summary['net_roi']:.2f}%")
        print(f"  Avg net profit/trade: ${summary['avg_net_profit']:,.2f}")
        print(f"  Avg profit % per trade: {summary['avg_profit_pct']:.2f}%")
        print(f"  Win rate: {summary['win_rate']:.2f}%")
        print(f"  Winners: {summary['num_winners']}")
        print(f"  Losers: {summary['num_losers']}")
        print(f"  Gross Sharpe ratio: {summary['gross_sharpe_ratio']:.4f}")
        print(f"  Net Sharpe ratio:   {summary['net_sharpe_ratio']:.4f}")
        print("=" * 80 + "\n")

    return trades_df, summary


def run_simulation_from_file(
    parquet_file: str,
    start_date: str,
    up_threshold: float,
    up_direction: str,
    down_threshold: float,
    down_direction: str,
    detection_window: int,
    hold_window: int,
    position_size: float,
    position_limit: int = 1,
    fee_rate: float = 0.001,
    num_accounts: int = 1,
    verbose: bool = True,
) -> tuple[pl.DataFrame, dict]:
    """
    Run trading simulation by loading data from a parquet file.
    
    This is a convenience wrapper around run_simulation() that handles file loading
    and date filtering.

    Args:
        parquet_file: Path to parquet file with kline data
        start_date: Start date for simulation (format: 'YYYY-MM-DD')
        up_threshold: Price movement threshold for UP signal (e.g., 0.01 for 1%)
        up_direction: Trade direction for UP threshold: 'B'=Buy/Long, 'S'=Sell/Short
        down_threshold: Price movement threshold for DOWN signal (e.g., -0.01 for -1%)
        down_direction: Trade direction for DOWN threshold: 'B'=Buy/Long, 'S'=Sell/Short
        detection_window: Number of periods to detect signal over
        hold_window: Number of periods to hold position
        position_size: Dollar amount to invest per trade
        position_limit: Maximum number of concurrent positions allowed (default: 1)
        fee_rate: Transaction fee rate applied to both entry and exit (default: 0.001 = 0.1%)
        num_accounts: Number of accounts (1=single account with position reversal, 2=separate long/short accounts, default: 1)
        verbose: Print results if True

    Returns:
        Tuple of (trades DataFrame, summary statistics dict)
    """
    # Load the parquet file
    df = pl.read_parquet(parquet_file)
    
    # Filter by start date if provided
    if start_date:
        # Convert start_date string to datetime for proper comparison
        # Handles both date strings and datetime objects
        if isinstance(start_date, str):
            start_date_dt = pl.lit(start_date).str.strptime(pl.Datetime, "%Y-%m-%d")
            df = df.filter(pl.col("open_time") >= start_date_dt)
        else:
            df = df.filter(pl.col("open_time") >= start_date)
    
    # Extract symbol name from filename (e.g., "btc_klines.parquet" -> "btc")
    parquet_path = Path(parquet_file)
    filename = parquet_path.stem
    symbol = filename.split("_")[0] if "_" in filename else filename
    
    # Run the simulation with the loaded data
    return run_simulation(
        df=df,
        up_threshold=up_threshold,
        up_direction=up_direction,
        down_threshold=down_threshold,
        down_direction=down_direction,
        detection_window=detection_window,
        hold_window=hold_window,
        position_size=position_size,
        position_limit=position_limit,
        fee_rate=fee_rate,
        num_accounts=num_accounts,
        verbose=verbose,
        symbol=symbol,
    )


def multisymbol_simulation(
    symbol_list: list[str],
    data_directory: str,
    up_threshold: float,
    up_direction: str,
    down_threshold: float,
    down_direction: str,
    detection_window: int,
    hold_window: int,
    position_size: float,
    position_limit: int = 1,
    fee_rate: float = 0.001,
    num_accounts: int = 1,
    start_date: str = None,
    verbose: bool = True,
) -> tuple[dict[str, tuple[pl.DataFrame, dict]], dict]:
    """
    Run trading simulation across multiple symbols with the same parameters.

    Args:
        symbol_list: List of symbol names (e.g., ['btc', 'eth', 'sol'])
        data_directory: Path to directory containing parquet files
        up_threshold: Price movement threshold for UP signal (e.g., 0.01 for 1%)
        up_direction: Trade direction for UP threshold: 'B'=Buy/Long, 'S'=Sell/Short
        down_threshold: Price movement threshold for DOWN signal (e.g., -0.01 for -1%)
        down_direction: Trade direction for DOWN threshold: 'B'=Buy/Long, 'S'=Sell/Short
        detection_window: Number of periods to detect signal over
        hold_window: Number of periods to hold position
        position_size: Dollar amount to invest per trade
        position_limit: Maximum number of concurrent positions allowed (default: 1)
        fee_rate: Transaction fee rate applied to both entry and exit (default: 0.001 = 0.1%)
        num_accounts: Number of accounts (1=single account with position reversal, 2=separate long/short accounts, default: 1)
        start_date: Optional start date in YYYY-MM-DD format to filter data (default: None = use all data)
        verbose: Print results if True

    Returns:
        Tuple of:
        - Dictionary mapping symbol -> (trades_df, summary_dict)
        - Aggregated summary statistics across all symbols
    """
    from pathlib import Path
    
    data_dir = Path(data_directory)
    if not data_dir.exists():
        raise ValueError(f"Data directory not found: {data_directory}")
    
    results = {}
    failed_symbols = []
    
    # Aggregate metrics
    total_trades = 0
    total_gross_profit = 0.0
    total_net_profit = 0.0
    total_fees = 0.0
    total_num_winners = 0
    total_num_losers = 0
    all_returns = []
    
    if verbose:
        print("\n" + "=" * 80)
        print("MULTI-SYMBOL SIMULATION")
        print("=" * 80)
        print(f"\nParameters:")
        print(f"  Symbols: {len(symbol_list)}")
        print(f"  UP: {up_threshold:+.4f} → {up_direction}")
        print(f"  DOWN: {down_threshold:+.4f} → {down_direction}")
        print(f"  Detection window: {detection_window} bars")
        print(f"  Hold window: {hold_window} bars")
        print(f"  Position size: ${position_size:,.2f}")
        print(f"  Position limit: {position_limit}")
        print(f"  Fee rate: {fee_rate:.4f} ({fee_rate*100:.2f}%)")
        print(f"  Accounts: {num_accounts}")
        if start_date:
            print(f"  Start date: {start_date}")
        print()
    
    # Run simulation for each symbol
    for i, symbol in enumerate(symbol_list, 1):
        if verbose:
            print(f"[{i}/{len(symbol_list)}] Processing {symbol.upper()}...")
        
        # Find parquet file for this symbol
        pattern = f"{symbol.lower()}_klines*.parquet"
        matching_files = list(data_dir.glob(pattern))
        
        if not matching_files:
            if verbose:
                print(f"  ⚠️  No data file found for {symbol.upper()} (pattern: {pattern})")
            failed_symbols.append(symbol)
            continue
        
        # Use most recent file if multiple exist
        if len(matching_files) > 1:
            matching_files.sort()
            parquet_file = str(matching_files[-1])
            if verbose:
                print(f"  Using: {Path(parquet_file).name}")
        else:
            parquet_file = str(matching_files[0])
        
        try:
            # Run simulation for this symbol
            trades_df, summary = run_simulation_from_file(
                parquet_file,
                start_date,
                up_threshold,
                up_direction,
                down_threshold,
                down_direction,
                detection_window,
                hold_window,
                position_size,
                position_limit,
                fee_rate,
                num_accounts,
                verbose=False  # Suppress individual symbol output
            )
            
            # Store results
            results[symbol] = (trades_df, summary)
            
            # Aggregate metrics
            total_trades += summary["num_trades"]
            total_gross_profit += summary["gross_profit"]
            total_net_profit += summary["net_profit"]
            total_fees += summary["total_fees"]
            total_num_winners += summary["num_winners"]
            total_num_losers += summary["num_losers"]
            
            # Collect individual trade returns for aggregate Sharpe
            if len(trades_df) > 0:
                returns = (trades_df["net_profit_dollars"] / position_size).to_list()
                all_returns.extend(returns)
            
            if verbose:
                print(f"  ✓ {summary['num_trades']} trades, Net PnL: ${summary['net_profit']:,.2f}")
        
        except Exception as e:
            if verbose:
                print(f"  ❌ Error: {str(e)}")
            failed_symbols.append(symbol)
            continue
    
    # Calculate aggregated statistics
    successful_symbols = len(results)
    
    if total_trades > 0:
        aggregate_win_rate = (total_num_winners / total_trades) * 100
        aggregate_avg_net_profit = total_net_profit / total_trades
        
        # Calculate aggregate Sharpe ratio
        if len(all_returns) > 1:
            import statistics
            avg_return = statistics.mean(all_returns)
            std_return = statistics.stdev(all_returns)
            aggregate_sharpe = (avg_return / std_return) if std_return > 0 else 0.0
        else:
            aggregate_sharpe = 0.0
    else:
        aggregate_win_rate = 0.0
        aggregate_avg_net_profit = 0.0
        aggregate_sharpe = 0.0
    
    aggregate_summary = {
        "num_symbols": len(symbol_list),
        "successful_symbols": successful_symbols,
        "failed_symbols": len(failed_symbols),
        "failed_symbol_list": failed_symbols,
        "total_trades": total_trades,
        "total_gross_profit": total_gross_profit,
        "total_net_profit": total_net_profit,
        "total_fees": total_fees,
        "total_num_winners": total_num_winners,
        "total_num_losers": total_num_losers,
        "aggregate_win_rate": aggregate_win_rate,
        "aggregate_avg_net_profit": aggregate_avg_net_profit,
        "aggregate_sharpe_ratio": aggregate_sharpe,
        "avg_trades_per_symbol": total_trades / successful_symbols if successful_symbols > 0 else 0,
        "avg_net_profit_per_symbol": total_net_profit / successful_symbols if successful_symbols > 0 else 0,
    }
    
    if verbose:
        print("\n" + "=" * 80)
        print("AGGREGATE RESULTS")
        print("=" * 80)
        print(f"\nSymbols processed: {successful_symbols}/{len(symbol_list)}")
        if failed_symbols:
            print(f"Failed symbols: {', '.join(failed_symbols)}")
        print(f"\nTotal trades: {total_trades}")
        print(f"Avg trades per symbol: {aggregate_summary['avg_trades_per_symbol']:.1f}")
        print(f"\nGross profit: ${total_gross_profit:,.2f}")
        print(f"Total fees: ${total_fees:,.2f}")
        print(f"Net profit: ${total_net_profit:,.2f}")
        print(f"Avg net profit per symbol: ${aggregate_summary['avg_net_profit_per_symbol']:,.2f}")
        print(f"\nWin rate: {aggregate_win_rate:.2f}%")
        print(f"Winners: {total_num_winners}, Losers: {total_num_losers}")
        print(f"Avg net profit per trade: ${aggregate_avg_net_profit:.2f}")
        print(f"Aggregate Sharpe ratio: {aggregate_sharpe:.3f}")
        print("=" * 80)
    
    return results, aggregate_summary


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Simulate window-based trading strategy with up and down signals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # UP threshold triggers BUY, DOWN threshold triggers SELL
  python window_sim.py BTC 0.01 B -0.01 S 5 5 1000

  # UP threshold triggers SELL (short on strength), DOWN threshold triggers BUY (long on weakness)
  python window_sim.py BTC 0.01 S -0.01 B 5 5 1000

  # Start analysis from November 2024
  python window_sim.py BTC 0.03 B -0.08 S 480 60 1000 --start-date 2024-11-01

  # Full path still works
  python window_sim.py /full/path/to/data.parquet 0.01 B -0.01 S 5 5 1000

  # Save trades to CSV
  python window_sim.py ETH 0.01 B -0.01 S 5 5 1000 --output trades.csv
        """,
    )

    parser.add_argument("symbol", help="Symbol (e.g., BTC, ETH) or full path to parquet file")
    parser.add_argument(
        "up_threshold", type=float, help="Price movement threshold for UP signal (e.g., 0.01 for 1%)"
    )
    parser.add_argument(
        "up_direction", type=str, choices=["B", "S"], help="Trade direction for UP threshold: B=Buy/Long, S=Sell/Short"
    )
    parser.add_argument(
        "down_threshold", type=float, help="Price movement threshold for DOWN signal (e.g., -0.01 for -1%)"
    )
    parser.add_argument(
        "down_direction", type=str, choices=["B", "S"], help="Trade direction for DOWN threshold: B=Buy/Long, S=Sell/Short"
    )
    parser.add_argument(
        "detection_window",
        type=int,
        help="Number of periods to detect signal over",
    )
    parser.add_argument(
        "hold_window", type=int, help="Number of periods to hold position"
    )
    parser.add_argument(
        "position_size", type=float, help="Dollar amount to invest per trade"
    )
    parser.add_argument(
        "--position-limit",
        "-p",
        type=int,
        default=1,
        help="Maximum number of concurrent positions allowed (default: 1)",
    )
    parser.add_argument(
        "--fee-rate",
        "-f",
        type=float,
        default=0.0003,
        help="Transaction fee rate applied to both entry and exit (default: 0.001 = 0.1%%)",
    )
    parser.add_argument(
        "--num-accounts",
        "-n",
        type=int,
        default=1,
        choices=[1, 2],
        help="Number of accounts: 1=single account with position reversal, 2=separate long/short accounts (default: 1)",
    )
    parser.add_argument(
        "--start-date",
        "-s",
        type=str,
        default=None,
        help="Start date for analysis in YYYY-MM-DD format (default: use all data)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Save trades to CSV file",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress output",
    )
    parser.add_argument(
        "--data-dir",
        default="/workspace/data/klines",
        help="Directory containing parquet files (default: /workspace/data/klines)",
    )
    parser.add_argument(
        "--suffix",
        default="USDT",
        help="Suffix to append to symbol (default: USDT)",
    )

    args = parser.parse_args()

    # Construct full path if symbol provided instead of full path
    if args.symbol.endswith('.parquet'):
        # Full path provided
        parquet_file = args.symbol
    else:
        # Symbol provided - construct path
        # Look for files matching pattern: {SYMBOL}{SUFFIX}_1m_*.parquet
        data_dir = Path(args.data_dir)
        symbol_with_suffix = f"{args.symbol}{args.suffix}"
        matching_files = list(data_dir.glob(f"{symbol_with_suffix}_1m_*.parquet"))
        
        if not matching_files:
            parser.error(f"No files found matching pattern: {symbol_with_suffix}_1m_*.parquet in {data_dir}")
        elif len(matching_files) > 1:
            # Use the most recent file (by filename, which includes date range)
            matching_files.sort()
            parquet_file = str(matching_files[-1])
            print(f"Multiple files found, using most recent: {parquet_file}")
        else:
            parquet_file = str(matching_files[0])
    
    # Validate inputs
    if args.up_threshold <= 0:
        parser.error("Up threshold must be positive")
    if args.down_threshold >= 0:
        parser.error("Down threshold must be negative")
    if args.detection_window < 1:
        parser.error("Detection window must be at least 1")
    if args.hold_window < 1:
        parser.error("Hold window must be at least 1")
    if args.position_size <= 0:
        parser.error("Position size must be positive")
    if args.position_limit < 1:
        parser.error("Position limit must be at least 1")
    if args.fee_rate < 0:
        parser.error("Fee rate must be non-negative")
    if not Path(parquet_file).exists():
        parser.error(f"File not found: {parquet_file}")
    
    # Validate start date format if provided
    if args.start_date:
        from datetime import datetime
        try:
            datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            parser.error(f"Invalid start date format: {args.start_date}. Use YYYY-MM-DD format.")

    # Run simulation
    trades_df, summary = run_simulation_from_file(
        parquet_file,
        args.start_date,
        args.up_threshold,
        args.up_direction,
        args.down_threshold,
        args.down_direction,
        args.detection_window,
        args.hold_window,
        args.position_size,
        args.position_limit,
        args.fee_rate,
        args.num_accounts,
        verbose=not args.quiet,
    )

    # Save to CSV if requested
    if args.output and len(trades_df) > 0:
        trades_df.write_csv(args.output)
        print(f"Trades saved to: {args.output}")

    return 0 if summary["num_trades"] > 0 else 1


if __name__ == "__main__":
    exit(main())
