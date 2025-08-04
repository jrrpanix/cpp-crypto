from pl_loaders import load_all_parquet_files
import polars as pl
from datetime import datetime
from patterns import count_intervals, summary

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python calc.py <parquet_directory> [window] [threshold]")
        return
    parquet_dir = sys.argv[1]
    window = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.05
    df = load_all_parquet_files(parquet_dir)
    if df is None or df.height == 0:
        print("No parquet files loaded.")
        return
    stats = summary(df)
    up_count, down_count, up_follow_count, down_follow_count = count_intervals(df, "close", window=window, threshold=threshold)
    stats['up_count'] = up_count
    stats['down_count'] = down_count
    stats['up_follow_count'] = up_follow_count
    stats['down_follow_count'] = down_follow_count
    print("Summary statistics:")
    print(f"Up intervals ({window} rows, {threshold*100:.2f}%): {up_count}")
    print(f"Up intervals followed by up: {up_follow_count} ({(up_follow_count/up_count*100 if up_count else 0):.2f}%)")
    print(f"Down intervals ({window} rows, {threshold*100:.2f}%): {down_count}")
    print(f"Down intervals followed by down: {down_follow_count} ({(down_follow_count/down_count*100 if down_count else 0):.2f}%)")
    print("Detailed statistics:")
    print(f"Total rows: {stats['total_rows']} | Date range: {stats['min_date']} to {stats['max_date']}")
    print(f"Starting price: {stats.get('open_price')} occurs on date {stats.get('open_price_date')}")
    print(f"Min price (low): {stats.get('min_price')} occurs on date {stats.get('min_price_date')}")
    print(f"Max price (high): {stats.get('max_price')} occurs on date {stats.get('max_price_date')}")
    print(f"Ending price: {stats.get('close_price')} occurs on date {stats.get('close_price_date')}")

if __name__ == "__main__":
    main()

