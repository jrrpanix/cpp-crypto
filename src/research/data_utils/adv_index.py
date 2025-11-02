#!/usr/bin/env python3
"""
Build an index from daily aggregate bars using ADV-based weights.

This script takes the output from calc_adv.py (weights by period) and
daily price data to construct an index that handles rebalancing gracefully
using either return chaining or divisor methodology.
"""

import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import polars as pl
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def load_weights(weights_file: Path) -> pl.DataFrame:
    """
    Load weights from calc_adv.py output.
    
    Expected columns: symbol, begin_date, end_date, adv, rank, weight
    
    Args:
        weights_file: Path to weights parquet file from calc_adv.py
        
    Returns:
        DataFrame with weights per symbol per period
    """
    df = pl.read_parquet(weights_file)
    print(f"📊 Loaded weights: {len(df)} rows")
    print(f"   Periods: {df['end_date'].min()} to {df['end_date'].max()}")
    print(f"   Unique symbols: {df['symbol'].n_unique()}")
    return df


def load_daily_prices(daily_dir: Path, symbols: List[str], start_date: datetime, end_date: datetime) -> pl.DataFrame:
    """
    Load daily aggregate price data for specified symbols.
    
    Args:
        daily_dir: Directory containing daily aggregate parquet files (e.g., /workspace/data/daily_agg/)
        symbols: List of symbols to load
        start_date: Start date for data
        end_date: End date for data
        
    Returns:
        DataFrame with columns: open_time, symbol, open, high, low, close, volume, quote_volume
    """
    all_data = []
    
    for symbol in symbols:
        # Look for daily file: {SYMBOL}_daily.parquet or similar
        pattern = f"{symbol}_*.parquet"
        files = list(daily_dir.glob(pattern))
        
        if not files:
            print(f"⚠️  No daily file found for {symbol}")
            continue
        
        # Use most recent file
        file = sorted(files)[-1]
        
        try:
            df = pl.read_parquet(file)
            
            # Filter by date range
            df = df.filter(
                (pl.col("open_time") >= start_date) &
                (pl.col("open_time") <= end_date)
            )
            
            # Add symbol column if not present
            if "symbol" not in df.columns:
                df = df.with_columns(pl.lit(symbol).alias("symbol"))
            
            all_data.append(df)
            
        except Exception as e:
            print(f"❌ Error loading {symbol}: {e}")
            continue
    
    if not all_data:
        raise ValueError("No data loaded for any symbols")
    
    # Combine all data
    combined = pl.concat(all_data)
    print(f"📈 Loaded daily prices: {len(combined):,} rows across {len(all_data)} symbols")
    
    return combined


def build_index_return_chain(
    daily_prices: pl.DataFrame,
    weights_df: pl.DataFrame,
    base_level: float = 100.0
) -> pl.DataFrame:
    """
    Build index using return-based chaining methodology.
    
    This method chains returns within each rebalance period, eliminating
    jumps at rebalance points by ensuring continuity through cumulative returns.
    
    Args:
        daily_prices: DataFrame with daily OHLC data (open_time, symbol, close, etc.)
        weights_df: DataFrame with weights per period (symbol, end_date, weight)
        base_level: Starting index level (default: 100.0)
        
    Returns:
        DataFrame with columns: open_time, index_level, num_symbols
    """
    print(f"\n🔗 Building index using return-chain method (base={base_level})...")
    
    # Get unique rebalance dates (sorted)
    rebalance_dates = weights_df.select("end_date").unique().sort("end_date")
    
    # Create a complete date series from daily prices
    all_dates = daily_prices.select("open_time").unique().sort("open_time")
    
    # Calculate daily returns for each symbol
    daily_returns = daily_prices.select(["open_time", "symbol", "close"]).sort(["symbol", "open_time"])
    daily_returns = daily_returns.with_columns([
        pl.col("close").pct_change().over("symbol").alias("return")
    ])
    
    # Fill first day's returns with 0 (no change from base level)
    daily_returns = daily_returns.with_columns([
        pl.col("return").fill_null(0.0)
    ])
    
    # Build daily weights by forward-filling from rebalance dates
    daily_weights_list = []
    
    for i, rebal_row in enumerate(rebalance_dates.iter_rows(named=True)):
        rebal_date = rebal_row["end_date"]
        
        # Get weights for this period
        period_weights = weights_df.filter(pl.col("end_date") == rebal_date).select(["symbol", "weight"])
        
        # Determine the date range for these weights
        # Weights from period ending rebal_date apply to NEXT period
        weight_start = rebal_date + pl.duration(days=1)
        
        if i < len(rebalance_dates) - 1:
            # Use until next rebalance
            next_rebal = rebalance_dates[i + 1, "end_date"]
            weight_end = next_rebal
        else:
            # Last period - use until end of data
            weight_end = all_dates[-1, "open_time"]
        
        # Get all dates in this range
        period_dates = all_dates.filter(
            (pl.col("open_time") > weight_start) &
            (pl.col("open_time") <= weight_end)
        )
        
        # Cross join dates with weights
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
    portfolio_data = daily_returns.join(
        daily_weights,
        on=["open_time", "symbol"],
        how="inner"
    )
    
    # Calculate weighted portfolio return for each day
    portfolio_returns = portfolio_data.group_by("open_time").agg([
        (pl.col("weight") * pl.col("return")).sum().alias("portfolio_return"),
        pl.col("symbol").n_unique().alias("num_symbols")
    ]).sort("open_time")
    
    # Chain returns to create index level
    # Start with base level on day before first return, then apply returns
    portfolio_returns = portfolio_returns.with_columns([
        (1.0 + pl.col("portfolio_return")).alias("return_factor")
    ])
    
    portfolio_returns = portfolio_returns.with_columns([
        pl.col("return_factor").cum_prod().alias("cumulative_return")
    ])
    
    portfolio_returns = portfolio_returns.with_columns([
        (pl.col("cumulative_return") * base_level).alias("index_level")
    ])
    
    # Option: Normalize so first value is exactly base_level
    # This adjusts for any returns that occurred before we could calculate portfolio returns
    first_level = portfolio_returns["index_level"][0]
    normalization_factor = base_level / first_level
    
    portfolio_returns = portfolio_returns.with_columns([
        (pl.col("index_level") * normalization_factor).alias("index_level")
    ])
    
    result = portfolio_returns.select(["open_time", "index_level", "num_symbols", "portfolio_return"])
    
    print(f"✅ Index built: {len(result)} days")
    print(f"   First date: {result['open_time'][0]}")
    print(f"   Start level: {result['index_level'][0]:.2f} (normalized from {first_level:.2f})")
    print(f"   First return: {result['portfolio_return'][0]*100:.4f}%")
    print(f"   End level: {result['index_level'][-1]:.2f}")
    print(f"   Total return: {(result['index_level'][-1] / result['index_level'][0] - 1) * 100:.2f}%")
    
    return result


def save_index(index_df: pl.DataFrame, output_file: Path, index_name: str):
    """Save index to parquet file."""
    index_df.write_parquet(output_file)
    file_size_mb = output_file.stat().st_size / (1024 * 1024)
    print(f"\n💾 Saved index to: {output_file}")
    print(f"   File size: {file_size_mb:.2f} MB")


def plot_index(index_df: pl.DataFrame, index_name: str, output_file: Path = None):
    """Plot index level over time."""
    if output_file is None:
        output_file = Path(f"{index_name.replace(' ', '_')}_plot.png")
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    # Convert to pandas for plotting
    plot_data = index_df.to_pandas()
    
    # Plot index level
    ax1.plot(plot_data["open_time"], plot_data["index_level"], linewidth=1.5, color="blue")
    ax1.set_title(f"{index_name} - Index Level", fontsize=14, fontweight="bold")
    ax1.set_ylabel("Index Level", fontsize=12)
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=100, color='gray', linestyle='--', alpha=0.5, label="Base Level (100)")
    ax1.legend()
    
    # Plot number of constituents
    ax2.plot(plot_data["open_time"], plot_data["num_symbols"], linewidth=1.5, color="green")
    ax2.set_title(f"{index_name} - Number of Constituents", fontsize=14, fontweight="bold")
    ax2.set_xlabel("Date", fontsize=12)
    ax2.set_ylabel("Number of Symbols", fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches="tight")
    print(f"\n📊 Saved plot to: {output_file}")
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description="Build index from daily bars using ADV weights",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build index from monthly ADV weights
  python adv_index.py WEIGHTS_10_1_MONTH_2024-07-01_2025-09-30.pq "Top 10 Index"
  
  # Specify daily data directory and output
  python adv_index.py weights.pq "My Index" --daily-dir /workspace/data/daily_agg --output my_index.pq --plot
        """
    )
    
    parser.add_argument("weights_file", type=str, help="Path to weights parquet file from calc_adv.py")
    parser.add_argument("index_name", type=str, help="Name of the index")
    parser.add_argument("--daily-dir", type=str, default="/workspace/data/daily_agg",
                        help="Directory containing daily aggregate parquet files")
    parser.add_argument("--output", type=str, help="Output parquet file (default: INDEX_{name}_{dates}.pq)")
    parser.add_argument("--plot", action="store_true", help="Generate plot of index")
    parser.add_argument("--plot-file", type=str, help="Output file for plot")
    parser.add_argument("--base-level", type=float, default=100.0, help="Starting index level (default: 100)")
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("ADV INDEX BUILDER")
    print("=" * 80)
    
    # Load weights
    weights_file = Path(args.weights_file)
    if not weights_file.exists():
        raise FileNotFoundError(f"Weights file not found: {weights_file}")
    
    weights_df = load_weights(weights_file)
    
    # Get symbols and date range from weights
    symbols = weights_df["symbol"].unique().to_list()
    min_date = weights_df["begin_date"].min()
    max_date = weights_df["end_date"].max()
    
    # Load daily prices
    daily_dir = Path(args.daily_dir)
    if not daily_dir.exists():
        raise FileNotFoundError(f"Daily directory not found: {daily_dir}")
    
    daily_prices = load_daily_prices(daily_dir, symbols, min_date, max_date)
    
    # Build index using return chain method
    index_df = build_index_return_chain(daily_prices, weights_df, base_level=args.base_level)
    
    # Generate output filename if not provided
    if args.output:
        output_file = Path(args.output)
    else:
        min_date_str = index_df["open_time"].min().strftime("%Y-%m-%d")
        max_date_str = index_df["open_time"].max().strftime("%Y-%m-%d")
        safe_name = args.index_name.replace(" ", "_").replace("/", "_")
        output_file = Path(f"INDEX_{safe_name}_{min_date_str}_{max_date_str}.pq")
    
    # Save index
    save_index(index_df, output_file, args.index_name)
    
    # Plot if requested
    if args.plot:
        plot_file = Path(args.plot_file) if args.plot_file else output_file.with_suffix(".png")
        plot_index(index_df, args.index_name, plot_file)
    
    print("\n" + "=" * 80)
    print("✅ Index construction complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()

