#!/usr/bin/env python3
"""
Repair missing data by merging downloaded files into existing parquet files.

This utility processes downloaded zip files from Binance and merges them
into the existing parquet files, ensuring no duplicate dates.
"""

import argparse
from datetime import datetime
from pathlib import Path

import polars as pl

from update_klines import read_binance_zip
from cli_utils import add_symbol_filter_arg


def extract_symbol_from_filename(filename: str) -> str:
    """
    Extract symbol from Binance zip filename.

    Args:
        filename: Filename like "BTCUSDT-1m-2025-04.zip"

    Returns:
        Symbol (e.g., "BTCUSDT")
    """
    # Format: SYMBOL-1m-YYYY-MM.zip
    parts = filename.replace(".zip", "").split("-")
    if len(parts) >= 3:
        # Join all parts except the last two (1m, YYYY, MM)
        return "-".join(parts[:-3]) if len(parts) > 3 else parts[0]
    return parts[0]


def extract_date_from_filename(filename: str) -> tuple:
    """
    Extract year and month from Binance zip filename.

    Args:
        filename: Filename like "BTCUSDT-1m-2025-04.zip"

    Returns:
        Tuple of (year, month) as strings
    """
    # Format: SYMBOL-1m-YYYY-MM.zip
    parts = filename.replace(".zip", "").split("-")
    if len(parts) >= 3:
        year = parts[-2]
        month = parts[-1]
        return year, month
    return None, None


def find_existing_parquet(symbol: str, klines_dir: Path) -> Path:
    """
    Find the existing parquet file for a symbol.

    Args:
        symbol: Trading symbol
        klines_dir: Directory containing kline parquet files

    Returns:
        Path to parquet file, or None if not found
    """
    # Look for files matching SYMBOL_1m_*.parquet
    matches = list(klines_dir.glob(f"{symbol}_1m_*.parquet"))

    if not matches:
        return None

    if len(matches) > 1:
        print(f"⚠️  Warning: Multiple parquet files found for {symbol}, using: {matches[0].name}")

    return matches[0]


def merge_data(existing_df: pl.DataFrame, new_df: pl.DataFrame) -> tuple:
    """
    Merge new data into existing data, avoiding duplicates.

    Args:
        existing_df: Existing parquet data
        new_df: New data from zip file

    Returns:
        Tuple of (merged_df, stats_dict)
        stats_dict contains: {
            "existing_rows": int,
            "new_rows": int,
            "duplicates": int,
            "added_rows": int,
            "total_rows": int
        }
    """
    existing_rows = len(existing_df)
    new_rows = len(new_df)

    # Get the date range of new data for logging
    new_dates = new_df.select("open_time").to_series()
    new_start = new_dates.min()
    new_end = new_dates.max()

    # Find duplicates by checking if open_time exists in existing data
    existing_times = set(existing_df.select("open_time").to_series())
    new_times = new_df.select("open_time").to_series()

    duplicates = sum(1 for t in new_times if t in existing_times)

    if duplicates > 0:
        print(f"      ⚠️  Found {duplicates} duplicate timestamps, removing...")
        # Filter out duplicates
        new_df = new_df.filter(~pl.col("open_time").is_in(existing_times))

    # Concatenate and sort
    merged_df = pl.concat([existing_df, new_df])
    merged_df = merged_df.sort("open_time")

    added_rows = len(new_df)
    total_rows = len(merged_df)

    stats = {
        "existing_rows": existing_rows,
        "new_rows": new_rows,
        "duplicates": duplicates,
        "added_rows": added_rows,
        "total_rows": total_rows,
        "new_start": new_start,
        "new_end": new_end,
    }

    return merged_df, stats


def process_zip_file(
    zip_path: Path, klines_dir: Path, output_dir: Path = None, check_mode: bool = False
) -> bool:
    """
    Process a single zip file and merge it into the corresponding parquet file.

    Args:
        zip_path: Path to the zip file
        klines_dir: Directory containing existing parquet files
        output_dir: Optional directory for check mode output
        check_mode: If True, save to output_dir instead of overwriting

    Returns:
        True if successful, False otherwise
    """
    print(f"\n📦 Processing: {zip_path.name}")

    # Extract symbol and date from filename
    symbol = extract_symbol_from_filename(zip_path.name)
    year, month = extract_date_from_filename(zip_path.name)

    print(f"   Symbol: {symbol}")
    print(f"   Period: {year}-{month}")

    # Find existing parquet file
    existing_parquet = find_existing_parquet(symbol, klines_dir)

    if not existing_parquet:
        print(f"   ❌ No existing parquet file found for {symbol}")
        print(f"      Looked for: {symbol}_1m_*.parquet in {klines_dir}")
        return False

    print(f"   Found: {existing_parquet.name}")

    try:
        # Read existing parquet
        print(f"   📖 Reading existing parquet...")
        existing_df = pl.read_parquet(existing_parquet)

        # Read new data from zip using shared function
        print(f"   📖 Reading new data from zip...")
        new_df = read_binance_zip(str(zip_path), existing_df.schema)

        # Debug: Show schemas
        print(f"   🔍 Schema check:")
        print(f"      Existing columns: {len(existing_df.columns)}")
        print(f"      New columns: {len(new_df.columns)}")

        # Check for schema mismatches
        mismatches = []
        for col in existing_df.columns:
            if col in new_df.columns:
                existing_type = existing_df[col].dtype
                new_type = new_df[col].dtype
                if existing_type != new_type:
                    mismatches.append(f"{col}: existing={existing_type}, new={new_type}")

        if mismatches:
            print(f"      ⚠️  Schema mismatches:")
            for m in mismatches:
                print(f"         {m}")
        else:
            print(f"      ✅ Schemas match")

        # Merge data
        print(f"   🔄 Merging data...")
        merged_df, stats = merge_data(existing_df, new_df)

        # Display statistics
        print(f"   📊 Statistics:")
        print(f"      Existing rows: {stats['existing_rows']:,}")
        print(f"      New rows in zip: {stats['new_rows']:,}")
        print(f"      Duplicates removed: {stats['duplicates']:,}")
        print(f"      Rows added: {stats['added_rows']:,}")
        print(f"      Total rows: {stats['total_rows']:,}")
        print(f"      New data range: {stats['new_start']} to {stats['new_end']}")

        # Determine output path
        if check_mode:
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / existing_parquet.name
            print(f"   💾 [CHECK MODE] Saving to: {output_path}")
        else:
            output_path = existing_parquet
            print(f"   💾 Saving updated file...")

        # Save the merged data
        merged_df.write_parquet(output_path)

        print(f"   ✅ Successfully processed {symbol}")

        return True

    except Exception as e:
        print(f"   ❌ Error processing {zip_path.name}: {e}")
        import traceback

        traceback.print_exc()
        return False


def repair_missing_data(
    missing_dir: Path,
    klines_dir: Path,
    check_dir: Path = None,
    check_mode: bool = False,
    check_all: bool = False,
    symbol_filter: str = None,
) -> None:
    """
    Repair missing data by merging downloaded zip files into parquet files.

    Args:
        missing_dir: Directory containing downloaded zip files
        klines_dir: Directory containing existing parquet files
        check_dir: Directory for check mode output
        check_mode: If True, process only one file and save to check_dir
        check_all: If True, process all files and save to check_dir (implies check_mode)
        symbol_filter: Optional prefix to filter symbols
    """
    print("🔧 REPAIR MISSING DATA")
    print("=" * 80)
    print(f"Missing data dir: {missing_dir}")
    print(f"Klines dir: {klines_dir}")

    if check_mode or check_all:
        print(f"Check mode dir: {check_dir}")
        if check_all:
            print("\n⚠️  CHECK ALL MODE: Will process ALL files and save to check directory")
        else:
            print("\n⚠️  CHECK MODE: Will process only ONE file and save to check directory")

    print()

    # Check directories exist
    if not missing_dir.exists():
        print(f"❌ Error: Missing data directory not found: {missing_dir}")
        return

    if not klines_dir.exists():
        print(f"❌ Error: Klines directory not found: {klines_dir}")
        return

    # Find all zip files
    zip_files = sorted(missing_dir.glob("*.zip"))

    if not zip_files:
        print(f"❌ No zip files found in {missing_dir}")
        return

    # Filter by symbol if requested
    if symbol_filter:
        zip_files = [
            f
            for f in zip_files
            if extract_symbol_from_filename(f.name).startswith(symbol_filter.upper())
        ]
        print(
            f"Filtered to {len(zip_files)} file(s) for symbols starting with '{symbol_filter.upper()}'"
        )

    print(f"Found {len(zip_files)} zip file(s) to process\n")

    if check_mode and not check_all and zip_files:
        print(f"Processing first file for check: {zip_files[0].name}\n")
        zip_files = zip_files[:1]
    elif check_all and zip_files:
        print(f"Processing all {len(zip_files)} file(s) for check\n")

    # Process files
    successful = 0
    failed = 0

    for zip_file in zip_files:
        if process_zip_file(zip_file, klines_dir, check_dir, check_mode or check_all):
            successful += 1
        else:
            failed += 1

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files processed: {len(zip_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    if (check_mode or check_all) and successful > 0:
        print(f"\n✅ Check mode complete. Review the output in: {check_dir}")
        print("   If the data looks good, run without --check to update all files.")
    elif successful > 0 and not check_mode and not check_all:
        print(f"\n✅ Successfully repaired {successful} file(s)")
        print("\nNext steps:")
        print("  1. Run make_daily.py to regenerate daily aggregates")
        print("  2. Run make_aggregate.py to update the aggregate file")
        print("  3. Run check_missing.py to verify gaps are filled")


def main():
    """Main function to repair missing data."""
    parser = argparse.ArgumentParser(
        description="Repair missing data by merging downloaded files into existing parquet files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check mode: Process one file and save to /workspace/data/check
  python repair_missing.py --check
  
  # Check all mode: Process all files and save to /workspace/data/check
  python repair_missing.py --check-all
  
  # Repair all missing data (after verifying with --check)
  python repair_missing.py
  
  # Repair only SOL symbols
  python repair_missing.py --symbol SOL
  
  # Check all SOL symbols
  python repair_missing.py --check-all --symbol SOL
  
  # Use custom directories
  python repair_missing.py --missing-dir /custom/missing --klines-dir /custom/klines
        """,
    )
    parser.add_argument(
        "--missing-dir",
        type=str,
        default="/workspace/data/missing",
        help="Directory containing downloaded zip files (default: /workspace/data/missing)",
    )
    parser.add_argument(
        "--klines-dir",
        type=str,
        default="/workspace/data/klines",
        help="Directory containing existing parquet files (default: /workspace/data/klines)",
    )
    parser.add_argument(
        "--check-dir",
        type=str,
        default="/workspace/data/check",
        help="Directory for check mode output (default: /workspace/data/check)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check mode: process only one file and save to check directory",
    )
    parser.add_argument(
        "--check-all",
        action="store_true",
        help="Check all mode: process all files and save to check directory (no actual updates)",
    )
    add_symbol_filter_arg(
        parser, help_text="Filter to symbols starting with this prefix (e.g., BTC, ETH, SOL)"
    )

    args = parser.parse_args()

    # Convert paths
    missing_dir = Path(args.missing_dir)
    klines_dir = Path(args.klines_dir)
    check_dir = Path(args.check_dir)

    # Repair missing data
    repair_missing_data(
        missing_dir=missing_dir,
        klines_dir=klines_dir,
        check_dir=check_dir,
        check_mode=args.check,
        check_all=args.check_all,
        symbol_filter=args.symbol,
    )


if __name__ == "__main__":
    main()
