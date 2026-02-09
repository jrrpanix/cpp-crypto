#!/usr/bin/env python3
"""
Create aggregate file that includes both Binance data and synthetic indexes.

This combines data from:
- /workspace/data/klines_daily/  (raw Binance data)
- /workspace/data/klines_index/  (synthetic indexes like IX10, IX25, etc.)

Output: /workspace/data/klines_aggregate/AGG_WITH_INDEXES_<dates>.pq

This allows the webapp to display both real symbols and indexes.
"""

import argparse
from datetime import datetime
from pathlib import Path

import polars as pl


def get_date_range(df: pl.DataFrame) -> tuple[str, str]:
    """Extract date range from dataframe."""
    min_date = df["open_time"].min()
    max_date = df["open_time"].max()

    start_str = (
        min_date.strftime("%Y-%m-%d") if hasattr(min_date, "strftime") else str(min_date)[:10]
    )
    end_str = max_date.strftime("%Y-%m-%d") if hasattr(max_date, "strftime") else str(max_date)[:10]

    return start_str, end_str


def combine_files(
    binance_dir: Path,
    index_dir: Path,
    output_dir: Path,
    start_date: str = None,
    end_date: str = None,
) -> None:
    """
    Combine Binance klines and synthetic indexes into a single aggregate file.

    Args:
        binance_dir: Directory with Binance daily kline files
        index_dir: Directory with synthetic index files
        output_dir: Directory to write aggregate file
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
    """
    all_dfs = []
    symbols_processed = []

    # Load Binance kline data
    print(f"📊 Loading Binance kline data from {binance_dir}")
    binance_files = sorted(binance_dir.glob("*_daily_*.parquet"))

    if not binance_files:
        print(f"⚠️  No Binance files found in {binance_dir}")
    else:
        print(f"   Found {len(binance_files)} Binance kline files")

        for file_path in binance_files:
            try:
                df = pl.read_parquet(file_path)
                symbol = file_path.stem.split("_daily_")[0]

                # Add symbol column
                df = df.with_columns(pl.lit(symbol).alias("symbol"))

                # Filter by date range if specified
                if start_date:
                    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                    df = df.filter(pl.col("open_time") >= start_dt)

                if end_date:
                    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                    df = df.filter(pl.col("open_time") <= end_dt)

                if len(df) > 0:
                    all_dfs.append(df)
                    symbols_processed.append(symbol)
                    print(f"     ✓ {symbol}: {len(df):,} rows")

            except Exception as e:
                print(f"     ❌ Error reading {file_path.name}: {e}")
                continue

    # Load index data
    print(f"\n📈 Loading synthetic indexes from {index_dir}")

    if not index_dir.exists():
        print(f"⚠️  Index directory does not exist: {index_dir}")
        print(f"   Create indexes first using build_index.py")
    else:
        index_files = sorted(index_dir.glob("*_daily_*.parquet"))

        if not index_files:
            print(f"⚠️  No index files found in {index_dir}")
        else:
            print(f"   Found {len(index_files)} index files")

            for file_path in index_files:
                try:
                    df = pl.read_parquet(file_path)
                    symbol = file_path.stem.split("_daily_")[0]

                    # Add symbol column if not present
                    if "symbol" not in df.columns:
                        df = df.with_columns(pl.lit(symbol).alias("symbol"))

                    # Filter by date range if specified
                    if start_date:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        df = df.filter(pl.col("open_time") >= start_dt)

                    if end_date:
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        df = df.filter(pl.col("open_time") <= end_dt)

                    if len(df) > 0:
                        all_dfs.append(df)
                        symbols_processed.append(f"{symbol} [INDEX]")
                        print(f"     ✓ {symbol}: {len(df):,} rows [INDEX]")

                except Exception as e:
                    print(f"     ❌ Error reading {file_path.name}: {e}")
                    continue

    if not all_dfs:
        print("\n❌ No data to combine")
        return

    # Combine all dataframes
    print(f"\n🔗 Combining {len(all_dfs)} file(s)...")

    try:
        combined_df = pl.concat(all_dfs, how="vertical_relaxed")
        print(f"   Combined: {len(combined_df):,} total rows")
        print(f"   Symbols: {len(symbols_processed)} ({len(index_files)} indexes)")
    except Exception as e:
        print(f"❌ Error combining dataframes: {e}")
        return

    # Sort by symbol and date
    print("\n📑 Sorting by symbol and date...")
    combined_df = combined_df.sort(["symbol", "open_time"])

    # Get date range for filename
    start_date_str, end_date_str = get_date_range(combined_df)
    output_filename = f"AGG_WITH_INDEXES_{start_date_str}_{end_date_str}.pq"
    output_path = output_dir / output_filename

    print(f"\n📅 Date range: {start_date_str} to {end_date_str}")
    print(f"📄 Output file: {output_filename}")
    print(f"📂 Output path: {output_path}")

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write the combined file
    print("\n💾 Writing combined file...")
    try:
        combined_df.write_parquet(output_path, compression="snappy")
        print(f"✅ Successfully written to: {output_path}")

        # Show some stats
        print("\n📊 File statistics:")
        print(f"   Total rows: {len(combined_df):,}")
        print(f"   Total symbols: {len(symbols_processed)}")
        print(f"   Date range: {start_date_str} to {end_date_str}")
        print(f"   Columns: {', '.join(combined_df.columns)}")

        # Show symbol counts
        print("\n🔝 Top 15 symbols by row count:")
        symbol_counts = (
            combined_df.group_by("symbol")
            .agg(pl.count().alias("count"))
            .sort("count", descending=True)
        )
        for row in symbol_counts.head(15).iter_rows(named=True):
            index_marker = (
                " [INDEX]"
                if any(row["symbol"] in s for s in symbols_processed if "[INDEX]" in s)
                else ""
            )
            print(f"   {row['symbol']}: {row['count']:,} rows{index_marker}")

    except Exception as e:
        print(f"❌ Error writing file: {e}")


def main():
    """Main function to combine files."""
    parser = argparse.ArgumentParser(
        description="Combine Binance klines and synthetic indexes into aggregate file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Combine all Binance klines and indexes
  python make_aggregate_with_indexes.py
  
  # Specify custom directories
  python make_aggregate_with_indexes.py \\
    --binance-dir /workspace/data/klines_daily \\
    --index-dir /workspace/data/klines_index \\
    --output-dir /workspace/data/klines_aggregate
  
  # Filter by date range
  python make_aggregate_with_indexes.py \\
    --start-date 2024-07-01 \\
    --end-date 2025-10-31
        """,
    )
    parser.add_argument(
        "--binance-dir",
        type=str,
        default="/workspace/data/klines_daily",
        help="Directory with Binance daily kline files (default: /workspace/data/klines_daily)",
    )
    parser.add_argument(
        "--index-dir",
        type=str,
        default="/workspace/data/klines_index",
        help="Directory with synthetic index files (default: /workspace/data/klines_index)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/workspace/data/klines_aggregate",
        help="Output directory (default: /workspace/data/klines_aggregate)",
    )
    parser.add_argument("--start-date", type=str, help="Start date (YYYY-MM-DD) - optional filter")
    parser.add_argument("--end-date", type=str, help="End date (YYYY-MM-DD) - optional filter")

    args = parser.parse_args()

    binance_dir = Path(args.binance_dir)
    index_dir = Path(args.index_dir)
    output_dir = Path(args.output_dir)

    print("=" * 80)
    print("AGGREGATE BUILDER (WITH INDEXES)")
    print("=" * 80)
    print(f"\nBinance data: {binance_dir}")
    print(f"Index data: {index_dir}")
    print(f"Output: {output_dir}")

    if args.start_date:
        print(f"Start date filter: {args.start_date}")
    if args.end_date:
        print(f"End date filter: {args.end_date}")

    print()

    # Validate input directories
    if not binance_dir.exists():
        print(f"❌ Error: Binance directory not found: {binance_dir}")
        return

    combine_files(binance_dir, index_dir, output_dir, args.start_date, args.end_date)

    print("\n" + "=" * 80)
    print("✅ Aggregate file created successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()
