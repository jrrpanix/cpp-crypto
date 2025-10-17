#!/usr/bin/env python3
"""
Debug script to compare gaps before and after repair.
"""

import argparse
from pathlib import Path

import polars as pl


def check_symbol_gaps(parquet_file: Path, symbol: str) -> None:
    """
    Check for gaps in a specific parquet file.
    
    Args:
        parquet_file: Path to the parquet file
        symbol: Symbol name
    """
    print(f"\n{'='*80}")
    print(f"Checking: {symbol}")
    print(f"File: {parquet_file.name}")
    print('='*80)
    
    # Read the file
    df = pl.read_parquet(parquet_file)
    
    # Get date range
    dates = df.select("open_time").sort("open_time")
    start_date = dates[0, 0]
    end_date = dates[-1, 0]
    
    print(f"Date range: {start_date} to {end_date}")
    print(f"Total rows: {len(df):,}")
    
    # Calculate expected rows (1 minute bars)
    time_diff = end_date - start_date
    expected_minutes = int(time_diff.total_seconds() / 60) + 1
    print(f"Expected rows (1-min bars): {expected_minutes:,}")
    print(f"Missing rows: {expected_minutes - len(df):,}")
    
    # Find gaps
    print(f"\nLooking for gaps...")
    
    # Sort by time
    df = df.sort("open_time")
    
    # Calculate time differences (should be 60 seconds for 1-min bars)
    df = df.with_columns([
        (pl.col("open_time").diff().dt.total_seconds() / 60).alias("minutes_gap")
    ])
    
    # Find gaps > 1 minute
    gaps = df.filter(pl.col("minutes_gap") > 1).select(["open_time", "minutes_gap"])
    
    if len(gaps) > 0:
        print(f"\n⚠️  Found {len(gaps)} gap(s):")
        for row in gaps.iter_rows(named=True):
            gap_start = row["open_time"]
            gap_minutes = int(row["minutes_gap"]) - 1
            gap_days = gap_minutes / (60 * 24)
            print(f"   Gap before: {gap_start}")
            print(f"   Duration: {gap_minutes} minutes ({gap_days:.1f} days)")
    else:
        print(f"\n✅ No gaps found! Data is continuous.")


def main():
    """Main function to debug gaps."""
    parser = argparse.ArgumentParser(
        description="Debug gaps in parquet files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check SOLUSDT
  python debug_gaps.py SOLUSDT
  
  # Check AERGOUSDT
  python debug_gaps.py AERGOUSDT
  
  # Use custom klines directory
  python debug_gaps.py SOLUSDT --klines-dir /custom/path
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
        help="Directory containing kline parquet files (default: /workspace/data/klines)"
    )
    
    args = parser.parse_args()
    
    # Find the parquet file
    klines_dir = Path(args.klines_dir)
    symbol = args.symbol.upper()
    
    # Look for files matching the symbol
    matches = list(klines_dir.glob(f"{symbol}_1m_*.parquet"))
    
    if not matches:
        print(f"❌ No parquet file found for {symbol}")
        print(f"   Looked in: {klines_dir}")
        return
    
    if len(matches) > 1:
        print(f"⚠️  Multiple files found for {symbol}:")
        for m in matches:
            print(f"   - {m.name}")
        print(f"\nUsing: {matches[0].name}")
    
    parquet_file = matches[0]
    check_symbol_gaps(parquet_file, symbol)


if __name__ == "__main__":
    main()
