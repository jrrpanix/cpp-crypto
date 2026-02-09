#!/usr/bin/env python3
"""
Plot daily price and volume data from aggregated parquet files.

This utility plots:
- Chart 1: Open, High, Low, Close prices
- Chart 2: Daily volume

Default file: /workspace/data/klines_aggregate/AGG_*.pq
Default suffix: USDT
"""

import argparse
from pathlib import Path

import polars as pl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from cli_utils import add_dir_arg


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


def plot_symbol(
    symbol: str,
    aggregate_file: Path,
    output_dir: Path = None,
    show: bool = True,
    dollar_volume: bool = False,
) -> None:
    """
    Plot daily price and volume data for a symbol.

    Args:
        symbol: Full symbol name (e.g., BTCUSDT)
        aggregate_file: Path to aggregate parquet file
        output_dir: Optional directory to save plot (if None, won't save)
        show: Whether to display the plot interactively
        dollar_volume: If True, plot dollar volume (quote_volume); if False, plot unit volume
    """
    print(f"Reading data from: {aggregate_file.name}")

    # Read the parquet file
    try:
        df = pl.read_parquet(aggregate_file)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    print(f"Total rows in file: {len(df):,}")
    print(f"Symbols in file: {df['symbol'].n_unique()}")

    # Filter for the specific symbol
    symbol_df = df.filter(pl.col("symbol") == symbol)

    if len(symbol_df) == 0:
        print(f"❌ No data found for symbol: {symbol}")
        print(f"\nAvailable symbols starting with '{symbol[:3]}':")
        available = df.filter(pl.col("symbol").str.starts_with(symbol[:3]))
        if len(available) > 0:
            symbols = available.select("symbol").unique().sort("symbol")
            for s in symbols["symbol"].to_list():
                print(f"  - {s}")
        return

    print(f"\n✓ Found {len(symbol_df):,} daily bars for {symbol}")

    # Sort by date
    symbol_df = symbol_df.sort("open_time")

    # Extract data for plotting
    dates = symbol_df["open_time"].to_list()
    opens = symbol_df["open"].to_list()
    highs = symbol_df["high"].to_list()
    lows = symbol_df["low"].to_list()
    closes = symbol_df["close"].to_list()

    # Choose between dollar volume (quote_volume) or unit volume
    if dollar_volume:
        if "quote_volume" not in symbol_df.columns:
            print("⚠️  Warning: quote_volume column not found, falling back to unit volume")
            volume_col = "volume"
            volume_label = "Volume (Units)"
            dollar_volume = False
        else:
            volume_col = "quote_volume"
            volume_label = "Volume (USD)"
    else:
        volume_col = "volume"
        volume_label = "Volume (Units)"

    volumes = symbol_df[volume_col].to_list()

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    fig.suptitle(f"{symbol} Daily Price and Volume", fontsize=16, fontweight="bold")

    # Plot 1: Price (Open, High, Low, Close)
    ax1.plot(dates, opens, label="Open", linewidth=1.5, alpha=0.8)
    ax1.plot(dates, highs, label="High", linewidth=1.5, alpha=0.8)
    ax1.plot(dates, lows, label="Low", linewidth=1.5, alpha=0.8)
    ax1.plot(dates, closes, label="Close", linewidth=2, alpha=0.9, color="black")

    ax1.set_ylabel("Price (USDT)", fontsize=12, fontweight="bold")
    ax1.legend(loc="upper left", framealpha=0.9)
    ax1.grid(True, alpha=0.3)
    ax1.set_title("Daily Prices", fontsize=12, pad=10)

    # Format y-axis for price
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.2f}"))

    # Plot 2: Volume
    ax2.bar(
        dates, volumes, width=0.8, alpha=0.7, color="steelblue", edgecolor="darkblue", linewidth=0.5
    )

    ax2.set_ylabel(volume_label, fontsize=12, fontweight="bold")
    ax2.set_xlabel("Date", fontsize=12, fontweight="bold")
    ax2.grid(True, alpha=0.3, axis="y")
    ax2.set_title(f"Daily {volume_label}", fontsize=12, pad=10)

    # Format y-axis for volume
    if dollar_volume:
        # Format as currency for dollar volume
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.0f}"))
    else:
        # Format as regular number for unit volume
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"{x:,.0f}"))

    # Format x-axis dates
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Add some statistics as text
    avg_vol_str = (
        f"${sum(volumes)/len(volumes):,.0f}"
        if dollar_volume
        else f"{sum(volumes)/len(volumes):,.0f}"
    )
    stats_text = (
        f"Period: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}\n"
        f"Days: {len(symbol_df)}\n"
        f"Price Range: ${min(lows):,.2f} - ${max(highs):,.2f}\n"
        f"Avg {volume_label}: {avg_vol_str}"
    )
    ax1.text(
        0.02,
        0.98,
        stats_text,
        transform=ax1.transAxes,
        verticalalignment="top",
        fontsize=9,
        family="monospace",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.8),
    )

    plt.tight_layout()

    # Save plot if output directory specified
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{symbol}_daily.png"
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        print(f"\n✅ Plot saved to: {output_file}")

    # Show plot if requested
    if show:
        plt.show()
    else:
        plt.close()


def main():
    """Main function to plot daily data."""
    parser = argparse.ArgumentParser(
        description="Plot daily price and volume data from aggregated parquet files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plot BTCUSDT (default suffix is USDT)
  python plot_daily.py BTC
  
  # Plot ETHUSDT with dollar volume instead of unit volume
  python plot_daily.py ETH --dollar-volume
  
  # Plot with custom suffix
  python plot_daily.py BTC --suffix USDC
  
  # Save plot without showing
  python plot_daily.py BTC --no-show --output-dir ./plots
        """,
    )
    parser.add_argument("prefix", type=str, help="Symbol prefix (e.g., BTC, ETH, DOGE)")
    parser.add_argument("--suffix", type=str, default="USDT", help="Symbol suffix (default: USDT)")
    add_dir_arg(
        parser,
        "aggregate-dir",
        default="/workspace/data/klines_aggregate",
        help_text="Directory containing aggregate parquet files",
    )
    add_dir_arg(parser, "output-dir", help_text="Directory to save plot image (optional)")
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Don't display plot interactively (useful when saving only)",
    )
    parser.add_argument(
        "--dollar-volume",
        action="store_true",
        help="Plot dollar volume (quote_volume) instead of unit volume",
    )

    args = parser.parse_args()

    # Construct full symbol name
    symbol = f"{args.prefix.upper()}{args.suffix.upper()}"

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

    # Parse output directory if provided
    output_dir = Path(args.output_dir) if args.output_dir else None

    # Plot the data
    plot_symbol(
        symbol=symbol,
        aggregate_file=aggregate_file,
        output_dir=output_dir,
        show=not args.no_show,
        dollar_volume=args.dollar_volume,
    )


if __name__ == "__main__":
    main()
