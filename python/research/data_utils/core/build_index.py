#!/usr/bin/env python3
"""
Build a weighted index from kline data in ONE STEP.

Combines the functionality of calc_adv.py + calc_index.py:
1. Calculates ADV (Average Dollar Volume) from daily klines
2. Generates weights for top N symbols per rebalance period
3. Builds index using return-chain methodology
4. Outputs index as a kline file compatible with trade simulator

The output index file has the same schema as other kline files and can be
found alongside other symbols in /workspace/data/klines_daily/
"""

import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import List

import polars as pl
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load_daily_klines(
    klines_dir: Path, start_date: datetime, end_date: datetime, suffix: str = "USDT"
) -> pl.DataFrame:
    """
    Load all daily kline files from directory.

    Args:
        klines_dir: Directory containing daily kline parquet files
        start_date: Start date for data
        end_date: End date for data
        suffix: Symbol suffix filter (e.g., "USDT")

    Returns:
        DataFrame with all symbol data
    """
    print(f"📂 Loading daily klines from {klines_dir}")

    all_files = list(klines_dir.glob("*.parquet"))
    if not all_files:
        all_files = list(klines_dir.glob("*.pq"))

    if not all_files:
        raise FileNotFoundError(f"No parquet files found in {klines_dir}")

    # Filter by suffix if specified
    if suffix:
        all_files = [f for f in all_files if suffix.upper() in f.stem.upper()]

    print(f"   Found {len(all_files)} parquet files")

    all_data = []
    for file in all_files:
        try:
            # Extract symbol from filename (e.g., BTCUSDT_*.parquet -> BTCUSDT)
            symbol = file.stem.split("_")[0]

            df = pl.read_parquet(file)

            # Filter by date range
            df = df.filter((pl.col("open_time") >= start_date) & (pl.col("open_time") <= end_date))

            if len(df) == 0:
                continue

            # Add symbol column if not present
            if "symbol" not in df.columns:
                df = df.with_columns(pl.lit(symbol).alias("symbol"))

            # Standardize numeric columns to Float64
            numeric_columns = ["open", "high", "low", "close", "volume"]
            for col in numeric_columns:
                if col in df.columns:
                    df = df.with_columns(pl.col(col).cast(pl.Float64))

            # Ensure quote_volume exists and is Float64
            if "quote_volume" not in df.columns:
                if "volume" in df.columns and "close" in df.columns:
                    df = df.with_columns((pl.col("volume") * pl.col("close")).alias("quote_volume"))
            else:
                df = df.with_columns(pl.col("quote_volume").cast(pl.Float64))

            # Cast optional columns if they exist
            if "count" in df.columns:
                df = df.with_columns(pl.col("count").cast(pl.Int64))

            if "taker_buy_volume" in df.columns:
                df = df.with_columns(pl.col("taker_buy_volume").cast(pl.Float64))

            if "taker_buy_quote_volume" in df.columns:
                df = df.with_columns(pl.col("taker_buy_quote_volume").cast(pl.Float64))

            all_data.append(df)

        except Exception as e:
            print(f"   ⚠️  Error loading {file.name}: {e}")
            continue

    if not all_data:
        raise ValueError("No data loaded from any files")

    combined = pl.concat(all_data)
    print(f"   Loaded {len(combined):,} rows for {combined['symbol'].n_unique()} symbols")

    return combined


def calculate_adv_weights(
    df: pl.DataFrame, interval: int = 1, units: str = "months", top_n: int = 10, drop_n: int = 0
) -> pl.DataFrame:
    """
    Calculate ADV and generate weights for top N symbols per period.

    Args:
        df: DataFrame with daily data (open_time, symbol, quote_volume)
        interval: Number of units per rebalance period
        units: "months" or "weeks"
        top_n: Number of top symbols to include
        drop_n: Number of top symbols to drop (e.g., drop_n=1 excludes #1)

    Returns:
        DataFrame with columns: begin_date, end_date, symbol, adv, rank, weight
    """
    print(f"\n📊 Calculating {interval}-{units} ADV for top {top_n} symbols...")
    if drop_n > 0:
        print(f"   (Dropping top {drop_n}, keeping ranks {drop_n + 1}-{top_n})")

    # Add year and month columns
    df = df.with_columns(
        [pl.col("open_time").dt.year().alias("year"), pl.col("open_time").dt.month().alias("month")]
    )

    if units == "months":
        # Monthly grouping
        if interval == 1:
            result = df.group_by(["symbol", "year", "month"]).agg(
                [
                    pl.col("quote_volume").mean().alias("adv"),
                    pl.col("open_time").count().alias("day_count"),
                ]
            )

            # Create begin_date and end_date
            result = result.with_columns(
                [pl.date(pl.col("year"), pl.col("month"), 1).alias("begin_date")]
            )

            result = result.with_columns(
                [
                    pl.when(pl.col("month") == 12)
                    .then(pl.col("year") + 1)
                    .otherwise(pl.col("year"))
                    .alias("next_year"),
                    pl.when(pl.col("month") == 12)
                    .then(1)
                    .otherwise(pl.col("month") + 1)
                    .alias("next_month"),
                ]
            )

            result = result.with_columns(
                [
                    (
                        pl.date(pl.col("next_year"), pl.col("next_month"), 1) - pl.duration(days=1)
                    ).alias("end_date")
                ]
            )

            # Filter symbols with at least 90% data coverage
            result = result.with_columns(
                [
                    ((pl.col("end_date") - pl.col("begin_date")).dt.total_days() + 1).alias(
                        "month_days"
                    )
                ]
            )
            result = result.filter(
                pl.col("day_count") >= (pl.col("month_days") * 0.9).cast(pl.Int64)
            )

            result = result.drop(
                ["next_year", "next_month", "day_count", "month_days", "year", "month"]
            )

    # Create interval identifier and rank
    result = result.with_columns(
        [
            (
                pl.col("begin_date").dt.strftime("%Y-%m-%d")
                + "_"
                + pl.col("end_date").dt.strftime("%Y-%m-%d")
            ).alias("interval_id")
        ]
    )

    result = result.with_columns(
        [pl.col("adv").rank(method="ordinal", descending=True).over("interval_id").alias("rank")]
    )

    # Filter to top N
    result = result.filter(pl.col("rank") <= top_n)

    # Drop top N if requested
    if drop_n > 0:
        result = result.filter(pl.col("rank") > drop_n)

    # Calculate weights
    result = result.with_columns(
        [(pl.col("adv") / pl.col("adv").sum().over("interval_id")).alias("weight")]
    )

    result = result.drop(["interval_id"])
    result = result.sort(["begin_date", "rank"])

    print(f"   ✅ Generated weights for {result['symbol'].n_unique()} unique symbols")
    print(f"   Total periods: {result.select('begin_date').n_unique()}")

    return result


def build_index_returns(
    daily_prices: pl.DataFrame, weights_df: pl.DataFrame, base_level: float = 100.0
) -> pl.DataFrame:
    """
    Build index using return-chain methodology.

    Args:
        daily_prices: DataFrame with daily OHLC data
        weights_df: DataFrame with weights per period
        base_level: Starting index level

    Returns:
        DataFrame with columns: open_time, index_level, num_symbols
    """
    print(f"\n🔗 Building index using return-chain method (base={base_level})...")

    # Get unique rebalance dates
    rebalance_dates = weights_df.select("end_date").unique().sort("end_date")
    all_dates = daily_prices.select("open_time").unique().sort("open_time")

    # Calculate daily returns for each symbol and extract volume data
    daily_returns = daily_prices.select(
        ["open_time", "symbol", "close", "volume", "quote_volume"]
    ).sort(["symbol", "open_time"])
    daily_returns = daily_returns.with_columns(
        [pl.col("close").pct_change().over("symbol").alias("return")]
    )
    daily_returns = daily_returns.with_columns([pl.col("return").fill_null(0.0)])

    # Build daily weights by forward-filling from rebalance dates
    daily_weights_list = []

    for i, rebal_row in enumerate(rebalance_dates.iter_rows(named=True)):
        rebal_date = rebal_row["end_date"]

        # Get weights for this period
        period_weights = weights_df.filter(pl.col("end_date") == rebal_date).select(
            ["symbol", "weight"]
        )

        # Weights apply to NEXT period (avoid look-ahead bias)
        weight_start = rebal_date + pl.duration(days=1)

        if i < len(rebalance_dates) - 1:
            next_rebal = rebalance_dates[i + 1, "end_date"]
            weight_end = next_rebal
        else:
            weight_end = all_dates[-1, "open_time"]

        # Get all dates in this range
        period_dates = all_dates.filter(
            (pl.col("open_time") > weight_start) & (pl.col("open_time") <= weight_end)
        )

        if len(period_dates) > 0:
            period_weights = period_weights.with_columns(pl.lit(1).alias("_key"))
            period_dates = period_dates.with_columns(pl.lit(1).alias("_key"))

            daily_weights_period = period_dates.join(period_weights, on="_key").drop("_key")
            daily_weights_list.append(daily_weights_period)

    if not daily_weights_list:
        raise ValueError("No daily weights generated")

    # Combine all daily weights
    daily_weights = pl.concat(daily_weights_list)

    # Join weights with returns
    portfolio_data = daily_returns.join(daily_weights, on=["open_time", "symbol"], how="inner")

    # Calculate weighted portfolio return for each day
    # Also calculate synthetic volume as weighted sum of constituent volumes
    portfolio_returns = (
        portfolio_data.group_by("open_time")
        .agg(
            [
                (pl.col("weight") * pl.col("return")).sum().alias("portfolio_return"),
                (pl.col("weight") * pl.col("volume")).sum().alias("synthetic_volume"),
                (pl.col("weight") * pl.col("quote_volume")).sum().alias("synthetic_quote_volume"),
                pl.col("symbol").n_unique().alias("num_symbols"),
            ]
        )
        .sort("open_time")
    )

    # Chain returns to create index level
    portfolio_returns = portfolio_returns.with_columns(
        [(1.0 + pl.col("portfolio_return")).alias("return_factor")]
    )

    portfolio_returns = portfolio_returns.with_columns(
        [pl.col("return_factor").cum_prod().alias("cumulative_return")]
    )

    portfolio_returns = portfolio_returns.with_columns(
        [(pl.col("cumulative_return") * base_level).alias("index_level")]
    )

    # Normalize so first value is exactly base_level
    first_level = portfolio_returns["index_level"][0]
    normalization_factor = base_level / first_level

    portfolio_returns = portfolio_returns.with_columns(
        [(pl.col("index_level") * normalization_factor).alias("index_level")]
    )

    result = portfolio_returns.select(
        [
            "open_time",
            "index_level",
            "num_symbols",
            "portfolio_return",
            "synthetic_volume",
            "synthetic_quote_volume",
        ]
    )

    print(f"✅ Index built: {len(result)} days")
    print(f"   Start level: {result['index_level'][0]:.2f}")
    print(f"   End level: {result['index_level'][-1]:.2f}")
    print(
        f"   Total return: {(result['index_level'][-1] / result['index_level'][0] - 1) * 100:.2f}%"
    )
    print(f"   Avg daily synthetic quote volume: ${result['synthetic_quote_volume'].mean():,.0f}")

    return result


def convert_to_kline_format(index_df: pl.DataFrame, index_symbol: str) -> pl.DataFrame:
    """
    Convert index to standard kline format.

    Creates OHLC bars where all prices equal the index level (since it's a
    synthetic index without intraday variation at daily resolution).

    Schema matches Binance daily kline files exactly for compatibility with
    make_aggregate_with_indexes.py and the trading webapp.

    Synthetic volume represents the weighted sum of constituent volumes,
    allowing proper ADV calculations for the index.

    Args:
        index_df: DataFrame with index_level, synthetic_volume, synthetic_quote_volume columns
        index_symbol: Symbol name for the index (e.g., "IX10")

    Returns:
        DataFrame in kline format with columns matching Binance daily files:
        open, high, low, close, volume, quote_volume, count, taker_buy_volume,
        taker_buy_quote_volume, open_time, close_time, symbol
    """
    print(f"\n📊 Converting index to kline format...")

    # Create kline structure
    # For an index, OHLC all equal the index level
    # Volume and quote_volume are synthetic weighted sums from constituents
    # Schema matches Binance daily kline files exactly for compatibility
    kline_df = index_df.select(
        [
            pl.col("index_level").alias("open"),
            pl.col("index_level").alias("high"),
            pl.col("index_level").alias("low"),
            pl.col("index_level").alias("close"),
            pl.col("synthetic_volume").alias("volume"),
            pl.col("synthetic_quote_volume").alias("quote_volume"),
            pl.lit(0.0).alias("count"),
            pl.lit(0.0).alias("taker_buy_volume"),
            pl.lit(0.0).alias("taker_buy_quote_volume"),
            pl.col("open_time"),
            pl.col("open_time").alias("close_time"),  # Same as open_time for daily bars
        ]
    )

    # Add symbol column
    kline_df = kline_df.with_columns([pl.lit(index_symbol).alias("symbol")])

    print(f"   ✅ Created kline format with {len(kline_df)} bars")
    print(f"   📋 Columns: {kline_df.columns}")

    return kline_df


def save_kline(kline_df: pl.DataFrame, output_file: Path):
    """Save index in kline format."""
    kline_df.write_parquet(output_file)
    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"\n💾 Saved index kline to: {output_file}")
    print(f"   File size: {file_size_mb:.2f} MB")
    print(f"   Compatible with trade simulator ✓")


def plot_index(index_df: pl.DataFrame, index_name: str, output_file: Path):
    """Generate index visualization."""
    print(f"\n📈 Generating plot...")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

    plot_data = index_df.to_pandas()

    # Plot index level
    ax1.plot(plot_data["open_time"], plot_data["index_level"], linewidth=1.5, color="blue")
    ax1.set_title(f"{index_name} - Index Level", fontsize=14, fontweight="bold")
    ax1.set_ylabel("Index Level", fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=100, color="gray", linestyle="--", alpha=0.5, label="Base Level (100)")
    ax1.legend()

    # Plot number of constituents
    ax2.plot(plot_data["open_time"], plot_data["num_symbols"], linewidth=1.5, color="green")
    ax2.set_title(f"{index_name} - Number of Constituents", fontsize=14, fontweight="bold")
    ax2.set_xlabel("Date", fontsize=12)
    ax2.set_ylabel("Number of Symbols", fontsize=12)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"   Saved plot to: {output_file}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Build weighted index from daily klines in ONE STEP",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build top 10 USDT index with monthly rebalancing
  python build_index.py --klines-dir /workspace/data/klines_daily \\
    --start-date 2024-07-01 --end-date 2025-10-31 \\
    --top-n 10 --symbol IX10 --name "Top 10 Monthly Index"
  # Output: /workspace/data/klines_index/IX10_daily_2024-08_2025-10.parquet
  
  # Build top 25 index, dropping BTC (rank 1), with custom output dir
  python build_index.py --klines-dir /workspace/data/klines_daily \\
    --start-date 2024-07-01 --end-date 2025-10-31 \\
    --top-n 25 --drop-n 1 --symbol IX25 --name "Top 25 (ex-BTC)" \\
    --output-dir /custom/path/indexes
  
  # Build top 50 index with specific output file
  python build_index.py --klines-dir /workspace/data/klines_daily \\
    --start-date 2024-07-01 --end-date 2025-10-31 \\
    --top-n 50 --symbol IX50 \\
    --output /workspace/data/klines_index/IX50.parquet
        """,
    )

    parser.add_argument(
        "--klines-dir",
        type=str,
        required=True,
        help="Directory containing daily kline parquet files (raw Binance data)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to save index files (default: <klines-dir>/../klines_index/)",
    )
    parser.add_argument("--start-date", type=str, required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--top-n", type=int, default=10, help="Number of top symbols to include (default: 10)"
    )
    parser.add_argument(
        "--drop-n", type=int, default=0, help="Number of top symbols to drop (default: 0)"
    )
    parser.add_argument(
        "--interval", type=int, default=1, help="Rebalance interval length (default: 1)"
    )
    parser.add_argument(
        "--units",
        type=str,
        default="months",
        choices=["months", "weeks"],
        help="Rebalance interval units (default: months)",
    )
    parser.add_argument(
        "--suffix", type=str, default="USDT", help="Symbol suffix filter (default: USDT)"
    )
    parser.add_argument(
        "--symbol", type=str, required=True, help="Index symbol name (e.g., IX10, IX25, TOPX)"
    )
    parser.add_argument("--name", type=str, help="Index display name (default: uses --symbol)")
    parser.add_argument(
        "--output",
        type=str,
        help="Output parquet file path (default: <klines-dir>/<symbol>.parquet)",
    )
    parser.add_argument(
        "--base-level", type=float, default=100.0, help="Starting index level (default: 100)"
    )
    parser.add_argument("--plot", action="store_true", help="Generate plot of index")
    parser.add_argument(
        "--plot-file", type=str, help="Output file for plot (default: <symbol>_plot.png)"
    )

    args = parser.parse_args()

    print("=" * 80)
    print("INDEX BUILDER (ONE-STEP)")
    print("=" * 80)

    # Parse dates
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")

    # Validate directories
    klines_dir = Path(args.klines_dir)
    if not klines_dir.exists():
        raise FileNotFoundError(f"Klines directory not found: {klines_dir}")

    # Determine output directory for indexes
    if args.output_dir:
        index_dir = Path(args.output_dir)
    else:
        # Default: create klines_index directory alongside klines_daily
        index_dir = klines_dir.parent / "klines_index"

    # Create index directory if it doesn't exist
    index_dir.mkdir(parents=True, exist_ok=True)

    # Set default index name
    index_name = args.name if args.name else args.symbol

    print(f"\n📋 Configuration:")
    print(f"   Index Symbol: {args.symbol}")
    print(f"   Index Name: {index_name}")
    print(f"   Output Directory: {index_dir}")
    print(f"   Top N: {args.top_n}")
    if args.drop_n > 0:
        print(f"   Drop N: {args.drop_n} (keeping ranks {args.drop_n + 1}-{args.top_n})")
    print(f"   Rebalance: {args.interval} {args.units}")
    print(f"   Date Range: {args.start_date} to {args.end_date}")
    print(f"   Suffix Filter: {args.suffix}")

    # Load all daily klines
    daily_data = load_daily_klines(klines_dir, start_date, end_date, args.suffix)

    # Calculate ADV and weights
    weights_df = calculate_adv_weights(
        daily_data, interval=args.interval, units=args.units, top_n=args.top_n, drop_n=args.drop_n
    )

    # Build index
    index_df = build_index_returns(daily_data, weights_df, base_level=args.base_level)

    # Convert to kline format
    kline_df = convert_to_kline_format(index_df, args.symbol)

    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        # Use naming pattern that matches other daily files: {SYMBOL}_daily_{dates}.parquet
        # Saved to klines_index directory to separate synthetic data from raw Binance data
        min_date_str = index_df["open_time"].min().strftime("%Y-%m")
        max_date_str = index_df["open_time"].max().strftime("%Y-%m")
        output_file = index_dir / f"{args.symbol}_daily_{min_date_str}_{max_date_str}.parquet"

    # Save kline file
    save_kline(kline_df, output_file)

    # Plot if requested
    if args.plot:
        plot_file = Path(args.plot_file) if args.plot_file else output_file.with_suffix(".png")
        plot_index(index_df, index_name, plot_file)

    print("\n" + "=" * 80)
    print("✅ Index building complete!")
    print(f"   Index file: {output_file}")
    print(f"   Saved to: {index_dir}")
    print(f"\n💡 Next steps:")
    print(f"   1. Regenerate aggregate with indexes:")
    print(f"      uv run python make_aggregate_with_indexes.py")
    print(f"   2. Restart backend server to see {args.symbol} in the webapp")
    print("=" * 80)


if __name__ == "__main__":
    main()
