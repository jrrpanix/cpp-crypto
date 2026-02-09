#!/usr/bin/env python3
"""
Combine all daily parquet files into a single aggregated file.

This utility reads all daily-bar parquet files from /workspace/data/klines_daily
and combines them into a single file named AGG_<start_date>_<end_date>.pq
stored in /workspace/data/klines_aggregate/
"""

import argparse
from datetime import datetime
from pathlib import Path

import polars as pl

from cli_utils import add_io_args, add_dry_run_arg


def get_date_range(df: pl.DataFrame) -> tuple[str, str]:
    """
    Get the start and end dates from a dataframe.

    Args:
        df: DataFrame with open_time column

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    dates = df.select(pl.col("open_time").dt.date())
    start_date = dates.min().item().strftime("%Y-%m-%d")
    end_date = dates.max().item().strftime("%Y-%m-%d")
    return start_date, end_date


def combine_daily_files(input_dir: Path, output_dir: Path, dry_run: bool = False) -> None:
    """
    Combine all daily parquet files into a single aggregated file.

    Args:
        input_dir: Directory containing daily parquet files
        output_dir: Directory to write aggregated file
        dry_run: If True, don't write output, just print what would be done
    """

    # Get all parquet files
    files = sorted(input_dir.glob("*.parquet"))

    if not files:
        print(f"❌ No parquet files found in {input_dir}")
        return

    print(f"Found {len(files)} daily parquet file(s)\n")

    # Read and combine all files
    print("Reading files...")
    dfs = []
    symbols_processed = []

    for file_path in files:
        try:
            df = pl.read_parquet(file_path)

            # Extract symbol from filename (e.g., BTCUSDT_daily_2024-07_2025-09.parquet -> BTCUSDT)
            symbol = file_path.stem.split("_daily_")[0]

            # Add symbol column
            df = df.with_columns(pl.lit(symbol).alias("symbol"))

            dfs.append(df)
            symbols_processed.append(symbol)
            print(f"  ✓ {symbol}: {len(df):,} rows")

        except Exception as e:
            print(f"  ❌ Error reading {file_path.name}: {e}")
            continue

    if not dfs:
        print("❌ No data to combine")
        return

    print(f"\nCombining {len(dfs)} file(s)...")

    # Combine all dataframes
    try:
        combined_df = pl.concat(dfs, how="vertical_relaxed")
        print(f"  Combined: {len(combined_df):,} total rows")
        print(f"  Symbols: {len(symbols_processed)}")
    except Exception as e:
        print(f"❌ Error combining dataframes: {e}")
        return

    # Sort by symbol and date
    print("\nSorting by symbol and date...")
    combined_df = combined_df.sort(["symbol", "open_time"])

    # Get date range for filename
    start_date, end_date = get_date_range(combined_df)
    output_filename = f"AGG_{start_date}_{end_date}.pq"
    output_path = output_dir / output_filename

    print(f"\nDate range: {start_date} to {end_date}")
    print(f"Output file: {output_filename}")
    print(f"Output path: {output_path}")

    if dry_run:
        print("\n[DRY RUN] File would be written with:")
        print(f"  - {len(combined_df):,} rows")
        print(f"  - {len(symbols_processed)} symbols")
        print(f"  - Columns: {combined_df.columns}")

        # Show sample data
        print("\nSample data (first 5 rows):")
        print(combined_df.head(5))

        print("\nSymbol counts:")
        symbol_counts = (
            combined_df.group_by("symbol")
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
        )
        print(symbol_counts.head(10))

        return

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write the combined file
    print("\nWriting combined file...")
    try:
        combined_df.write_parquet(output_path, compression="snappy")
        print(f"✅ Successfully written to: {output_path}")

        # Show some stats
        print("\nFile statistics:")
        print(f"  Total rows: {len(combined_df):,}")
        print(f"  Total symbols: {len(symbols_processed)}")
        print(f"  Date range: {start_date} to {end_date}")
        print(f"  Columns: {', '.join(combined_df.columns)}")

        # Show symbol counts
        print("\nTop 10 symbols by row count:")
        symbol_counts = (
            combined_df.group_by("symbol")
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
        )
        print(symbol_counts.head(10))

    except Exception as e:
        print(f"❌ Error writing file: {e}")


def main():
    """Main function to combine daily files."""
    parser = argparse.ArgumentParser(
        description="Combine all daily parquet files into a single aggregated file."
    )

    # Use common CLI utilities
    add_io_args(
        parser,
        input_default="/workspace/data/klines_daily",
        output_default="/workspace/data/klines_aggregate",
        input_help="Input directory containing daily parquet files",
        output_help="Output directory for aggregated file",
    )
    add_dry_run_arg(parser)

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    # Validate input directory
    if not input_dir.exists():
        print(f"❌ Error: Input directory not found: {input_dir}")
        return

    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")

    if args.dry_run:
        print("[DRY RUN MODE - No files will be written]\n")

    print()

    combine_daily_files(input_dir, output_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
