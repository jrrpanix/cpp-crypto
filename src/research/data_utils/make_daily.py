#!/usr/bin/env python3
"""
Convert minute-bar parquet files to daily-bar summaries.

This utility processes all parquet files in /workspace/data/klines and creates
daily aggregated versions with the same structure.
"""

import argparse
import os
from pathlib import Path

import polars as pl


def aggregate_to_daily(df: pl.DataFrame) -> pl.DataFrame:
    """
    Aggregate minute bars to daily bars.
    
    For each day:
    - open: first bar's open
    - high: max high price
    - low: min low price
    - close: last bar's close
    - volume: sum of volume
    - quote_volume: sum of quote_volume (if exists)
    - count: sum of count/trades
    - taker_buy_volume: sum of taker_buy_volume (if exists)
    - taker_buy_quote_volume: sum of taker_buy_quote_volume (if exists)
    """
    
    # Extract date from open_time
    df = df.with_columns(
        pl.col("open_time").dt.date().alias("date")
    )
    
    # Build aggregation expressions dynamically based on available columns
    agg_exprs = [
        pl.col("open").first().alias("open"),
        pl.col("high").max().alias("high"),
        pl.col("low").min().alias("low"),
        pl.col("close").last().alias("close"),
        pl.col("volume").sum().alias("volume"),
    ]
    
    # Add optional columns if they exist
    if "quote_volume" in df.columns:
        agg_exprs.append(pl.col("quote_volume").sum().alias("quote_volume"))
    
    if "count" in df.columns:
        agg_exprs.append(pl.col("count").sum().alias("count"))
    elif "trades" in df.columns:
        agg_exprs.append(pl.col("trades").sum().alias("trades"))
    
    if "taker_buy_volume" in df.columns:
        agg_exprs.append(pl.col("taker_buy_volume").sum().alias("taker_buy_volume"))
    
    if "taker_buy_quote_volume" in df.columns:
        agg_exprs.append(pl.col("taker_buy_quote_volume").sum().alias("taker_buy_quote_volume"))
    
    # Use the first open_time and last close_time for the day
    agg_exprs.extend([
        pl.col("open_time").first().alias("open_time"),
    ])
    
    if "close_time" in df.columns:
        agg_exprs.append(pl.col("close_time").last().alias("close_time"))
    
    # Group by date and aggregate
    daily_df = df.group_by("date").agg(agg_exprs)
    
    # Sort by date and drop the temporary date column
    daily_df = daily_df.sort("date").drop("date")
    
    return daily_df


def process_file(input_path: Path, output_dir: Path, dry_run: bool = False) -> None:
    """
    Process a single parquet file and create daily aggregated version.
    
    Args:
        input_path: Path to input minute-bar parquet file
        output_dir: Directory to write daily-bar parquet file
        dry_run: If True, don't write output, just print what would be done
    """
    print(f"Processing: {input_path.name}")
    
    # Read the parquet file
    try:
        df = pl.read_parquet(input_path)
    except Exception as e:
        print(f"  ❌ Error reading file: {e}")
        return
    
    print(f"  Input: {len(df):,} rows")
    
    # Aggregate to daily
    try:
        daily_df = aggregate_to_daily(df)
    except Exception as e:
        print(f"  ❌ Error aggregating: {e}")
        return
    
    print(f"  Output: {len(daily_df):,} rows (daily bars)")
    
    # Create output filename by replacing _1m with _daily
    output_filename = input_path.name.replace("_1m_", "_daily_")
    
    if dry_run:
        print(f"  [DRY RUN] Would write to: {output_dir / output_filename}")
        return
    
    # Write output file
    output_path = output_dir / output_filename
    try:
        daily_df.write_parquet(output_path, compression="snappy")
        print(f"  ✅ Written to: {output_path.name}")
    except Exception as e:
        print(f"  ❌ Error writing file: {e}")


def main():
    """Main function to process all parquet files."""
    parser = argparse.ArgumentParser(
        description="Convert minute-bar parquet files to daily-bar summaries."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="/workspace/data/klines",
        help="Input directory containing minute-bar parquet files (default: /workspace/data/klines)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/workspace/data/klines_daily",
        help="Output directory for daily-bar parquet files (default: /workspace/data/klines_daily)"
    )
    parser.add_argument(
        "--pattern",
        type=str,
        default="*.parquet",
        help="File pattern to match (default: *.parquet)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't write files, just show what would be done"
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Process only a specific file (by name)"
    )
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    # Validate input directory
    if not input_dir.exists():
        print(f"❌ Error: Input directory not found: {input_dir}")
        return
    
    # Create output directory if it doesn't exist
    if not args.dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Output directory: {output_dir}\n")
    else:
        print(f"[DRY RUN] Output directory would be: {output_dir}\n")
    
    # Get list of files to process
    if args.file:
        files = [input_dir / args.file]
        if not files[0].exists():
            print(f"❌ Error: File not found: {files[0]}")
            return
    else:
        files = sorted(input_dir.glob(args.pattern))
    
    if not files:
        print(f"❌ No files found matching pattern: {args.pattern}")
        return
    
    print(f"Found {len(files)} file(s) to process\n")
    
    # Process each file
    for file_path in files:
        process_file(file_path, output_dir, dry_run=args.dry_run)
        print()
    
    if not args.dry_run:
        print(f"✅ Complete! Processed {len(files)} file(s)")
    else:
        print(f"[DRY RUN] Would process {len(files)} file(s)")


if __name__ == "__main__":
    main()
