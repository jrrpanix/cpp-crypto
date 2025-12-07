#!/usr/bin/env python3
"""
Daily-based trade simulator using polars.

Simulates a trading strategy based on daily price movements.
If price increases by threshold within detection_window days, enters a position
and holds for hold_window days.

Similar to window_sim.py but operates on daily aggregated data instead of minute bars.
This is useful for:
- Longer-term trading strategies
- Easier identification of trends in low-liquidity coins
- Lower data processing requirements
- Strategic analysis rather than tactical execution
"""

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl


def calculate_returns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Calculate returns for each day.

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
    Detect when price change exceeds thresholds within detection window (days).
    
    For each day, calculates return from the open of the day detection_window periods ago
    to the close of the current day. Signals when this return exceeds threshold.

    Args:
        df: DataFrame with 'open_time', 'open', and 'close' columns
        up_threshold: Minimum return to trigger buy signal (e.g., 0.05 for 5%)
        down_threshold: Maximum return to trigger sell signal (e.g., -0.05 for -5%)
        detection_window: Number of days to look back (e.g., 5 means compare current close to open from 5 days ago)

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
    df: pl.DataFrame, 
    hold_window: int, 
    position_size: float, 
    position_limit: int = 1, 
    fee_rate: float = 0.001, 
    num_accounts: int = 1, 
    up_direction: str = "B", 
    down_direction: str = "S"
) -> tuple[pl.DataFrame, dict]:
    """
    Simulate trades based on up and down signals.

    Args:
        df: DataFrame with 'signal_up' and 'signal_down' columns
        hold_window: Number of days to hold position
        position_size: Dollar amount to invest per trade
        position_limit: Maximum number of concurrent positions allowed
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
    
    # Track open positions
    open_positions = []
    
    # Process every signal with position limit enforcement
    for signal_idx, signal_type, trade_direction in all_signals:
        # Entry: next day after signal
        entry_idx = signal_idx + 1

        # Exit: hold_window days after entry
        exit_idx = entry_idx + hold_window

        # Check if we have enough data
        if exit_idx >= len(df):
            continue

        if num_accounts == 1:
            # Single account logic: close opposite positions and reverse
            open_positions = [(e_idx, x_idx, d, e_date, x_date) for e_idx, x_idx, d, e_date, x_date in open_positions if x_idx > entry_idx]
            
            # Check if we have opposite direction positions
            opposite_direction = "S" if trade_direction == "B" else "B"
            opposite_positions = [p for p in open_positions if p[2] == opposite_direction]
            same_direction_positions = [p for p in open_positions if p[2] == trade_direction]
            
            if opposite_positions:
                # Close opposite positions and reverse
                for opp_entry_idx, opp_exit_idx, opp_dir, opp_entry_date, opp_exit_date in opposite_positions:
                    for trade in trades:
                        if (trade["entry_idx"] == opp_entry_idx and 
                            trade["direction"] == opp_dir and
                            trade["exit_idx"] == opp_exit_idx):
                            # Update to early exit
                            entry_row_for_early = df.row(entry_idx, named=True)
                            early_exit_price = entry_row_for_early["open"]
                            
                            # Get original entry price
                            opp_entry_row = df.row(opp_entry_idx, named=True)
                            opp_entry_price = opp_entry_row["open"]
                            
                            # Calculate fees
                            entry_fee = position_size * fee_rate
                            exit_fee = position_size * fee_rate
                            total_fees = entry_fee + exit_fee
                            
                            if opp_dir == "B":
                                profit_pct = (early_exit_price / opp_entry_price) - 1
                                gross_profit_dollars = position_size * profit_pct
                                net_profit_dollars = gross_profit_dollars - total_fees
                                net_profit_pct = net_profit_dollars / position_size
                            else:  # "S" - Short trade
                                profit_pct = (opp_entry_price / early_exit_price) - 1
                                gross_profit_dollars = position_size * profit_pct
                                net_profit_dollars = gross_profit_dollars - total_fees
                                net_profit_pct = net_profit_dollars / position_size
                            
                            # Update the existing trade record
                            trade["exit_idx"] = entry_idx
                            trade["exit_time"] = entry_row_for_early["open_time"]
                            trade["exit_price"] = early_exit_price
                            trade["profit_pct"] = profit_pct
                            trade["net_profit_pct"] = net_profit_pct
                            trade["gross_profit_dollars"] = gross_profit_dollars
                            trade["fees"] = total_fees
                            trade["net_profit_dollars"] = net_profit_dollars
                            break
                
                # Remove all opposite positions
                open_positions = same_direction_positions
            else:
                open_positions = same_direction_positions
            
            # Check position limit for same direction
            same_direction_positions = [p for p in open_positions if p[2] == trade_direction]
            if len(same_direction_positions) >= position_limit:
                if signal_type == "UP":
                    rejected_up_signals += 1
                else:
                    rejected_down_signals += 1
                continue
        else:
            # num_accounts == 2: separate long and short accounts
            open_positions = [(e_idx, x_idx, d, e_date, x_date) for e_idx, x_idx, d, e_date, x_date in open_positions if x_idx > entry_idx]
            
            # Check position limit for this direction
            same_direction_positions = [p for p in open_positions if p[2] == trade_direction]
            if len(same_direction_positions) >= position_limit:
                if signal_type == "UP":
                    rejected_up_signals += 1
                else:
                    rejected_down_signals += 1
                continue

        # Enter position
        entry_row = df.row(entry_idx, named=True)
        exit_row = df.row(exit_idx, named=True)

        entry_price = entry_row["open"]
        exit_price = exit_row["open"]
        entry_time = entry_row["open_time"]
        exit_time = exit_row["open_time"]

        # Calculate fees
        entry_fee = position_size * fee_rate
        exit_fee = position_size * fee_rate
        total_fees = entry_fee + exit_fee

        # Calculate profit
        if trade_direction == "B":
            # Long trade: profit = (exit - entry) / entry
            profit_pct = (exit_price / entry_price) - 1
            gross_profit_dollars = position_size * profit_pct
            net_profit_dollars = gross_profit_dollars - total_fees
            net_profit_pct = net_profit_dollars / position_size
        else:  # "S" - Short trade
            # Short trade: profit = (entry - exit) / entry
            profit_pct = (entry_price / exit_price) - 1
            gross_profit_dollars = position_size * profit_pct
            net_profit_dollars = gross_profit_dollars - total_fees
            net_profit_pct = net_profit_dollars / position_size

        trade_record = {
            "entry_idx": entry_idx,
            "exit_idx": exit_idx,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "direction": trade_direction,
            "position_size": position_size,
            "profit_pct": profit_pct,
            "gross_profit_dollars": gross_profit_dollars,
            "fees": total_fees,
            "net_profit_dollars": net_profit_dollars,
            "net_profit_pct": net_profit_pct,
            "signal_type": signal_type,
        }
        
        trades.append(trade_record)
        open_positions.append((entry_idx, exit_idx, trade_direction, entry_time, exit_time))

    # Calculate summary statistics
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

    trades_df = pl.DataFrame(trades)

    # Calculate statistics
    num_trades = len(trades)
    long_trades = [t for t in trades if t["direction"] == "B"]
    short_trades = [t for t in trades if t["direction"] == "S"]
    
    num_long_trades = len(long_trades)
    num_short_trades = len(short_trades)
    
    # Long statistics
    gross_long_profit = sum(t["gross_profit_dollars"] for t in long_trades)
    long_fees = sum(t["fees"] for t in long_trades)
    net_long_profit = sum(t["net_profit_dollars"] for t in long_trades)
    
    # Short statistics
    gross_short_profit = sum(t["gross_profit_dollars"] for t in short_trades)
    short_fees = sum(t["fees"] for t in short_trades)
    net_short_profit = sum(t["net_profit_dollars"] for t in short_trades)
    
    # Overall statistics
    gross_profit = gross_long_profit + gross_short_profit
    total_fees = long_fees + short_fees
    net_profit = net_long_profit + net_short_profit
    
    total_capital_deployed = num_trades * position_size
    gross_profit_pct = (gross_profit / total_capital_deployed * 100) if total_capital_deployed > 0 else 0.0
    net_profit_pct = (net_profit / total_capital_deployed * 100) if total_capital_deployed > 0 else 0.0
    
    # ROI as percentage of initial capital (one position_size)
    gross_roi = (gross_profit / position_size * 100) if position_size > 0 else 0.0
    net_roi = (net_profit / position_size * 100) if position_size > 0 else 0.0
    
    avg_net_profit = net_profit / num_trades if num_trades > 0 else 0.0
    avg_profit_pct = trades_df.select(pl.col("net_profit_pct").mean()).item() * 100
    
    # Win rate
    winners = trades_df.filter(pl.col("net_profit_dollars") > 0)
    num_winners = len(winners)
    num_losers = num_trades - num_winners
    win_rate = (num_winners / num_trades * 100) if num_trades > 0 else 0.0
    
    # Sharpe ratio (annualized, assuming 252 trading days)
    returns = trades_df.select(pl.col("net_profit_pct")).to_series()
    mean_return = returns.mean()
    std_return = returns.std()
    gross_returns = trades_df.select(pl.col("profit_pct")).to_series()
    gross_mean_return = gross_returns.mean()
    gross_std_return = gross_returns.std()
    
    # Annualize (252 trading days per year)
    gross_sharpe_ratio = (gross_mean_return * 252 / gross_std_return) if gross_std_return > 0 else 0.0
    net_sharpe_ratio = (mean_return * 252 / std_return) if std_return > 0 else 0.0
    
    # Date range
    first_time = df.row(0, named=True)["open_time"]
    last_time = df.row(len(df) - 1, named=True)["open_time"]
    date_range = f"{first_time} to {last_time}"
    num_days = len(df)
    avg_trades_per_day = num_trades / num_days if num_days > 0 else 0.0
    
    # Max exposure (concurrent positions)
    max_long_exposure = max([sum(1 for p in open_positions if p[2] == "B") for open_positions in [[]]] + 
                           [position_limit]) * position_size
    max_short_exposure = max([sum(1 for p in open_positions if p[2] == "S") for open_positions in [[]]] + 
                            [position_limit]) * position_size

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
        "gross_long_profit": gross_long_profit,
        "long_fees": long_fees,
        "net_long_profit": net_long_profit,
        "gross_short_profit": gross_short_profit,
        "short_fees": short_fees,
        "net_short_profit": net_short_profit,
        "gross_profit": gross_profit,
        "net_profit": net_profit,
        "gross_profit_pct": gross_profit_pct,
        "net_profit_pct": net_profit_pct,
        "gross_roi": gross_roi,
        "net_roi": net_roi,
        "avg_net_profit": avg_net_profit,
        "avg_profit_pct": avg_profit_pct,
        "win_rate": win_rate,
        "num_winners": num_winners,
        "num_losers": num_losers,
        "gross_sharpe_ratio": gross_sharpe_ratio,
        "net_sharpe_ratio": net_sharpe_ratio,
        "date_range": date_range,
        "num_days": num_days,
        "avg_trades_per_day": avg_trades_per_day,
    }

    return trades_df, summary


def run_simulation_from_file(
    file_path: str,
    start_date: str | None,
    up_threshold: float,
    down_threshold: float,
    detection_window: int,
    hold_window: int,
    position_size: float,
    position_limit: int = 1,
    fee_rate: float = 0.001,
    num_accounts: int = 1,
    up_direction: str = "B",
    down_direction: str = "S",
) -> tuple[pl.DataFrame, dict]:
    """
    Run simulation from a daily data parquet file.

    Args:
        file_path: Path to parquet file with daily data (can be single file or pattern)
        start_date: Optional start date filter (YYYY-MM-DD)
        up_threshold: Minimum return to trigger buy signal
        down_threshold: Maximum return to trigger sell signal
        detection_window: Number of days to look back for signal detection
        hold_window: Number of days to hold position
        position_size: Dollar amount per trade
        position_limit: Maximum concurrent positions
        fee_rate: Transaction fee rate
        num_accounts: 1 or 2 accounts
        up_direction: 'B' for long, 'S' for short on up signal
        down_direction: 'B' for long, 'S' for short on down signal

    Returns:
        Tuple of (trades DataFrame, summary dict)
    """
    # Load daily data - if pattern provided, load all matching files
    file_path_obj = Path(file_path)
    if '*' in file_path or not file_path_obj.exists():
        # Pattern or missing file - try glob pattern
        parent_dir = file_path_obj.parent
        pattern = file_path_obj.name
        matching_files = sorted(parent_dir.glob(pattern))
        
        if not matching_files:
            raise FileNotFoundError(f"No files found matching pattern: {file_path}")
        
        # Load and concatenate all matching files
        dfs = [pl.read_parquet(str(f)) for f in matching_files]
        df = pl.concat(dfs)
        
        # Sort by open_time and remove duplicates
        df = df.sort("open_time").unique(subset=["open_time"], keep="last")
    else:
        # Single file
        df = pl.read_parquet(file_path)
    
    # Filter by start date if provided
    if start_date:
        # Convert string date to datetime for proper comparison
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        df = df.filter(pl.col("open_time") >= start_dt)
    
    # Add index column for tracking
    df = df.with_row_index("index")
    
    # Calculate returns
    df = calculate_returns(df)
    
    # Detect signals
    df = detect_signals(df, up_threshold, down_threshold, detection_window)
    
    # Simulate trades
    trades_df, summary = simulate_trades(
        df,
        hold_window,
        position_size,
        position_limit,
        fee_rate,
        num_accounts,
        up_direction,
        down_direction,
    )
    
    return trades_df, summary


def print_summary(summary: dict, symbol: str = ""):
    """Print simulation summary statistics."""
    print(f"\n{'='*70}")
    print(f"SIMULATION SUMMARY{' - ' + symbol if symbol else ''}")
    print(f"{'='*70}")
    print(f"Date Range: {summary['date_range']}")
    print(f"Number of Days: {summary['num_days']}")
    print(f"\nStrategy Parameters:")
    print(f"  Position Limit: {summary['position_limit']}")
    print(f"  Number of Accounts: {summary['num_accounts']}")
    print(f"  Fee Rate: {summary['fee_rate']:.4%}")
    print(f"  Trade Size: ${summary['trade_size']:,.2f}")
    print(f"\nTrade Statistics:")
    print(f"  Total Trades: {summary['num_trades']}")
    print(f"  Long Trades: {summary['num_long_trades']}")
    print(f"  Short Trades: {summary['num_short_trades']}")
    print(f"  Rejected Up Signals: {summary['rejected_up_signals']}")
    print(f"  Rejected Down Signals: {summary['rejected_down_signals']}")
    print(f"  Avg Trades/Day: {summary['avg_trades_per_day']:.3f}")
    print(f"\nPerformance Metrics:")
    print(f"  Win Rate: {summary['win_rate']:.2f}%")
    print(f"  Winners: {summary['num_winners']}")
    print(f"  Losers: {summary['num_losers']}")
    print(f"\nProfit & Loss (Gross):")
    print(f"  Long Profit: ${summary['gross_long_profit']:,.2f}")
    print(f"  Short Profit: ${summary['gross_short_profit']:,.2f}")
    print(f"  Total Gross Profit: ${summary['gross_profit']:,.2f}")
    print(f"  Gross ROI: {summary['gross_roi']:.2f}%")
    print(f"  Gross Profit %: {summary['gross_profit_pct']:.2f}%")
    print(f"  Gross Sharpe Ratio: {summary['gross_sharpe_ratio']:.3f}")
    print(f"\nProfit & Loss (Net of Fees):")
    print(f"  Total Fees: ${summary['total_fees']:,.2f}")
    print(f"  Long Fees: ${summary['long_fees']:,.2f}")
    print(f"  Short Fees: ${summary['short_fees']:,.2f}")
    print(f"  Long Net Profit: ${summary['net_long_profit']:,.2f}")
    print(f"  Short Net Profit: ${summary['net_short_profit']:,.2f}")
    print(f"  Total Net Profit: ${summary['net_profit']:,.2f}")
    print(f"  Net ROI: {summary['net_roi']:.2f}%")
    print(f"  Net Profit %: {summary['net_profit_pct']:.2f}%")
    print(f"  Avg Net Profit/Trade: ${summary['avg_net_profit']:,.2f}")
    print(f"  Avg Profit % /Trade: {summary['avg_profit_pct']:.2f}%")
    print(f"  Net Sharpe Ratio: {summary['net_sharpe_ratio']:.3f}")
    print(f"\nExposure:")
    print(f"  Max Long Exposure: ${summary['max_long_exposure']:,.2f}")
    print(f"  Max Short Exposure: ${summary['max_short_exposure']:,.2f}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Daily trade simulator - simulates trades based on daily price movements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic long-only strategy: buy when price up 10% in 5 days, hold for 10 days
  uv run python %(prog)s MYXUSDT --up-threshold 0.10 --down-threshold -999 \\
    --detection-window 5 --hold-window 10 --position-size 10000

  # Mean reversion: short after 15% up in 3 days, cover after 5 days
  uv run python %(prog)s BTCUSDT --up-threshold 0.15 --up-direction S \\
    --detection-window 3 --hold-window 5 --position-size 10000

  # Momentum: long breakouts, hold longer
  uv run python %(prog)s ETHUSDT --up-threshold 0.20 --down-threshold -999 \\
    --detection-window 7 --hold-window 30 --position-size 10000

  # Two-way trading: long on 10% up, short on 10% down
  uv run python %(prog)s SOLUSDT --up-threshold 0.10 --down-threshold -0.10 \\
    --detection-window 5 --hold-window 10 --position-size 10000 --num-accounts 2

Default directories:
  Daily data: /workspace/data/klines_daily/{SYMBOL}_daily_*.parquet
  Note: Script automatically finds and uses the most recent file matching the symbol
        """,
    )
    parser.add_argument("symbol", help="Symbol to backtest (e.g., BTCUSDT) or full path to parquet file")
    parser.add_argument(
        "--up-threshold",
        "-u",
        type=float,
        default=0.05,
        help="Minimum return to trigger up signal (default: 0.05 = 5%%)",
    )
    parser.add_argument(
        "--down-threshold",
        "-d",
        type=float,
        default=-999.0,
        help="Maximum return to trigger down signal (default: -999 = disabled)",
    )
    parser.add_argument(
        "--detection-window",
        "-w",
        type=int,
        default=5,
        help="Number of days to look back for signal detection (default: 5)",
    )
    parser.add_argument(
        "--hold-window",
        "-H",
        type=int,
        default=10,
        help="Number of days to hold position (default: 10)",
    )
    parser.add_argument(
        "--position-size",
        "-p",
        type=float,
        default=10000.0,
        help="Dollar amount per trade (default: 10000)",
    )
    parser.add_argument(
        "--up-direction",
        choices=["B", "S"],
        default="B",
        help="Trade direction for UP threshold: B=Buy/Long, S=Sell/Short (default: B)",
    )
    parser.add_argument(
        "--down-direction",
        choices=["B", "S"],
        default="S",
        help="Trade direction for DOWN threshold: B=Buy/Long, S=Sell/Short (default: S)",
    )
    parser.add_argument(
        "--position-limit",
        "-l",
        type=int,
        default=1,
        help="Maximum number of concurrent positions allowed (default: 1)",
    )
    parser.add_argument(
        "--fee-rate",
        "-f",
        type=float,
        default=0.001,
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
        default="/workspace/data/klines_daily",
        help="Directory containing daily parquet files (default: /workspace/data/klines_daily)",
    )

    args = parser.parse_args()

    # Construct full path if symbol provided instead of full path
    if args.symbol.endswith('.parquet'):
        # Full path provided
        parquet_file = args.symbol
    else:
        # Symbol provided - find matching file with wildcard pattern
        data_dir = Path(args.data_dir)
        pattern = f"{args.symbol}_daily_*.parquet"
        matching_files = sorted(data_dir.glob(pattern))
        
        if not matching_files:
            parser.error(f"No files found matching pattern: {data_dir / pattern}")
        
        # Use the most recent file (last in sorted list)
        parquet_file = str(matching_files[-1])
    
    # Validate inputs
    if args.up_threshold <= 0 and args.down_threshold >= 0:
        parser.error("At least one threshold must be enabled (up_threshold > 0 or down_threshold < 0)")
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
        args.down_threshold,
        args.detection_window,
        args.hold_window,
        args.position_size,
        args.position_limit,
        args.fee_rate,
        args.num_accounts,
        args.up_direction,
        args.down_direction,
    )

    # Print summary
    if not args.quiet:
        symbol_name = args.symbol if not args.symbol.endswith('.parquet') else Path(args.symbol).stem
        print_summary(summary, symbol_name)

        if len(trades_df) > 0:
            print("\nFirst 10 trades:")
            print(trades_df.head(10))

    # Save trades if requested
    if args.output and len(trades_df) > 0:
        trades_df.write_csv(args.output)
        print(f"\nTrades saved to: {args.output}")


if __name__ == "__main__":
    main()
