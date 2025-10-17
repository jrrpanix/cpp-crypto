#!/usr/bin/env python3
"""
Debug script to check daily aggregation for a specific symbol.
"""

import argparse
from pathlib import Path

import polars as pl


def check_daily_aggregation(symbol: str, klines_dir: Path, daily_dir: Path) -> None:
    """
    Check if daily aggregation is working correctly for a symbol.
    
    Args:
        symbol: Symbol to check
        klines_dir: Directory with minute-level parquet files
        daily_dir: Directory with daily-level parquet files
    """
    print(f"\n{'='*80}")
    print(f"Checking daily aggregation for: {symbol}")
    print('='*80)
    
    # Find minute-level file
    minute_files = list(klines_dir.glob(f"{symbol}_1m_*.parquet"))
    if not minute_files:
        print(f"❌ No minute-level file found for {symbol}")
        return
    
    minute_file = minute_files[0]
    print(f"\n📊 Minute-level file: {minute_file.name}")
    
    # Read minute data
    minute_df = pl.read_parquet(minute_file)
    print(f"   Rows: {len(minute_df):,}")
    print(f"   Date range: {minute_df['open_time'].min()} to {minute_df['open_time'].max()}")
    
    # Find daily file
    daily_files = list(daily_dir.glob(f"{symbol}_daily_*.parquet"))
    if not daily_files:
        print(f"\n❌ No daily file found for {symbol}")
        print(f"   Run make_daily.py to generate it!")
        return
    
    daily_file = daily_files[0]
    print(f"\n📊 Daily file: {daily_file.name}")
    
    # Read daily data
    daily_df = pl.read_parquet(daily_file)
    print(f"   Rows: {len(daily_df):,}")
    print(f"   Date range: {daily_df['open_time'].min()} to {daily_df['open_time'].max()}")
    
    # Calculate expected daily rows
    minute_start = minute_df['open_time'].min()
    minute_end = minute_df['open_time'].max()
    expected_days = (minute_end - minute_start).days + 1
    
    print(f"\n📈 Comparison:")
    print(f"   Expected daily rows: {expected_days}")
    print(f"   Actual daily rows: {len(daily_df)}")
    
    if len(daily_df) == expected_days:
        print(f"   ✅ Daily aggregation looks correct!")
    else:
        print(f"   ⚠️  Missing {expected_days - len(daily_df)} days")
    
    # Check for gaps in daily data
    daily_sorted = daily_df.sort("open_time")
    daily_sorted = daily_sorted.with_columns([
        pl.col("open_time").diff().dt.total_days().alias("days_gap")
    ])
    
    gaps = daily_sorted.filter(pl.col("days_gap") > 1).select(["open_time", "days_gap"])
    
    if len(gaps) > 0:
        print(f"\n⚠️  Found {len(gaps)} gap(s) in daily data:")
        for row in gaps.iter_rows(named=True):
            gap_date = row["open_time"]
            gap_days = int(row["days_gap"]) - 1
            print(f"   Gap before: {gap_date.date()} ({gap_days} days)")
    else:
        print(f"\n✅ No gaps in daily data!")
    
    # Show sample of daily data
    print(f"\n📋 Sample daily data (first 5 rows):")
    print(daily_df.select(["open_time", "open", "high", "low", "close", "volume"]).head(5))


def main():
    """Main function to debug daily aggregation."""
    parser = argparse.ArgumentParser(
        description="Debug daily aggregation for a symbol.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check SOLUSDT
  python debug_daily.py SOLUSDT
  
  # Check AERGOUSDT
  python debug_daily.py AERGOUSDT
  
  # Use custom directories
  python debug_daily.py SOLUSDT --klines-dir /custom/klines --daily-dir /custom/daily
        """
    )
    parser.add_argument(
        "symbol",
        type=str,
        help="Symbol to check (e.g., SOLUSDT, AERGOUSDT)"
    )
    parser.add_argument(
        "--klines-dir",
        type=str,
        default="/workspace/data/klines",
        help="Directory containing minute-level parquet files (default: /workspace/data/klines)"
    )
    parser.add_argument(
        "--daily-dir",
        type=str,
        default="/workspace/data/klines_daily",
        help="Directory containing daily parquet files (default: /workspace/data/klines_daily)"
    )
    
    args = parser.parse_args()
    
    klines_dir = Path(args.klines_dir)
    daily_dir = Path(args.daily_dir)
    symbol = args.symbol.upper()
    
    check_daily_aggregation(symbol, klines_dir, daily_dir)


if __name__ == "__main__":
    main()
