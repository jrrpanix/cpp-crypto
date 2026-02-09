#!/usr/bin/env python3
"""
Download missing data for symbols with gaps.

This utility uses check_missing.py to identify gaps and then
downloads the missing monthly data files from Binance.
"""

import argparse
import os
from datetime import datetime
from pathlib import Path

from check_missing import find_aggregate_file, get_missing_data
from get_latest_klines import download_kline


def get_months_in_range(start_date: str, end_date: str) -> list:
    """
    Get all year-month pairs between start and end dates (inclusive).

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        List of (year, month) tuples
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")

    months = []
    current = start.replace(day=1)  # Start at beginning of month

    while current <= end:
        months.append((current.year, current.month))
        # Move to next month
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    return months


def file_exists(symbol: str, year: int, month: int, output_dir: Path) -> bool:
    """
    Check if the file already exists in the output directory.

    Args:
        symbol: Trading symbol
        year: Year
        month: Month
        output_dir: Output directory path

    Returns:
        True if file exists, False otherwise
    """
    filename = f"{symbol}-1m-{year}-{month:02}.zip"
    filepath = output_dir / filename
    return filepath.exists()


def download_missing_data(
    aggregate_dir: Path,
    output_dir: Path,
    symbol_filter: str = None,
    dry_run: bool = False,
    skip_existing: bool = True,
) -> None:
    """
    Download missing data for symbols with gaps.

    Args:
        aggregate_dir: Directory containing aggregate parquet files
        output_dir: Directory to save downloaded files
        symbol_filter: Optional prefix to filter symbols
        dry_run: If True, only print URLs without downloading
        skip_existing: If True, skip files that already exist
    """
    # Find and read aggregate file
    print("🔍 Finding aggregate file...")
    try:
        aggregate_file = find_aggregate_file(aggregate_dir)
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        return

    print(f"📖 Reading data from: {aggregate_file.name}\n")

    # Get missing data
    try:
        missing_data = get_missing_data(aggregate_file, symbol_filter)
    except Exception as e:
        print(f"❌ Error reading aggregate file: {e}")
        return

    # Filter to symbols with gaps
    symbols_with_gaps = {symbol: info for symbol, info in missing_data.items() if info["gaps"]}

    if not symbols_with_gaps:
        print("✅ No gaps found! All symbols have complete data.")
        return

    print(f"Found {len(symbols_with_gaps)} symbols with gaps:\n")

    # Create output directory if needed
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory: {output_dir}\n")

    # Track statistics
    total_files = 0
    skipped_files = 0
    downloaded_files = 0

    # Process each symbol
    for symbol, info in symbols_with_gaps.items():
        print("=" * 80)
        print(f"📊 {symbol}")
        print(f"   Period: {info['start_date']} to {info['end_date']}")
        print(f"   Missing: {info['missing_days']} days across {len(info['gaps'])} gap(s)")
        print()

        # Process each gap
        for i, gap in enumerate(info["gaps"], 1):
            print(f"   Gap {i}: {gap['start']} to {gap['end']} ({gap['days']} days)")

            # Get months to download for this gap
            months = get_months_in_range(gap["start"], gap["end"])

            for year, month in months:
                total_files += 1

                # Check if file exists
                if skip_existing and file_exists(symbol, year, month, output_dir):
                    print(f"      ⏭️  {year}-{month:02} - Already exists, skipping")
                    skipped_files += 1
                    continue

                # Build URL for display
                url = f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1m/{symbol}-1m-{year}-{month:02}.zip"

                if dry_run:
                    print(f"      [DRY RUN] Would download: {url}")
                else:
                    print(f"      ⏳ Downloading {year}-{month:02}...")
                    download_kline(year, month, symbol, str(output_dir), dry_run=False)
                    downloaded_files += 1

            print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"\nSymbols processed: {len(symbols_with_gaps)}")
    print(f"Total files to download: {total_files}")

    if dry_run:
        print(f"\n[DRY RUN] No files were downloaded")
    else:
        print(f"Files downloaded: {downloaded_files}")
        print(f"Files skipped (already exist): {skipped_files}")

        if downloaded_files > 0:
            print(f"\n✅ Downloaded files saved to: {output_dir}")
            print("\nNext steps:")
            print("  1. Unzip the downloaded files")
            print("  2. Process them with make_daily.py")
            print("  3. Re-run make_aggregate.py to update the aggregate file")


def main():
    """Main function to download missing data."""
    parser = argparse.ArgumentParser(
        description="Download missing data for symbols with gaps.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check what would be downloaded (dry run)
  python download_missing.py --dry-run
  
  # Download missing data for all symbols
  python download_missing.py
  
  # Download missing data for SOL symbols only
  python download_missing.py --symbol SOL
  
  # Download without skipping existing files
  python download_missing.py --no-skip-existing
  
  # Use custom directories
  python download_missing.py --aggregate-dir /custom/path --output-dir /custom/output
        """,
    )
    parser.add_argument(
        "--aggregate-dir",
        type=str,
        default="/workspace/data/klines_aggregate",
        help="Directory containing aggregate parquet files (default: /workspace/data/klines_aggregate)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/workspace/data/missing",
        help="Directory to save downloaded files (default: /workspace/data/missing)",
    )
    parser.add_argument(
        "--symbol",
        type=str,
        help="Filter to symbols starting with this prefix (e.g., BTC, ETH, SOL)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print download URLs without actually downloading"
    )
    parser.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="Download even if file already exists (will overwrite)",
    )

    args = parser.parse_args()

    # Convert paths
    aggregate_dir = Path(args.aggregate_dir)
    output_dir = Path(args.output_dir)

    # Check aggregate directory exists
    if not aggregate_dir.exists():
        print(f"❌ Error: Aggregate directory not found: {aggregate_dir}")
        return

    # Download missing data
    download_missing_data(
        aggregate_dir=aggregate_dir,
        output_dir=output_dir,
        symbol_filter=args.symbol,
        dry_run=args.dry_run,
        skip_existing=not args.no_skip_existing,
    )


if __name__ == "__main__":
    main()
