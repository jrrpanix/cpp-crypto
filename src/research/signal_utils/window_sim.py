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
    df: pl.DataFrame, hold_window: int, position_size: float
) -> tuple[pl.DataFrame, dict]:
    """
    Simulate trades based on up and down signals.

    Args:
        df: DataFrame with 'signal_up' and 'signal_down' columns
        hold_window: Number of periods to hold position
        position_size: Dollar amount to invest per trade

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
            "trade_size": position_size,
            "max_long_exposure": 0.0,
            "max_short_exposure": 0.0,
            "num_up_trades": 0,
            "num_down_trades": 0,
            "up_profit": 0.0,
            "down_profit": 0.0,
            "total_profit": 0.0,
            "total_profit_pct": 0.0,
            "total_roi": 0.0,
            "avg_profit": 0.0,
            "avg_profit_pct": 0.0,
            "win_rate": 0.0,
            "num_winners": 0,
            "num_losers": 0,
            "sharpe_ratio": 0.0,
            "date_range": "N/A",
            "num_days": 0,
            "avg_trades_per_day": 0.0,
        }

    trades = []
    
    # Combine and sort all signals by index
    all_signals = []
    for idx in up_signal_indices:
        all_signals.append((idx, "UP"))
    for idx in down_signal_indices:
        all_signals.append((idx, "DOWN"))
    
    # Sort by signal index (chronological order)
    all_signals.sort(key=lambda x: x[0])
    
    # Process every signal - no overlap prevention
    for signal_idx, direction in all_signals:
        # Entry: next bar after signal (signal_idx + 1)
        entry_idx = signal_idx + 1

        # Exit: hold_window bars after entry
        exit_idx = entry_idx + hold_window

        # Check if we have enough data
        if exit_idx >= len(df):
            continue

        # Get entry and exit prices
        entry_row = df.row(entry_idx, named=True)
        exit_row = df.row(exit_idx, named=True)

        entry_price = entry_row["open"]
        exit_price = exit_row["close"]

        if direction == "UP":
            # Calculate profit for long trade (buy low, sell high)
            profit_pct = (exit_price / entry_price) - 1
            profit_dollars = position_size * profit_pct
        else:  # direction == "DOWN"
            # Calculate profit for short trade (sell high, buy low)
            profit_pct = (entry_price / exit_price) - 1
            profit_dollars = position_size * profit_pct

        trades.append(
            {
                "signal_idx": signal_idx,
                "entry_idx": entry_idx,
                "exit_idx": exit_idx,
                "entry_time": entry_row["open_time"],
                "exit_time": exit_row["close_time"],
                "direction": direction,
                "entry_price": entry_price,
                "exit_price": exit_price,
                "profit_pct": profit_pct,
                "profit_dollars": profit_dollars,
                "position_size": position_size,
            }
        )

    if not trades:
        return pl.DataFrame(), {
            "num_trades": 0,
            "trade_size": position_size,
            "max_long_exposure": 0.0,
            "max_short_exposure": 0.0,
            "num_up_trades": 0,
            "num_down_trades": 0,
            "up_profit": 0.0,
            "down_profit": 0.0,
            "total_profit": 0.0,
            "total_profit_pct": 0.0,
            "total_roi": 0.0,
            "avg_profit": 0.0,
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
    long_events = []
    short_events = []
    
    num_up_in_trades = sum(1 for t in trades if t["direction"] == "UP")
    num_down_in_trades = sum(1 for t in trades if t["direction"] == "DOWN")
    print(f"DEBUG PRE: UP trades in list: {num_up_in_trades}, DOWN trades in list: {num_down_in_trades}")
    
    for trade in trades:
        if trade["direction"] == "UP":
            long_events.append((trade["entry_time"], 1))    # Long entry
            long_events.append((trade["exit_time"], -1))    # Long exit
        else:  # DOWN
            short_events.append((trade["entry_time"], 1))   # Short entry
            short_events.append((trade["exit_time"], -1))   # Short exit
    
    print(f"DEBUG POST: Long events created: {len(long_events)}, Short events created: {len(short_events)}")
    print(f"DEBUG POST: Expected long: {num_up_in_trades * 2}, Expected short: {num_down_in_trades * 2}")
    
    # Debug: Count entries vs exits
    long_entries = sum(1 for time, delta in long_events if delta == 1)
    long_exits = sum(1 for time, delta in long_events if delta == -1)
    short_entries = sum(1 for time, delta in short_events if delta == 1)
    short_exits = sum(1 for time, delta in short_events if delta == -1)
    print(f"DEBUG: Long entries: {long_entries}, exits: {long_exits}")
    print(f"DEBUG: Short entries: {short_entries}, exits: {short_exits}")
    
    # Sort events by time, with exits before entries at same time
    long_events.sort(key=lambda x: (x[0], x[1]))
    short_events.sort(key=lambda x: (x[0], x[1]))
    
    # Calculate max long exposure
    max_long_exposure = 0.0
    current_long_count = 0
    max_long_count = 0
    max_long_time = None
    
    # Debug: check for negative counts
    min_long_count = 0
    
    for time, delta in long_events:
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
    
    for time, delta in short_events:
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
    
    # Debug: Count active trades at max times
    if max_long_time and max_short_time:
        # Count how many trades were actually active at max_long_time
        active_long_at_max = sum(1 for t in trades if t["direction"] == "UP" and t["entry_time"] <= max_long_time <= t["exit_time"])
        active_short_at_max_long = sum(1 for t in trades if t["direction"] == "DOWN" and t["entry_time"] <= max_long_time <= t["exit_time"])
        print(f"DEBUG: At max long time ({max_long_time}): {active_long_at_max} long, {active_short_at_max_long} short")
        
        # Count how many trades were actually active at max_short_time  
        active_short_at_max = sum(1 for t in trades if t["direction"] == "DOWN" and t["entry_time"] <= max_short_time <= t["exit_time"])
        active_long_at_max_short = sum(1 for t in trades if t["direction"] == "UP" and t["entry_time"] <= max_short_time <= t["exit_time"])
        print(f"DEBUG: At max short time ({max_short_time}): {active_long_at_max_short} long, {active_short_at_max} short")
    
    # Debug: Sample some trades to verify direction
    sample_up = [t for t in trades if t["direction"] == "UP"][:3]
    sample_down = [t for t in trades if t["direction"] == "DOWN"][:3]
    print(f"DEBUG: Sample UP trade directions: {[t['direction'] for t in sample_up]}")
    print(f"DEBUG: Sample DOWN trade directions: {[t['direction'] for t in sample_down]}")
    
    # Calculate summary statistics overall
    total_profit = trades_df["profit_dollars"].sum()
    avg_profit = trades_df["profit_dollars"].mean()
    avg_profit_pct = trades_df["profit_pct"].mean()
    num_trades = len(trades_df)
    num_winners = (trades_df["profit_dollars"] > 0).sum()
    num_losers = (trades_df["profit_dollars"] < 0).sum()
    win_rate = num_winners / num_trades if num_trades > 0 else 0.0
    avg_trades_per_day = num_trades / num_days

    # Calculate total return on investment (ROI)
    # Assumes position_size is invested per trade
    total_invested = position_size * num_trades
    total_roi = (total_profit / total_invested * 100) if total_invested > 0 else 0.0

    # Calculate Sharpe ratio
    # Sharpe = mean(returns) / std(returns) * sqrt(252)
    # Using profit_pct as returns, annualized with sqrt(252) for trading days per year
    std_return = trades_df["profit_pct"].std()
    sharpe_ratio = (avg_profit_pct / std_return * (252 ** 0.5)) if std_return > 0 else 0.0

    # Calculate statistics by direction
    up_trades = trades_df.filter(pl.col("direction") == "UP")
    down_trades = trades_df.filter(pl.col("direction") == "DOWN")
    
    num_up_trades = len(up_trades)
    num_down_trades = len(down_trades)
    up_profit = up_trades["profit_dollars"].sum() if num_up_trades > 0 else 0.0
    down_profit = down_trades["profit_dollars"].sum() if num_down_trades > 0 else 0.0

    summary = {
        "num_trades": num_trades,
        "trade_size": position_size,
        "max_long_exposure": max_long_exposure,
        "max_short_exposure": max_short_exposure,
        "num_up_trades": num_up_trades,
        "num_down_trades": num_down_trades,
        "up_profit": up_profit,
        "down_profit": down_profit,
        "total_profit": total_profit,
        "total_profit_pct": (total_profit / (position_size * num_trades)) * 100,
        "total_roi": total_roi,
        "avg_profit": avg_profit,
        "avg_profit_pct": avg_profit_pct * 100,
        "win_rate": win_rate * 100,
        "num_winners": num_winners,
        "num_losers": num_losers,
        "sharpe_ratio": sharpe_ratio,
        "date_range": date_range,
        "num_days": num_days,
        "avg_trades_per_day": avg_trades_per_day,
    }

    return trades_df, summary


def plot_cumulative_pnl(trades_df: pl.DataFrame, parquet_file: str) -> None:
    """
    Plot cumulative PnL over time and save to file.

    Args:
        trades_df: DataFrame with trade results including exit_time and profit_dollars
        parquet_file: Original parquet filename, used to extract crypto name for output filename
    """
    # Sort by exit time to get chronological order
    trades_df = trades_df.sort("exit_time")

    # Calculate cumulative PnL
    trades_df = trades_df.with_columns(
        [pl.col("profit_dollars").cum_sum().alias("cumulative_pnl")]
    )

    # Extract crypto name from parquet file
    # Assumes format like "btc_klines.parquet" or path/to/btc_klines.parquet
    parquet_path = Path(parquet_file)
    filename = parquet_path.stem  # Gets filename without extension
    # Try to extract crypto symbol (take first part before underscore or use full name)
    crypto_name = filename.split("_")[0] if "_" in filename else filename

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
    parquet_file: str,
    up_threshold: float,
    down_threshold: float,
    detection_window: int,
    hold_window: int,
    position_size: float,
    verbose: bool = True,
) -> tuple[pl.DataFrame, dict]:
    """
    Run the complete trading simulation.

    Args:
        parquet_file: Path to parquet file with kline data
        up_threshold: Minimum price increase to trigger buy signal (e.g., 0.01 for 1%)
        down_threshold: Maximum price decrease to trigger sell signal (e.g., -0.01 for -1%)
        detection_window: Number of periods to detect signal over
        hold_window: Number of periods to hold position
        position_size: Dollar amount to invest per trade
        verbose: Print results if True

    Returns:
        Tuple of (trades DataFrame, summary statistics dict)
    """
    # Load data
    df = pl.read_parquet(parquet_file)

    # Add index column for reference
    df = df.with_row_index("index")

    # Detect signals
    df = detect_signals(df, up_threshold, down_threshold, detection_window)

    # Simulate trades
    trades_df, summary = simulate_trades(df, hold_window, position_size)

    # Create cumulative PnL plot if we have trades
    if len(trades_df) > 0:
        plot_cumulative_pnl(trades_df, parquet_file)

    if verbose:
        # Count total signals detected
        num_up_signals = df.filter(pl.col("signal_up") == True).height
        num_down_signals = df.filter(pl.col("signal_down") == True).height
        
        print("\n" + "=" * 80)
        print("TRADE SIMULATION RESULTS")
        print("=" * 80)
        print(f"\nParameters:")
        print(f"  Parquet file: {parquet_file}")
        print(f"  Up threshold: {up_threshold:.4f} ({up_threshold*100:.2f}%)")
        print(f"  Down threshold: {down_threshold:.4f} ({down_threshold*100:.2f}%)")
        print(f"  Detection window: {detection_window} periods")
        print(f"  Hold window: {hold_window} periods")
        print(f"  Position size: ${position_size:,.2f}")
        print(f"\nSignals Detected:")
        print(f"  UP signals: {num_up_signals}")
        print(f"  DOWN signals: {num_down_signals}")
        print(f"  Total signals: {num_up_signals + num_down_signals}")
        print(f"\nTrades Executed:")
        print(f"  Date range: {summary['date_range']}")
        print(f"  Number of days: {summary['num_days']}")
        print(f"  Total trades: {summary['num_trades']}")
        print(f"  Trade size: ${summary['trade_size']:,.2f}")
        print(f"  Max long exposure: ${summary['max_long_exposure']:,.2f}")
        print(f"  Max short exposure: ${summary['max_short_exposure']:,.2f}")
        print(f"  UP trades: {summary['num_up_trades']} (profit: ${summary['up_profit']:,.2f})")
        print(f"  DOWN trades: {summary['num_down_trades']} (profit: ${summary['down_profit']:,.2f})")
        print(f"  Average trades per day: {summary['avg_trades_per_day']:.2f}")
        print(f"\nPerformance:")
        print(f"  Total profit: ${summary['total_profit']:,.2f}")
        print(f"  Total profit %: {summary['total_profit_pct']:.2f}%")
        print(f"  Total ROI: {summary['total_roi']:.2f}%")
        print(f"  Average profit per trade: ${summary['avg_profit']:,.2f}")
        print(f"  Average profit % per trade: {summary['avg_profit_pct']:.2f}%")
        print(f"  Win rate: {summary['win_rate']:.2f}%")
        print(f"  Winners: {summary['num_winners']}")
        print(f"  Losers: {summary['num_losers']}")
        print(f"  Sharpe ratio: {summary['sharpe_ratio']:.4f}")
        print("=" * 80 + "\n")

    return trades_df, summary


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Simulate window-based trading strategy with up and down signals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 1% up threshold, -1% down threshold, 5-period detection, 5-period hold, $1000 position
  python window_sim.py data.parquet 0.01 -0.01 5 5 1000

  # Save trades to CSV
  python window_sim.py data.parquet 0.01 -0.01 5 5 1000 --output trades.csv
        """,
    )

    parser.add_argument("parquet_file", help="Path to parquet file with kline data")
    parser.add_argument(
        "up_threshold", type=float, help="Minimum price increase to trigger buy (e.g., 0.01 for 1%)"
    )
    parser.add_argument(
        "down_threshold", type=float, help="Maximum price decrease to trigger sell (e.g., -0.01 for -1%)"
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

    args = parser.parse_args()

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
    if not Path(args.parquet_file).exists():
        parser.error(f"File not found: {args.parquet_file}")

    # Run simulation
    trades_df, summary = run_simulation(
        args.parquet_file,
        args.up_threshold,
        args.down_threshold,
        args.detection_window,
        args.hold_window,
        args.position_size,
        verbose=not args.quiet,
    )

    # Save to CSV if requested
    if args.output and len(trades_df) > 0:
        trades_df.write_csv(args.output)
        print(f"Trades saved to: {args.output}")

    return 0 if summary["num_trades"] > 0 else 1


if __name__ == "__main__":
    exit(main())
