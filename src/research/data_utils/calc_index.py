#!/usr/bin/env python3
"""
Calculate index value using ADV-based weights.

Uses weights from previous period to compute index for current period,
avoiding look-ahead bias. Computes price as weighted sum: sum(wi * pricei)
and dollar volume as sum(volumei * pricei * wi).

Memory-efficient: processes data period-by-period instead of loading all data upfront.
"""

import argparse
from pathlib import Path
from datetime import datetime, timedelta
import polars as pl
import matplotlib.pyplot as plt


def load_weights(weights_file: Path) -> pl.DataFrame:
    """
    Load weights from parquet file.
    
    Expected columns: symbol, end_date, weight, rank
    
    Args:
        weights_file: Path to weights parquet file
        
    Returns:
        DataFrame with weights per symbol per period
    """
    df = pl.read_parquet(weights_file)
    print(f"📊 Loaded weights: {len(df)} rows")
    print(f"   Periods: {df['end_date'].min()} to {df['end_date'].max()}")
    print(f"   Unique symbols: {df['symbol'].n_unique()}")
    return df


def load_symbol_klines(klines_dir: Path, symbol: str, start_date: datetime, end_date: datetime) -> pl.DataFrame:
    """
    Load 1-minute kline data for a single symbol and date range.
    
    Args:
        klines_dir: Directory containing symbol kline parquet files
        symbol: Symbol to load
        start_date: Start date for data
        end_date: End date for data
        
    Returns:
        DataFrame with klines data for the symbol, or empty DataFrame if not found
    """
    # Look for parquet file matching pattern: {SYMBOL}_*.parquet
    pattern = f"{symbol}_*.parquet"
    files = list(klines_dir.glob(pattern))
    
    if not files:
        return pl.DataFrame()
    
    # Use most recent file if multiple exist
    file = sorted(files)[-1]
    
    try:
        # Read parquet file
        df = pl.read_parquet(file)
        
        # Filter by date range
        df = df.filter(
            (pl.col("open_time") >= start_date) &
            (pl.col("open_time") <= end_date)
        )
        
        # Add symbol column
        df = df.with_columns(pl.lit(symbol).alias("symbol"))
        
        # Ensure consistent data types (cast to Float64 for numeric columns)
        numeric_columns = ["open", "high", "low", "close", "volume"]
        for col in numeric_columns:
            if col in df.columns:
                df = df.with_columns(pl.col(col).cast(pl.Float64))
        
        # Ensure we have all required columns
        if "quote_volume" not in df.columns and "volume" in df.columns and "close" in df.columns:
            df = df.with_columns(
                (pl.col("volume") * pl.col("close")).alias("quote_volume")
            )
        else:
            # Cast quote_volume to Float64 if it exists
            if "quote_volume" in df.columns:
                df = df.with_columns(pl.col("quote_volume").cast(pl.Float64))
        
        # Ensure we have taker columns (if not present, set to 0.0)
        if "taker_buy_volume" not in df.columns:
            df = df.with_columns(pl.lit(0.0).alias("taker_buy_volume"))
        else:
            df = df.with_columns(pl.col("taker_buy_volume").cast(pl.Float64))
            
        if "taker_buy_quote_volume" not in df.columns:
            df = df.with_columns(pl.lit(0.0).alias("taker_buy_quote_volume"))
        else:
            df = df.with_columns(pl.col("taker_buy_quote_volume").cast(pl.Float64))
        
        # Cast count to Int64 if it exists
        if "count" in df.columns:
            df = df.with_columns(pl.col("count").cast(pl.Int64))
        
        # Cast ignore to Float64 if it exists (some files have Int64, some Float64)
        if "ignore" in df.columns:
            df = df.with_columns(pl.col("ignore").cast(pl.Float64))
        
        return df
        
    except Exception as e:
        print(f"❌ Error loading {symbol}: {e}")
        return pl.DataFrame()


def compute_index(weights_df: pl.DataFrame, klines_dir: Path, index_name: str) -> pl.DataFrame:
    """
    Compute index using weights from previous period with return-chain methodology.
    
    Uses return-based chaining to eliminate jumps at rebalance points.
    For each period's end date, apply those weights to the NEXT period's prices.
    This prevents look-ahead bias. Processes data period-by-period to minimize memory usage.
    
    Args:
        weights_df: DataFrame with symbol, end_date, weight, rank columns
        klines_dir: Directory containing symbol kline parquet files
        index_name: Name of the index for reporting
        
    Returns:
        DataFrame with index values. Contains columns:
        open_time, index_level, num_symbols
    """
    print(f"\n🔢 Computing {index_name} using return-chain methodology...")
    
    # Get unique periods from weights
    periods = weights_df.select("end_date").unique().sort("end_date")
    
    all_period_returns = []
    
    for i, period in enumerate(periods.iter_rows()):
        period_end = period[0]
        
        # Get weights for this period
        period_weights = weights_df.filter(pl.col("end_date") == period_end)
        symbols = period_weights["symbol"].to_list()
        
        # Apply these weights to NEXT period (avoid look-ahead)
        # If period ends on 2024-07-31, apply to data starting 2024-08-01
        next_start = period_end + timedelta(days=1)
        
        # Get next period's end (or use a default window, e.g., 30 days)
        next_periods = periods.filter(pl.col("end_date") > period_end)
        if len(next_periods) > 0:
            next_end = next_periods[0, 0]
        else:
            # For last period, use 30 days forward
            next_end = next_start + timedelta(days=30)
        
        # Load klines for this period only (memory efficient)
        period_klines_list = []
        loaded_symbols = 0
        
        for symbol in symbols:
            symbol_data = load_symbol_klines(klines_dir, symbol, next_start, next_end)
            if len(symbol_data) > 0:
                period_klines_list.append(symbol_data)
                loaded_symbols += 1
        
        if not period_klines_list:
            print(f"⚠️  No data for period {next_start} to {next_end}")
            continue
        
        # Combine klines for this period
        period_klines = pl.concat(period_klines_list)
        
        # Ensure count column exists and is Int64
        if "count" not in period_klines.columns:
            period_klines = period_klines.with_columns(pl.lit(0).cast(pl.Int64).alias("count"))
        
        # Calculate returns for each symbol (bar-to-bar)
        period_returns = period_klines.select(["open_time", "symbol", "close"]).sort(["symbol", "open_time"])
        period_returns = period_returns.with_columns([
            pl.col("close").pct_change().over("symbol").alias("return")
        ])
        
        # Fill first bar's returns with 0 for each symbol
        period_returns = period_returns.with_columns([
            pl.col("return").fill_null(0.0)
        ])
        
        # Join weights with returns
        period_returns = period_returns.join(
            period_weights.select(["symbol", "weight"]),
            on="symbol",
            how="left"
        )
        
        # Calculate weighted portfolio return for each timestamp
        portfolio_returns = period_returns.group_by("open_time").agg([
            (pl.col("weight") * pl.col("return")).sum().alias("portfolio_return"),
            pl.col("symbol").n_unique().alias("num_symbols")
        ]).sort("open_time")
        
        # Add period identifier for later chaining
        portfolio_returns = portfolio_returns.with_columns([
            pl.lit(i).alias("period_id")
        ])
        
        all_period_returns.append(portfolio_returns)
        
        print(f"   Period {period_end} → {next_start} to {next_end}: "
              f"{len(portfolio_returns):,} bars from {loaded_symbols}/{len(symbols)} symbols")
    
    if not all_period_returns:
        raise ValueError("No index values computed")
    
    # Combine all periods
    combined_returns = pl.concat(all_period_returns).sort("open_time")
    
    print(f"\n🔗 Chaining returns across {len(all_period_returns)} rebalance periods...")
    
    # Chain returns across periods
    # Within each period, chain returns normally
    # At period boundaries, ensure continuity
    
    chained_results = []
    cumulative_level = 1.0  # Start with multiplier of 1.0
    
    for period_id in range(len(all_period_returns)):
        period_data = combined_returns.filter(pl.col("period_id") == period_id)
        
        if len(period_data) == 0:
            continue
        
        # Calculate cumulative return within this period
        period_data = period_data.with_columns([
            (1.0 + pl.col("portfolio_return")).alias("return_factor")
        ])
        
        period_data = period_data.with_columns([
            pl.col("return_factor").cum_prod().alias("period_cumulative")
        ])
        
        # Apply the cumulative level from previous periods
        period_data = period_data.with_columns([
            (pl.col("period_cumulative") * cumulative_level).alias("index_level")
        ])
        
        chained_results.append(period_data)
        
        # Update cumulative level for next period
        # The next period starts where this period ended
        cumulative_level = period_data["index_level"][-1]
        
        print(f"   Period {period_id}: {len(period_data):,} bars, ending level = {cumulative_level:.4f}")
    
    # Combine all chained periods
    index_df = pl.concat(chained_results).sort("open_time")
    
    # Normalize to start at 100
    base_level = 100.0
    first_level = index_df["index_level"][0]
    normalization_factor = base_level / first_level
    
    index_df = index_df.with_columns([
        (pl.col("index_level") * normalization_factor).alias("index_level")
    ])
    
    # Select final columns
    index_df = index_df.select(["open_time", "index_level", "num_symbols"])
    
    print(f"\n✅ Index computed: {len(index_df):,} total bars")
    print(f"   Start level: {index_df['index_level'][0]:.2f} (normalized)")
    print(f"   End level: {index_df['index_level'][-1]:.2f}")
    print(f"   Total return: {(index_df['index_level'][-1] / index_df['index_level'][0] - 1) * 100:.2f}%")
    
    return index_df


def save_index(index_df: pl.DataFrame, output_file: Path, index_name: str):
    """
    Save index data to parquet file.
    
    Args:
        index_df: DataFrame with index values
        output_file: Path to output parquet file
        index_name: Name of the index (for metadata)
    """
    # Add index name as metadata column
    index_df = index_df.with_columns(pl.lit(index_name).alias("index_name"))
    
    # Save to parquet
    index_df.write_parquet(output_file)
    print(f"\n💾 Saved index to: {output_file}")
    print(f"   File size: {output_file.stat().st_size / 1024 / 1024:.2f} MB")


def plot_index(index_df: pl.DataFrame, index_name: str, output_file: Path = None):
    """
    Plot index level over time.
    
    Args:
        index_df: DataFrame with index values
        index_name: Name of the index
        output_file: Optional path to save plot
    """
    # Convert to pandas for plotting
    timestamps = index_df["open_time"].to_list()
    index_levels = index_df["index_level"].to_list()
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: Index level
    ax1.plot(timestamps, index_levels, linewidth=1.5, color='steelblue', alpha=0.8)
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('Index Level', fontsize=12)
    ax1.set_title(f'{index_name} - Level History', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label='Base Level (100)')
    ax1.legend()
    
    # Plot 2: Number of symbols
    if "num_symbols" in index_df.columns:
        num_symbols = index_df["num_symbols"].to_list()
        ax2.plot(timestamps, num_symbols, linewidth=1.5, color='coral', alpha=0.8)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Number of Symbols', fontsize=12)
        ax2.set_title('Symbol Count Over Time', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"\n📊 Saved plot to: {output_file}")
    else:
        plt.show()
    
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Calculate index value using ADV-based weights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python calc_index.py WEIGHTS_10_1_MONTH_2024-07-01_2025-09-30.pq "Top 10 Monthly Index"
  
  # Specify custom klines directory
  python calc_index.py WEIGHTS_50_12_WEEK_2024-07-01_2025-09-30.pq "Top 50 Weekly Index" \\
    --klines-dir /data/klines
  
  # Save output to specific location
  python calc_index.py WEIGHTS_25_1_MONTH_2024-07-01_2025-09-30.pq "Top 25 Index" \\
    --output /results/index_top25.pq
        """
    )
    
    parser.add_argument(
        "weights_file",
        help="Path to weights parquet file (e.g., WEIGHTS_10_1_MONTH_2024-07-01_2025-09-30.pq)"
    )
    parser.add_argument(
        "index_name",
        help="Name for the index (e.g., 'Top 10 Monthly ADV Index')"
    )
    parser.add_argument(
        "--klines-dir",
        default="/workspace/data/daily_klines",
        help="Directory containing kline parquet files (default: /workspace/data/daily_klines)"
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output parquet file path (default: INDEX_{index_name}_*.pq)"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate plot of index values"
    )
    parser.add_argument(
        "--plot-file",
        help="Save plot to file instead of displaying"
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    weights_path = Path(args.weights_file)
    if not weights_path.exists():
        parser.error(f"Weights file not found: {weights_path}")
    
    klines_dir = Path(args.klines_dir)
    if not klines_dir.exists():
        parser.error(f"Klines directory not found: {klines_dir}")
    
    print("=" * 80)
    print("INDEX CALCULATOR")
    print("=" * 80)
    print(f"\n📁 Weights file: {weights_path}")
    print(f"📁 Klines directory: {klines_dir}")
    print(f"📊 Index name: {args.index_name}")
    
    # Load weights
    weights_df = load_weights(weights_path)
    
    # Compute index (processes data period-by-period to minimize memory usage)
    index_df = compute_index(weights_df, klines_dir, args.index_name)
    
    # Determine output file
    if args.output:
        output_file = Path(args.output)
    else:
        # Generate output filename based on weights file
        # Extract date range from weights filename
        weights_name = weights_path.stem
        parts = weights_name.split("_")
        # Find date range in filename
        date_part = "_".join([p for p in parts if "-" in p and len(p) == 10])
        
        safe_index_name = args.index_name.replace(" ", "_").replace("/", "_")
        output_file = Path(f"INDEX_{safe_index_name}_{date_part}.pq")
    
    # Save index
    save_index(index_df, output_file, args.index_name)
    
    # Plot if requested
    if args.plot or args.plot_file:
        plot_file = Path(args.plot_file) if args.plot_file else None
        plot_index(index_df, args.index_name, plot_file)
    
    print("\n" + "=" * 80)
    print("✅ Index calculation complete!")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    exit(main())
