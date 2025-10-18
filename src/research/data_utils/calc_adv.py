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


def calculate_adv(
    df: pl.DataFrame,
    interval_months: int = 1,
    top_n: int = None
) -> pl.DataFrame:
    """
    Calculate Average Daily Volume over intervals.
    
    Args:
        df: DataFrame with daily data (must have open_time, symbol, quote_volume)
        interval_months: Number of months per interval (default: 1)
        top_n: If specified, keep only top N symbols by ADV per interval and add weights
        
    Returns:
        DataFrame with columns: begin_date, end_date, symbol, adv, [weight]
        Weight column is added if top_n is specified
    """
    # Add year and month columns for grouping
    df = df.with_columns([
        pl.col("open_time").dt.year().alias("year"),
        pl.col("open_time").dt.month().alias("month")
    ])
    
    if interval_months == 1:
        # Monthly intervals - group by year and month
        result = df.group_by(["symbol", "year", "month"]).agg([
            pl.col("quote_volume").mean().alias("adv")
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
        
        # Drop temporary columns
        result = result.drop(["next_year", "next_month"])
        
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
            pl.col("quote_volume").mean().alias("adv")
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
        
        # Sort by interval and symbol
        result = result.sort(["interval_group", "symbol"])
        
        # Drop temporary columns
        result = result.drop(["interval_group", "start_year", "start_month", "end_year", "end_month", "next_year", "next_month"])
    
    
    # If top_n is specified, filter to top N symbols per interval and calculate weights
    if top_n is not None:
        # Create a unique interval identifier from begin_date and end_date
        result = result.with_columns([
            (pl.col("begin_date").dt.strftime("%Y-%m-%d") + "_" + 
             pl.col("end_date").dt.strftime("%Y-%m-%d")).alias("interval_id")
        ])
        
        # For each interval, rank symbols by ADV and keep top N
        result = result.with_columns([
            pl.col("adv").rank(method="ordinal", descending=True)
            .over("interval_id")
            .alias("rank")
        ])
        
        # Filter to top N
        result = result.filter(pl.col("rank") <= top_n)
        
        # Calculate weights: weight_i = adv_i / sum(top N adv) for each interval
        result = result.with_columns([
            (pl.col("adv") / pl.col("adv").sum().over("interval_id")).alias("weight")
        ])
        
        # Drop temporary columns
        result = result.drop(["interval_id", "rank", "year", "month"])
        
        # Sort by begin_date, then by adv descending
        result = result.sort(["begin_date", "adv"], descending=[False, True])
        
        # Reorder columns with weight
        result = result.select(["begin_date", "end_date", "symbol", "adv", "weight"])
    else:
        # Drop year and month columns
        result = result.drop(["year", "month"])
        
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
        # Format for human readability
        output_df = df.with_columns([
            pl.col("begin_date").dt.strftime("%Y-%m-%d").alias("begin_date"),
            pl.col("end_date").dt.strftime("%Y-%m-%d").alias("end_date"),
            pl.col("adv").map_elements(lambda x: f"${x:,.2f}", return_dtype=pl.Utf8).alias("adv")
        ])
        return str(output_df)
    else:
        # Keep original format for CSV output
        return df.write_csv()


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
  
  # Calculate monthly ADV and save to file (generates ADV_2024-07-01_2025-09-30.pq)
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --output-dir /workspace/data/klines_aggregate
  
  # Calculate 3-month ADV
  python calc_adv.py --input-file AGG.pq --interval 3
  
  # Calculate 6-month ADV for BTC symbols (prefix filter)
  python calc_adv.py --input-file AGG.pq --interval 6 --symbol BTC
  
  # Calculate quarterly ADV (3 months) and save
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --interval 3 --output-dir /workspace/data
  
  # Top 10 USDT symbols by ADV per month with weights (generates WEIGHTS_10_2024-07-01_2025-09-30.pq)
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --nsymbols 10 --output-dir /workspace/data/klines_aggregate
  
  # Top 20 USDT symbols quarterly with weights (generates WEIGHTS_20_2024-07-01_2025-09-30.pq)
  python calc_adv.py --input-file AGG_2024-07-01_2025-09-30.pq --interval 3 --nsymbols 20 --output-dir /workspace/data
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
        help="Interval in months (default: 1 for monthly)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Optional output directory (if not specified, prints to stdout). "
             "Filename is auto-generated: ADV_<dates>.pq or WEIGHTS_<nsymbols>_<dates>.pq"
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
    
    args = parser.parse_args()
    
    # Validate input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"❌ Error: Input file not found: {input_path}")
        return
    
    # Validate interval
    if args.interval < 1:
        print(f"❌ Error: Interval must be at least 1 month")
        return
    
    # Validate nsymbols
    if args.nsymbols is not None and args.nsymbols < 1:
        print(f"❌ Error: nsymbols must be at least 1")
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
    if args.nsymbols:
        print(f"\n📊 Calculating {args.interval}-month ADV (top {args.nsymbols} symbols per interval)...")
    else:
        print(f"\n📊 Calculating {args.interval}-month ADV...")
    
    try:
        result = calculate_adv(df, args.interval, args.nsymbols)
    except Exception as e:
        print(f"❌ Error calculating ADV: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print(f"   Calculated ADV for {result['symbol'].n_unique()} unique symbols")
    print(f"   Total periods: {len(result):,}")
    
    if args.nsymbols:
        print(f"   Filtered to top {args.nsymbols} symbols per interval")
        print(f"   Weights calculated (sum to 1.0 per interval)")
    
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
        
        # Generate output filename based on computation type
        if args.nsymbols:
            output_filename = f"WEIGHTS_{args.nsymbols}{date_suffix}.pq"
        else:
            output_filename = f"ADV{date_suffix}.pq"
        
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
        # Print to stdout
        print(f"\n{'='*80}")
        print("AVERAGE DAILY VOLUME (ADV)")
        print('='*80)
        print()
        print(format_output(result, human_readable=True))
        print()
        print(f"{'='*80}")
        print(f"Note: ADV is in USD (quote_volume)")
        print(f"Interval: {args.interval} month(s)")
        print('='*80)


if __name__ == "__main__":
    main()
