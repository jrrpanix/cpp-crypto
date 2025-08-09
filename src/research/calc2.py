import polars as pl
from patterns import windowed_up_down_probabilities, summary
import os

def main():
    import sys
    if len(sys.argv) < 5:
        print("Usage: python calc2.py <parquet_directory> <symbol> <window> <threshold>")
        return
    parquet_dir = sys.argv[1]
    symbol = sys.argv[2]
    window = int(sys.argv[3])
    threshold = float(sys.argv[4])
    # Find the file for the symbol
    files = [f for f in os.listdir(parquet_dir) if f.startswith(symbol) and f.endswith('.parquet')]
    if not files:
        print(f"No parquet file found for symbol {symbol} in {parquet_dir}")
        return
    parquet_file = os.path.join(parquet_dir, files[0])
    df = pl.read_parquet(parquet_file)
    if df is None or df.height == 0:
        print("No parquet data loaded.")
        return
    stats = summary(df)
    print("Summary statistics:")
    print(f"Total rows: {stats['total_rows']} | Date range: {stats['min_date']} to {stats['max_date']}")
    print(f"Starting price: {stats.get('open_price')} occurs on date {stats.get('open_price_date')}")
    print(f"Min price (low): {stats.get('min_price')} occurs on date {stats.get('min_price_date')}")
    print(f"Max price (high): {stats.get('max_price')} occurs on date {stats.get('max_price_date')}")
    print(f"Ending price: {stats.get('close_price')} occurs on date {stats.get('close_price_date')}")
    # Call new windowed probability function
    lookaheads = [1, 5, 10, 30, 60]
    probs = windowed_up_down_probabilities(df, price_col="close", threshold=threshold, window=window, lookaheads=lookaheads)
    print(f"\nWindowed up/down probabilities (window={window}, threshold={threshold*100:.2f}%):")
    for direction in ['up', 'down']:
        print(f"{direction.capitalize()} event probabilities and profit/loss:")
        for look in lookaheads:
            prob_up = probs[direction][look]['up']
            prob_down = probs[direction][look]['down']
            profit = probs[direction][look]['profit']
            n_events = probs[direction][look].get('n_events', None)
            print(f"  {look} windows ahead: up={prob_up*100:.2f}%, down={prob_down*100:.2f}%, total profit/loss=${profit:.2f} (for $1000 per trade)" + (f", n_events={n_events}" if n_events is not None else ""))
        print()

if __name__ == "__main__":
    main()
