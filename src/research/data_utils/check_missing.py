#!/usr/bin/env python3
"""
Check for gaps in daily data from aggregated parquet files.

This utility reads the aggregate file and identifies missing months
or date ranges for each symbol.
"""

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple

import polars as pl


def find_aggregate_file(aggregate_dir: Path) -> Path:
    """
    Find the aggregate parquet file in the directory.
    
    Args:
        aggregate_dir: Directory containing aggregate files
        
    Returns:
        Path to the aggregate file
        
    Raises:
        FileNotFoundError: If no aggregate file is found
    """
    files = list(aggregate_dir.glob("AGG_*.pq"))
    
    if not files:
        raise FileNotFoundError(f"No AGG_*.pq file found in {aggregate_dir}")
    
    if len(files) > 1:
        print(f"⚠️  Warning: Multiple AGG files found, using: {files[0].name}")
    
    return files[0]


def get_missing_months(dates: List[datetime]) -> List[Tuple[str, str]]:
    """
    Find missing months in a list of dates.
    
    Args:
        dates: List of datetime objects (should be sorted)
        
    Returns:
        List of tuples (start_month, end_month) representing gaps
    """
    if len(dates) < 2:
        return []
    
    gaps = []
    
    for i in range(len(dates) - 1):
        current_date = dates[i]
        next_date = dates[i + 1]
        
        # Calculate expected next date (next day)
        expected_next = current_date + timedelta(days=1)
        
        # If gap is more than 1 day, we have missing data
        gap_days = (next_date - current_date).days
        if gap_days > 1:
            gap_start = expected_next
            gap_end = next_date - timedelta(days=1)
            
            # Format as YYYY-MM for monthly gaps
            start_month = gap_start.strftime("%Y-%m")
            end_month = gap_end.strftime("%Y-%m")
            
            gaps.append((gap_start.strftime("%Y-%m-%d"), gap_end.strftime("%Y-%m-%d"), gap_days - 1))
    
    return gaps


def get_missing_data(aggregate_file: Path, symbol_filter: str = None) -> dict:
    """
    Get missing data gaps for all symbols in the aggregate file.
    
    This function can be imported and used by other scripts like download_missing.py.
    
    Args:
        aggregate_file: Path to aggregate parquet file
        symbol_filter: Optional prefix to filter symbols (e.g., "BTC" for all BTC* symbols)
        
    Returns:
        Dictionary with structure:
        {
            "symbol": {
                "start_date": "YYYY-MM-DD",
                "end_date": "YYYY-MM-DD",
                "expected_days": int,
                "actual_days": int,
                "missing_days": int,
                "gaps": [
                    {
                        "start": "YYYY-MM-DD",
                        "end": "YYYY-MM-DD",
                        "days": int,
                        "months": int
                    },
                    ...
                ]
            },
            ...
        }
    """
    # Read the parquet file
    df = pl.read_parquet(aggregate_file)
    
    # Filter symbols if requested
    if symbol_filter:
        df = df.filter(pl.col("symbol").str.starts_with(symbol_filter.upper()))
    
    # Get unique symbols
    symbols = sorted(df.select("symbol").unique()["symbol"].to_list())
    
    result = {}
    
    for symbol in symbols:
        # Get data for this symbol
        symbol_df = df.filter(pl.col("symbol") == symbol).sort("open_time")
        
        # Extract dates
        dates = [dt.date() if hasattr(dt, 'date') else dt for dt in symbol_df["open_time"].to_list()]
        
        # Get date range
        start_date = dates[0]
        end_date = dates[-1]
        expected_days = (end_date - start_date).days + 1
        actual_days = len(dates)
        
        # Find gaps
        gaps = get_missing_months(dates)
        
        # Build result for this symbol
        symbol_info = {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "expected_days": expected_days,
            "actual_days": actual_days,
            "missing_days": expected_days - actual_days,
            "gaps": []
        }
        
        for gap_start, gap_end, gap_days in gaps:
            # Calculate number of months
            start_dt = datetime.strptime(gap_start, "%Y-%m-%d")
            end_dt = datetime.strptime(gap_end, "%Y-%m-%d")
            months_diff = (end_dt.year - start_dt.year) * 12 + end_dt.month - start_dt.month + 1
            
            symbol_info["gaps"].append({
                "start": gap_start,
                "end": gap_end,
                "days": gap_days,
                "months": months_diff
            })
        
        result[symbol] = symbol_info
    
    return result


def check_missing_data(aggregate_file: Path, show_clean: bool = False, symbol_filter: str = None) -> None:
    """
    Check for missing data in the aggregate file and print report.
    
    Args:
        aggregate_file: Path to aggregate parquet file
        show_clean: If True, also show symbols with no gaps
        symbol_filter: Optional prefix to filter symbols (e.g., "BTC" for all BTC* symbols)
    """
    print(f"Reading data from: {aggregate_file.name}\n")
    
    # Get missing data using the library function
    try:
        missing_data = get_missing_data(aggregate_file, symbol_filter)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    # Calculate totals for header
    total_symbols = len(missing_data)
    symbols_with_gaps = [s for s, info in missing_data.items() if info["gaps"]]
    clean_symbols = [s for s, info in missing_data.items() if not info["gaps"]]
    
    print(f"Total symbols: {total_symbols}")
    if symbol_filter:
        print(f"Filtered to symbols starting with '{symbol_filter.upper()}'")
    
    print("\n" + "="*80)
    print("CHECKING FOR DATA GAPS")
    print("="*80 + "\n")
    
    # Print symbols with gaps
    for symbol in symbols_with_gaps:
        info = missing_data[symbol]
        print(f"📊 {symbol}")
        print(f"   Period: {info['start_date']} to {info['end_date']}")
        print(f"   Days: {info['actual_days']} / {info['expected_days']} expected ({info['actual_days']/info['expected_days']*100:.1f}%)")
        print(f"   Missing: {info['missing_days']} days")
        print(f"   Gaps found: {len(info['gaps'])}")
        
        for gap in info["gaps"]:
            if gap["months"] > 1:
                print(f"      ⚠️  {gap['start']} to {gap['end']} ({gap['days']} days, ~{gap['months']} months)")
            else:
                print(f"      • {gap['start']} to {gap['end']} ({gap['days']} days)")
        
        print()
    
    # Summary
    print("="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\nSymbols with gaps: {len(symbols_with_gaps)} / {total_symbols}")
    print(f"Clean symbols: {len(clean_symbols)} / {total_symbols}")
    
    if symbols_with_gaps:
        print(f"\n⚠️  Symbols with data gaps:")
        for symbol in symbols_with_gaps:
            print(f"   - {symbol}")
    
    if show_clean and clean_symbols:
        print(f"\n✅ Clean symbols (no gaps):")
        for symbol in clean_symbols:
            print(f"   - {symbol}")


def main():
    """Main function to check for missing data."""
    parser = argparse.ArgumentParser(
        description="Check for gaps in daily data from aggregated parquet files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check all symbols for gaps
  python check_missing.py
  
  # Check only SOL symbols
  python check_missing.py --symbol SOL
  
  # Check BTC symbols and show clean ones too
  python check_missing.py --symbol BTC --show-clean
  
  # Use custom aggregate directory
  python check_missing.py --aggregate-dir /workspace/data/klines_aggregate
        """
    )
    parser.add_argument(
        "--aggregate-dir",
        type=str,
        default="/workspace/data/klines_aggregate",
        help="Directory containing aggregate parquet files (default: /workspace/data/klines_aggregate)"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        help="Filter to symbols starting with this prefix (e.g., BTC, ETH, SOL)"
    )
    parser.add_argument(
        "--show-clean",
        action="store_true",
        help="Also show symbols with no gaps"
    )
    
    args = parser.parse_args()
    
    # Find aggregate file
    aggregate_dir = Path(args.aggregate_dir)
    if not aggregate_dir.exists():
        print(f"❌ Error: Aggregate directory not found: {aggregate_dir}")
        return
    
    try:
        aggregate_file = find_aggregate_file(aggregate_dir)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return
    
    # Check for missing data
    check_missing_data(
        aggregate_file=aggregate_file,
        show_clean=args.show_clean,
        symbol_filter=args.symbol
    )


if __name__ == "__main__":
    main()
