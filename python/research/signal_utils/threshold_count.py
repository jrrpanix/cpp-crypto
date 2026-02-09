#!/usr/bin/env python3
"""
Count threshold events in price data.

Counts how many times the return over a rolling window exceeds a threshold.
- If threshold > 0: counts events where return > threshold (upward movements)
- If threshold < 0: counts events where return < threshold (downward movements)
"""

import argparse
import sys
from pathlib import Path

import polars as pl


def count_threshold_events(
    parquet_file: str,
    threshold: float,
    window: int,
) -> dict:
    """
    Count how many times return over window exceeds threshold.

    Args:
        parquet_file: Path to parquet file with kline data
        threshold: Return threshold (positive for up moves, negative for down moves)
        window: Number of periods for rolling window

    Returns:
        Dictionary with event counts and statistics
    """
    # Load data
    df = pl.read_parquet(parquet_file)

    # Verify required columns
    required_cols = ["open", "close", "open_time", "close_time"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # Calculate return from open N periods ago to current close
    df = df.with_columns(
        [
            pl.col("open").shift(window).alias("window_start_open"),
        ]
    )

    # Calculate rolling window return
    df = df.with_columns(
        [
            ((pl.col("close") - pl.col("window_start_open")) / pl.col("window_start_open")).alias(
                "window_return"
            )
        ]
    )

    # Filter out null values (first N rows won't have window_start_open)
    df = df.filter(pl.col("window_return").is_not_null())

    total_periods = len(df)

    if threshold > 0:
        # Count upward movements exceeding threshold
        events_df = df.filter(pl.col("window_return") > threshold)
        direction = "UP"
    else:
        # Count downward movements below threshold
        events_df = df.filter(pl.col("window_return") < threshold)
        direction = "DOWN"

    num_events = len(events_df)

    # Calculate statistics
    if num_events > 0:
        min_return = events_df["window_return"].min()
        max_return = events_df["window_return"].max()
        avg_return = events_df["window_return"].mean()

        first_time = events_df["open_time"].min()
        last_time = events_df["close_time"].max()
        date_range = f"{first_time} to {last_time}"

        # Calculate time span
        num_days = (last_time - first_time).days if hasattr((last_time - first_time), "days") else 0
        if num_days == 0:
            num_days = 1

        events_per_day = num_events / num_days
    else:
        min_return = 0.0
        max_return = 0.0
        avg_return = 0.0
        date_range = "N/A"
        num_days = 0
        events_per_day = 0.0

    return {
        "parquet_file": parquet_file,
        "threshold": threshold,
        "threshold_pct": threshold * 100,
        "window": window,
        "direction": direction,
        "total_periods": total_periods,
        "num_events": num_events,
        "event_rate": (num_events / total_periods * 100) if total_periods > 0 else 0.0,
        "min_return": min_return,
        "max_return": max_return,
        "avg_return": avg_return,
        "avg_return_pct": avg_return * 100,
        "date_range": date_range,
        "num_days": num_days,
        "events_per_day": events_per_day,
    }


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Count threshold events in price data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Count how many times price went up > 1% over 5 periods
  python threshold_count.py data.parquet 0.01 5

  # Count how many times price went down < -1% over 5 periods
  python threshold_count.py data.parquet -0.01 5

  # Count 2% upward moves over 10 periods
  python threshold_count.py data.parquet 0.02 10
        """,
    )

    parser.add_argument("parquet_file", help="Path to parquet file with kline data")
    parser.add_argument(
        "threshold",
        type=float,
        help="Return threshold (positive for up moves, negative for down moves)",
    )
    parser.add_argument(
        "window",
        type=int,
        help="Number of periods for rolling window",
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Only print event count")

    args = parser.parse_args()

    # Validate inputs
    if args.threshold == 0:
        parser.error("Threshold cannot be zero")
    if args.window < 1:
        parser.error("Window must be at least 1")
    if not Path(args.parquet_file).exists():
        parser.error(f"File not found: {args.parquet_file}")

    try:
        # Count events
        result = count_threshold_events(
            args.parquet_file,
            args.threshold,
            args.window,
        )

        if args.quiet:
            # Just print the count
            print(result["num_events"])
        else:
            # Print detailed report
            print("\n" + "=" * 80)
            print("THRESHOLD EVENT COUNTER")
            print("=" * 80)
            print(f"\nParameters:")
            print(f"  Parquet file: {result['parquet_file']}")
            print(f"  Threshold: {result['threshold']:.4f} ({result['threshold_pct']:.2f}%)")
            print(f"  Window: {result['window']} periods")
            print(f"  Direction: {result['direction']}")
            print(f"\nResults:")
            print(f"  Date range: {result['date_range']}")
            print(f"  Number of days: {result['num_days']}")
            print(f"  Total periods analyzed: {result['total_periods']:,}")
            print(f"  Number of events: {result['num_events']:,}")
            print(f"  Event rate: {result['event_rate']:.2f}%")
            print(f"  Events per day: {result['events_per_day']:.2f}")

            if result["num_events"] > 0:
                print(f"\nEvent Statistics:")
                print(f"  Min return: {result['min_return']:.4f} ({result['min_return']*100:.2f}%)")
                print(f"  Max return: {result['max_return']:.4f} ({result['max_return']*100:.2f}%)")
                print(f"  Avg return: {result['avg_return']:.4f} ({result['avg_return_pct']:.2f}%)")

            print("=" * 80 + "\n")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
