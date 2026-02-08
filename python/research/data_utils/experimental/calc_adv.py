#!/usr/bin/env python3
"""
Calculate Average Daily Volume (ADV) from aggregate daily data.

This utility computes the average daily trading volume (in dollars) over
specified intervals to avoid look-ahead bias.
"""

import argparse
from datetime import datetime
from pathlib import Path

import polars as pl
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for saving plots
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def calculate_adv(
    df: pl.DataFrame,
    interval: int = 1,
    units: str = "months",
    start_of_month: bool = False,
    index_start_day: str = None,
    top_n: int = None,
    drop_n: int = 0
) -> pl.DataFrame:
    """
    Calculate Average Daily Volume over intervals.
    
    Args:
        df: DataFrame with daily data (must have open_time, symbol, quote_volume)
        interval: Number of units per interval (default: 1)
        units: "months" or "weeks" (default: "months")
        start_of_month: If True, align week intervals to start of month (default: False for rolling)
        index_start_day: Day of week to start intervals (monday, tuesday, etc.). Overrides start_of_month.
        top_n: If specified, keep only top N symbols by ADV per interval and add weights
        drop_n: If specified with top_n, drop the top drop_n symbols before calculating weights (default: 0)
        
    Returns:
        DataFrame with columns: begin_date, end_date, symbol, adv, [rank], [weight]
        Weight column is added if top_n is specified
        Rank shows original ranking (1 = highest ADV, even if dropped)
    """
    # Add year and month columns for grouping
    df = df.with_columns([
        pl.col("open_time").dt.year().alias("year"),
        pl.col("open_time").dt.month().alias("month")
    ])
    
    if units == "months":
        return _calculate_adv_months(df, interval, top_n, drop_n)
    elif units == "weeks":
        return _calculate_adv_weeks(df, interval, start_of_month, index_start_day, top_n, drop_n)
    else:
        raise ValueError(f"Invalid units: {units}. Must be 'months' or 'weeks'")


def _calculate_adv_months(
    df: pl.DataFrame,
    interval_months: int,
    top_n: int = None,
    drop_n: int = 0
) -> pl.DataFrame:
    """Calculate ADV using month-based intervals."""
    
    if interval_months == 1:
        # Monthly intervals - group by year and month
        result = df.group_by(["symbol", "year", "month"]).agg([
            pl.col("quote_volume").mean().alias("adv"),
            pl.col("open_time").count().alias("day_count")
        ])
        
        # Create proper calendar begin_date and end_date
        # Begin date = first day of the month
        result = result.with_columns([
            pl.date(pl.col("year"), pl.col("month"), 1).alias("begin_date")
        ])
        
        # End date = first day of next month minus 1 day
        # Calculate next month and next year properly
        result = result.with_columns([
            pl.when(pl.col("month") == 12)
            .then(pl.col("year") + 1)
            .otherwise(pl.col("year"))
            .alias("next_year"),
            pl.when(pl.col("month") == 12)
            .then(1)
            .otherwise(pl.col("month") + 1)
            .alias("next_month")
        ])
        
        # Create end_date as (first day of next month) - 1 day
        result = result.with_columns([
            (pl.date(pl.col("next_year"), pl.col("next_month"), 1) - pl.duration(days=1)).alias("end_date")
        ])
        
        # Calculate expected days in month and filter symbols with insufficient data
        result = result.with_columns([
            ((pl.col("end_date") - pl.col("begin_date")).dt.total_days() + 1).alias("month_days")
        ])
        
        # Filter out symbols that don't have data for at least 90% of the month
        result = result.filter(pl.col("day_count") >= (pl.col("month_days") * 0.9).cast(pl.Int64))
        
        # Drop temporary columns
        result = result.drop(["next_year", "next_month", "day_count", "month_days"])
        
        # Sort by year, month, symbol
        result = result.sort(["year", "month", "symbol"])
        
    else:
        # Multi-month intervals
        # Create interval groups based on months since epoch
        df = df.with_columns([
            ((pl.col("year") * 12 + pl.col("month") - 1) / interval_months).floor().alias("interval_group")
        ])
        
        result = df.group_by(["symbol", "interval_group"]).agg([
            pl.col("year").min().alias("start_year"),
            pl.col("month").min().alias("start_month"),
            pl.col("year").max().alias("end_year"),
            pl.col("month").max().alias("end_month"),
            pl.col("quote_volume").mean().alias("adv"),
            pl.col("open_time").count().alias("day_count")
        ])
        
        # Create begin_date (first day of start month)
        result = result.with_columns([
            pl.date(pl.col("start_year"), pl.col("start_month"), 1).alias("begin_date")
        ])
        
        # Create end_date (last day of end month)
        # Calculate next month and next year properly
        result = result.with_columns([
            pl.when(pl.col("end_month") == 12)
            .then(pl.col("end_year") + 1)
            .otherwise(pl.col("end_year"))
            .alias("next_year"),
            pl.when(pl.col("end_month") == 12)
            .then(1)
            .otherwise(pl.col("end_month") + 1)
            .alias("next_month")
        ])
        
        # Create end_date as (first day of next month) - 1 day
        result = result.with_columns([
            (pl.date(pl.col("next_year"), pl.col("next_month"), 1) - pl.duration(days=1)).alias("end_date")
        ])
        
        # Calculate expected days and filter symbols with insufficient data
        result = result.with_columns([
            ((pl.col("end_date") - pl.col("begin_date")).dt.total_days() + 1).alias("interval_days")
        ])
        
        # Filter out symbols that don't have data for at least 90% of the interval
        result = result.filter(pl.col("day_count") >= (pl.col("interval_days") * 0.9).cast(pl.Int64))
        
        # Sort by interval and symbol
        result = result.sort(["interval_group", "symbol"])
        
        # Drop temporary columns
        result = result.drop(["interval_group", "start_year", "start_month", "end_year", "end_month", "next_year", "next_month", "day_count", "interval_days"])
    
    
    # If top_n is specified, filter to top N symbols per interval and calculate weights
    if top_n is not None:
        # Create a unique interval identifier from begin_date and end_date
        result = result.with_columns([
            (pl.col("begin_date").dt.strftime("%Y-%m-%d") + "_" + 
             pl.col("end_date").dt.strftime("%Y-%m-%d")).alias("interval_id")
        ])
        
        # For each interval, rank symbols by ADV
        result = result.with_columns([
            pl.col("adv").rank(method="ordinal", descending=True)
            .over("interval_id")
            .alias("rank")
        ])
        
        # Filter to top N
        result = result.filter(pl.col("rank") <= top_n)
        
        # If drop_n is specified, drop the top drop_n symbols
        if drop_n > 0:
            # Filter out ranks 1 through drop_n
            result = result.filter(pl.col("rank") > drop_n)
        
        # Calculate weights: weight_i = adv_i / sum(remaining adv) for each interval
        result = result.with_columns([
            (pl.col("adv") / pl.col("adv").sum().over("interval_id")).alias("weight")
        ])
        
        # Drop temporary interval_id column
        result = result.drop(["interval_id", "year", "month"])
        
        # Sort by begin_date, then by rank
        result = result.sort(["begin_date", "rank"])
        
        # Reorder columns with weight and rank
        result = result.select(["begin_date", "end_date", "symbol", "adv", "rank", "weight"])
    else:
        # Drop year and month columns
        result = result.drop(["year", "month"])
        
        # Sort by begin_date, then by adv descending
        result = result.sort(["begin_date", "adv"], descending=[False, True])
        
        # Reorder columns without weight
        result = result.select(["begin_date", "end_date", "symbol", "adv"])
    
    return result


def _calculate_adv_weeks(
    df: pl.DataFrame,
    interval_weeks: int,
    start_of_month: bool = False,
    index_start_day: str = None,
    top_n: int = None,
    drop_n: int = 0
) -> pl.DataFrame:
    """
    Calculate ADV using week-based intervals.
    
    Args:
        df: DataFrame with daily data
        interval_weeks: Number of weeks per interval
        start_of_month: If True, align intervals to start of month; if False, use rolling intervals
        index_start_day: Day of week to start intervals (monday, tuesday, etc.). Overrides start_of_month.
        top_n: If specified, keep only top N symbols per interval
        drop_n: If specified with top_n, drop the top drop_n symbols before calculating weights (default: 0)
    """
    from datetime import date, timedelta
    
    # Ensure data is sorted by time
    df = df.sort("open_time")
    
    # Get the first date in the data
    first_date = df.select(pl.col("open_time").min()).item()
    
    if index_start_day:
        # Map day names to weekday numbers (0=Monday, 6=Sunday)
        day_map = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }
        
        target_weekday = day_map.get(index_start_day.lower())
        if target_weekday is None:
            raise ValueError(f"Invalid day: {index_start_day}. Use monday, tuesday, wednesday, thursday, friday, saturday, or sunday")
        
        # Find the first occurrence of the target weekday on or after first_date
        current_weekday = first_date.weekday()
        days_ahead = (target_weekday - current_weekday) % 7
        if days_ahead == 0 and first_date.hour == 0 and first_date.minute == 0:
            # Already on target day at 00:00:00
            anchor_date = first_date.date()
        else:
            # Move to next occurrence of target weekday
            anchor_date = (first_date + timedelta(days=days_ahead)).date()
        
        # Calculate weeks since the anchor date
        df = df.with_columns([
            ((pl.col("open_time").cast(pl.Date) - pl.lit(anchor_date)).dt.total_days() / 7).floor().alias("weeks_since_start")
        ])
        
    elif start_of_month:
        # Align to the first day of the first month in the data
        first_month_start = date(first_date.year, first_date.month, 1)
        
        # Calculate weeks since the first month start
        df = df.with_columns([
            ((pl.col("open_time").cast(pl.Date) - pl.lit(first_month_start)).dt.total_days() / 7).floor().alias("weeks_since_start")
        ])
    else:
        # Rolling intervals - just use the first date in the data
        # Calculate weeks since the first date (rolling)
        df = df.with_columns([
            ((pl.col("open_time").cast(pl.Date) - pl.lit(first_date.date())).dt.total_days() / 7).floor().alias("weeks_since_start")
        ])
    
    # Create interval groups
    df = df.with_columns([
        (pl.col("weeks_since_start") / interval_weeks).floor().alias("interval_group")
    ])
    
    # Group by symbol and interval
    result = df.group_by(["symbol", "interval_group"]).agg([
        pl.col("open_time").min().alias("begin_date"),
        pl.col("open_time").max().alias("end_date"),
        pl.col("quote_volume").mean().alias("adv"),
        pl.col("open_time").count().alias("day_count")
    ])
    
    # Sort by interval and symbol first to get interval boundaries
    result = result.sort(["interval_group", "symbol"])
    
    # For each interval_group, determine the true start time (earliest 00:00:00 across all symbols)
    interval_starts = df.group_by("interval_group").agg([
        pl.col("open_time").min().alias("interval_true_start")
    ])
    
    # Join to get the true interval start for each symbol
    result = result.join(interval_starts, on="interval_group", how="left")
    
    # Filter: keep only symbols whose begin_date matches the interval's true start
    # This eliminates symbols that were listed mid-interval
    result = result.filter(pl.col("begin_date") == pl.col("interval_true_start"))
    
    # Calculate expected number of days in the interval
    result = result.with_columns([
        ((pl.col("end_date") - pl.col("begin_date")).dt.total_days() + 1).alias("interval_days")
    ])
    
    # Filter out symbols that don't have data for at least 90% of the interval
    # This handles cases where symbols are delisted mid-interval
    min_days_threshold = int(interval_weeks * 7 * 0.9)
    result = result.filter(pl.col("day_count") >= min_days_threshold)
    
    # Drop temporary columns
    result = result.drop(["interval_group", "day_count", "interval_days", "interval_true_start"])
    
    # If top_n is specified, filter to top N symbols per interval and calculate weights
    if top_n is not None:
        # Create a unique interval identifier from begin_date and end_date
        result = result.with_columns([
            (pl.col("begin_date").dt.strftime("%Y-%m-%d") + "_" + 
             pl.col("end_date").dt.strftime("%Y-%m-%d")).alias("interval_id")
        ])
        
        # For each interval, rank symbols by ADV
        result = result.with_columns([
            pl.col("adv").rank(method="ordinal", descending=True)
            .over("interval_id")
            .alias("rank")
        ])
        
        # Filter to top N
        result = result.filter(pl.col("rank") <= top_n)
        
        # If drop_n is specified, drop the top drop_n symbols
        if drop_n > 0:
            # Filter out ranks 1 through drop_n
            result = result.filter(pl.col("rank") > drop_n)
        
        # Calculate weights: weight_i = adv_i / sum(remaining adv) for each interval
        result = result.with_columns([
            (pl.col("adv") / pl.col("adv").sum().over("interval_id")).alias("weight")
        ])
        
        # Drop temporary interval_id column
        result = result.drop(["interval_id"])
        
        # Sort by begin_date, then by rank
        result = result.sort(["begin_date", "rank"])
        
        # Reorder columns with weight and rank
        result = result.select(["begin_date", "end_date", "symbol", "adv", "rank", "weight"])
    else:
        # Sort by begin_date, then by adv descending
        result = result.sort(["begin_date", "adv"], descending=[False, True])
        
        # Reorder columns without weight
        result = result.select(["begin_date", "end_date", "symbol", "adv"])
    
    return result


def format_output(df: pl.DataFrame, human_readable: bool = True) -> str:
    """
    Format the output for display.
    
    Args:
        df: Result DataFrame
        human_readable: If True, format numbers with commas and $
        
    Returns:
        Formatted string
    """
    if human_readable:
        # Format for human readability - keep dates as dates, just format ADV
        output_df = df.with_columns([
            pl.col("adv").map_elements(lambda x: f"${x:,.2f}", return_dtype=pl.Utf8).alias("adv")
        ])
        return str(output_df)
    else:
        # Keep original format for CSV output
        return df.write_csv()


def plot_adv(df: pl.DataFrame, output_path: Path, top_symbols: int = 10):
    """
    Create visualizations of ADV over time.
    
    Args:
        df: Result DataFrame with ADV calculations
        output_path: Path to save the plot
        top_symbols: Number of top symbols to plot (default: 10)
    """
    # Convert to pandas for easier plotting
    pdf = df.to_pandas()
    
    # Get top symbols by total ADV
    symbol_totals = pdf.groupby('symbol')['adv'].sum().sort_values(ascending=False)
    top_syms = symbol_totals.head(top_symbols).index.tolist()
    
    # Filter to top symbols
    plot_df = pdf[pdf['symbol'].isin(top_syms)].copy()
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # Plot 1: ADV over time for each symbol
    ax1 = axes[0]
    for symbol in top_syms:
        sym_data = plot_df[plot_df['symbol'] == symbol].sort_values('begin_date')
        ax1.plot(sym_data['begin_date'], sym_data['adv'] / 1e9, 
                marker='o', markersize=4, label=symbol, linewidth=2, alpha=0.7)
    
    ax1.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Average Daily Volume (Billions USD)', fontsize=12, fontweight='bold')
    ax1.set_title(f'Top {top_symbols} Symbols by Average Daily Volume Over Time', 
                  fontsize=14, fontweight='bold', pad=20)
    ax1.legend(loc='best', fontsize=9, ncol=2)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Plot 2: Stacked area chart showing market share
    ax2 = axes[1]
    pivot_df = plot_df.pivot_table(index='begin_date', columns='symbol', values='adv', fill_value=0)
    pivot_df = pivot_df[top_syms]  # Ensure correct order
    
    ax2.stackplot(pivot_df.index, *[pivot_df[col] / 1e9 for col in pivot_df.columns], 
                  labels=pivot_df.columns, alpha=0.7)
    
    ax2.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Average Daily Volume (Billions USD)', fontsize=12, fontweight='bold')
    ax2.set_title(f'Market Share: Top {top_symbols} Symbols ADV (Stacked)', 
                  fontsize=14, fontweight='bold', pad=20)
    ax2.legend(loc='best', fontsize=9, ncol=2)
    ax2.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n📊 Plot saved to: {output_path}")
    plt.close()


def plot_weights(df: pl.DataFrame, output_path: Path, num_intervals: int = 20):
    """
    Create visualization of symbol weights over time.
    
    Args:
        df: Result DataFrame with weights
        output_path: Path to save the plot
        num_intervals: Number of recent intervals to plot (default: 20)
    """
    if 'weight' not in df.columns:
        print("⚠️  No weights to plot (weights only available with --nsymbols)")
        return
    
    # Convert to pandas for easier plotting
    pdf = df.to_pandas()
    
    # Get the most recent intervals
    unique_dates = pdf['begin_date'].unique()
    unique_dates = sorted(unique_dates)[-num_intervals:]
    plot_df = pdf[pdf['begin_date'].isin(unique_dates)].copy()
    
    # Create figure
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Create stacked bar chart
    pivot_df = plot_df.pivot_table(index='begin_date', columns='symbol', values='weight', fill_value=0)
    
    # Plot stacked bars
    pivot_df.plot(kind='bar', stacked=True, ax=ax, width=0.8, alpha=0.8)
    
    ax.set_xlabel('Interval Start Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Weight (Portfolio Allocation)', fontsize=12, fontweight='bold')
    ax.set_title('Symbol Weights Over Time (Each Bar Sums to 1.0)', 
                 fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=9)
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')
    ax.set_ylim(0, 1.0)
    
    # Format x-axis
    labels = [d.strftime('%Y-%m-%d') if isinstance(d, datetime) else str(d) 
              for d in pivot_df.index]
    ax.set_xticklabels(labels, rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"📊 Weights plot saved to: {output_path}")
    plt.close()


def main():
    """Main function to calculate ADV."""
    parser = argparse.ArgumentParser(
        description="Calculate Average Daily Volume (ADV) from aggregate daily data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Calculate monthly ADV for all USDT symbols (default)
  python calc_adv.py --input-file /workspace/data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq
  
  # Calculate monthly ADV for all symbols (disable suffix filter)
  python calc_adv.py --input-file AGG.pq --suffix ''
  
  # Calculate monthly ADV for USDC symbols
  python calc_adv.py --input-file AGG.pq --suffix USDC
  
  # Calculate monthly ADV and save (generates ADV_1_MONTH_2024-07-01_2025-09-30.pq)
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --output-dir /workspace/data/klines_aggregate
  
  # Calculate 1-week ADV (rolling, starts from first date in data)
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --interval 1 --units weeks --output-dir /workspace/data
  
  # Calculate 1-week ADV aligned to start of month
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --interval 1 --units weeks --start-of-month --output-dir /workspace/data
  
  # Calculate 1-week ADV starting every Monday (consistent across years)
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --interval 1 --units weeks --index-start-day monday --output-dir /workspace/data
  
  # Calculate 2-week ADV starting every Monday
  python calc_adv.py --input-file AGG.pq --interval 2 --units weeks --index-start-day monday
  
  # Calculate 3-month ADV
  python calc_adv.py --input-file AGG.pq --interval 3
  
  # Calculate 6-month ADV for BTC symbols (prefix filter)
  python calc_adv.py --input-file AGG.pq --interval 6 --symbol BTC
  
  # Top 10 USDT symbols by ADV per month with weights (generates WEIGHTS_10_1_MONTH_2024-07-01_2025-09-30.pq)
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --nsymbols 10 --output-dir /workspace/data/klines_aggregate
  
  # Top 25 USDT symbols per week with weights (generates WEIGHTS_25_1_WEEK_2024-07-01_2025-09-30.pq)
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --interval 1 --units weeks --nsymbols 25 --output-dir /workspace/data
  
  # Generate plots showing top 10 symbols over time
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --plot --plot-symbols 10
  
  # Calculate weekly ADV for top 25, save data and generate plots
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --interval 1 --units weeks --nsymbols 25 --output-dir /workspace/data --plot
        """
    )
    parser.add_argument(
        "--input-file",
        type=str,
        required=True,
        help="Path to aggregate parquet file"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=1,
        help="Interval length (default: 1)"
    )
    parser.add_argument(
        "--units",
        type=str,
        default="months",
        choices=["months", "weeks"],
        help="Interval units: 'months' or 'weeks' (default: months)"
    )
    parser.add_argument(
        "--start-of-month",
        action="store_true",
        help="For weekly intervals, align to start of month instead of rolling (default: rolling)"
    )
    parser.add_argument(
        "--index-start-day",
        type=str,
        choices=["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
        help="Day of week to start weekly intervals (e.g., monday). Ensures consistent rolling across years. Overrides --start-of-month."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Optional output directory (if not specified, prints to stdout). "
             "Filename is auto-generated: ADV_<interval>_<units>_<dates>.pq or WEIGHTS_<nsymbols>_<interval>_<units>_<dates>.pq"
    )
    parser.add_argument(
        "--symbol",
        type=str,
        help="Filter to symbols starting with this prefix (e.g., BTC, ETH)"
    )
    parser.add_argument(
        "--suffix",
        type=str,
        default="USDT",
        help="Filter to symbols ending with this suffix (default: USDT). Use empty string '' to disable filtering."
    )
    parser.add_argument(
        "--nsymbols",
        type=int,
        help="Keep only top N symbols by ADV per interval and calculate weights"
    )
    parser.add_argument(
        "--drop-n",
        type=int,
        default=0,
        help="Drop the top N symbols before calculating weights (default: 0). "
             "Requires --nsymbols. Example: --nsymbols 50 --drop-n 10 gives you ranks 11-50 (40 symbols)."
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate visualization plots of ADV over time"
    )
    parser.add_argument(
        "--plot-symbols",
        type=int,
        default=10,
        help="Number of top symbols to include in plots (default: 10)"
    )
    parser.add_argument(
        "--show-all",
        action="store_true",
        help="Display all rows in output (no truncation)"
    )
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        return
    
    # Validate interval
    if args.interval < 1:
        print(f"❌ Error: Interval must be at least 1")
        return
    
    # Validate nsymbols
    if args.nsymbols is not None and args.nsymbols < 1:
        print(f"❌ Error: nsymbols must be at least 1")
        return
    
    # Validate drop_n
    if args.drop_n < 0:
        print(f"❌ Error: drop-n must be non-negative")
        return
    
    if args.drop_n > 0 and args.nsymbols is None:
        print(f"❌ Error: --drop-n requires --nsymbols to be specified")
        return
    
    if args.drop_n > 0 and args.nsymbols is not None and args.drop_n >= args.nsymbols:
        print(f"❌ Error: drop-n ({args.drop_n}) must be less than nsymbols ({args.nsymbols})")
        return
    
    print(f"📖 Reading data from: {input_path.name}")
    
    # Read the aggregate file
    try:
        df = pl.read_parquet(input_path)
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    print(f"   Total rows: {len(df):,}")
    print(f"   Total symbols: {df['symbol'].n_unique()}")
    
    # Filter by suffix (default: USDT)
    if args.suffix:
        df = df.filter(pl.col("symbol").str.ends_with(args.suffix.upper()))
        print(f"   Filtered to symbols ending with '{args.suffix.upper()}': {df['symbol'].n_unique()}")
    
    # Filter by symbol prefix if requested
    if args.symbol:
        df = df.filter(pl.col("symbol").str.starts_with(args.symbol.upper()))
        print(f"   Filtered to symbols starting with '{args.symbol.upper()}': {df['symbol'].n_unique()}")
    
    # Calculate ADV
    units_label = "month" if args.interval == 1 else "months"
    if args.units == "weeks":
        units_label = "week" if args.interval == 1 else "weeks"
    
    if args.nsymbols:
        if args.drop_n > 0:
            remaining_symbols = args.nsymbols - args.drop_n
            print(f"\n📊 Calculating {args.interval}-{units_label} ADV (top {args.nsymbols}, dropping top {args.drop_n}, keeping ranks {args.drop_n + 1}-{args.nsymbols}: {remaining_symbols} symbols)...")
        else:
            print(f"\n📊 Calculating {args.interval}-{units_label} ADV (top {args.nsymbols} symbols per interval)...")
    else:
        print(f"\n📊 Calculating {args.interval}-{units_label} ADV...")
    
    try:
        result = calculate_adv(df, args.interval, args.units, args.start_of_month, args.index_start_day, args.nsymbols, args.drop_n)
    except Exception as e:
        print(f"❌ Error calculating ADV: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"   Calculated ADV for {result['symbol'].n_unique()} unique symbols")
    print(f"   Total periods: {len(result):,}")
    
    if args.nsymbols:
        if args.drop_n > 0:
            print(f"   Filtered to ranks {args.drop_n + 1}-{args.nsymbols} (dropped top {args.drop_n})")
        else:
            print(f"   Filtered to top {args.nsymbols} symbols per interval")
        print(f"   Weights calculated (sum to 1.0 per interval)")
    
    # Generate plots if requested
    if args.plot:
        print("\n📊 Generating plots...")
        try:
            # Determine output directory for plots
            if args.output_dir:
                plot_dir = Path(args.output_dir)
            else:
                plot_dir = input_path.parent
            
            # Extract filename components
            input_name = input_path.stem
            parts = input_name.split('_')
            date_suffix = ""
            if len(parts) >= 3:
                date_suffix = f"_{parts[-2]}_{parts[-1]}"
            
            units_upper = args.units.upper()
            if args.interval == 1:
                units_suffix = units_upper.rstrip('S')
            else:
                units_suffix = units_upper + 'S' if not units_upper.endswith('S') else units_upper
            
            # Generate ADV plot
            plot_filename = f"ADV_PLOT_{args.interval}_{units_suffix}{date_suffix}.png"
            plot_path = plot_dir / plot_filename
            plot_adv(result, plot_path, top_symbols=args.plot_symbols)
            
            # Generate weights plot if applicable
            if args.nsymbols:
                weights_plot_filename = f"WEIGHTS_PLOT_{args.nsymbols}_{args.interval}_{units_suffix}{date_suffix}.png"
                weights_plot_path = plot_dir / weights_plot_filename
                plot_weights(result, weights_plot_path)
                
        except Exception as e:
            print(f"⚠️  Error generating plots: {e}")
            import traceback
            traceback.print_exc()
    
    # Output results
    if args.output_dir:
        # Generate output filename from input filename
        output_dir = Path(args.output_dir)
        
        # Extract date range from input filename (e.g., AGG_2024-07-01_2025-09-30.pq)
        input_name = input_path.stem  # Remove .pq extension
        
        # Try to extract dates from filename pattern: PREFIX_YYYY-MM-DD_YYYY-MM-DD
        date_suffix = ""
        parts = input_name.split('_')
        if len(parts) >= 3:
            # Assume last two parts are dates
            date_suffix = f"_{parts[-2]}_{parts[-1]}"
        
        # Generate units suffix (singular vs plural)
        units_upper = args.units.upper()
        if args.interval == 1:
            # Singular form: MONTH or WEEK
            units_suffix = units_upper.rstrip('S')
        else:
            # Plural form: MONTHS or WEEKS
            if not units_upper.endswith('S'):
                units_suffix = units_upper + 'S'
            else:
                units_suffix = units_upper
        
        # Generate output filename based on computation type
        if args.nsymbols:
            if args.drop_n > 0:
                # Include drop_n in filename: WEIGHTS_50_DROP10_1_MONTH_...
                output_filename = f"WEIGHTS_{args.nsymbols}_DROP{args.drop_n}_{args.interval}_{units_suffix}{date_suffix}.pq"
            else:
                output_filename = f"WEIGHTS_{args.nsymbols}_{args.interval}_{units_suffix}{date_suffix}.pq"
        else:
            output_filename = f"ADV_{args.interval}_{units_suffix}{date_suffix}.pq"
        
        output_path = output_dir / output_filename
        
        try:
            # Write to parquet file
            result.write_parquet(str(output_path))
            print(f"\n✅ Wrote output to: {output_path}")
            
            # Show summary statistics
            print(f"\n📈 Summary Statistics:")
            print(f"   Min ADV: ${result['adv'].min():,.2f}")
            print(f"   Max ADV: ${result['adv'].max():,.2f}")
            print(f"   Mean ADV: ${result['adv'].mean():,.2f}")
            print(f"   Median ADV: ${result['adv'].median():,.2f}")
            
        except Exception as e:
            print(f"❌ Error writing output file: {e}")
    else:
        # Print to stdout with proper formatting
        print(f"\n{'='*80}")
        print("AVERAGE DAILY VOLUME (ADV)")
        print('='*80)
        print()
        
        # Configure Polars display options if showing all rows
        if args.show_all:
            with pl.Config(
                tbl_rows=-1,  # Show all rows
                tbl_cols=-1,  # Show all columns
                fmt_str_lengths=100  # Show longer strings
            ):
                print(result)
        else:
            print(result)
        
        print()
        print(f"{'='*80}")
        print(f"Note: ADV is in USD (quote_volume)")
        print(f"Interval: {args.interval} {args.units}")
        print(f"Date columns are Date type, ADV is Float64")
        if args.show_all:
            print(f"Showing all {len(result)} rows")
        print('='*80)


if __name__ == "__main__":
    main()
