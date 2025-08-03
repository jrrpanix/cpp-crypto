from pl_loaders import load_all_parquet_files
import polars as pl
from datetime import datetime
from patterns import count_intervals, summary

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python calc.py <parquet_directory>")
        return
    parquet_dir = sys.argv[1]
    df = load_all_parquet_files(parquet_dir)
    if df is None or df.height == 0:
        print("No parquet files loaded.")
        return
    stats = summary(df)
    print(f"Total rows: {stats['total_rows']} | Date range: {stats['min_date']} to {stats['max_date']}")
    print(f"Starting price: {stats.get('open_price')} occurs on date {stats.get('open_price_date')}")
    print(f"Min price (low): {stats.get('min_price')} occurs on date {stats.get('min_price_date')}")
    print(f"Max price (high): {stats.get('max_price')} occurs on date {stats.get('max_price_date')}")
    print(f"Ending price: {stats.get('close_price')} occurs on date {stats.get('close_price_date')}")

if __name__ == "__main__":
    main()

