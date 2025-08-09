import polars as pl
from moves import trigger
from patterns import summary
import os

def main():
    import sys
    if len(sys.argv) < 6:
        print("Usage: python calc3.py <parquet_directory> <symbol> <window> <threshold> <holding_horizon>")
        return
    parquet_dir = sys.argv[1]
    symbol = sys.argv[2]
    window = int(sys.argv[3])
    threshold = float(sys.argv[4])
    holding_horizon = int(sys.argv[5])
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
    # Call trigger function from moves.py
    start_df, end_df = trigger(df, window, threshold)
    print(f"\nTrigger results (window={window}, threshold={threshold}):")
    print(f"Number of triggers: {start_df.height}")
    if start_df.height > 0:
        print("First 5 start rows:")
        print(start_df)
        print("First 5 end rows:")
        print(end_df)
        # Call trade_move
        from trade_move import trade_move
        trade_type = "buy" if threshold > 0 else "sell"
        trade_df = trade_move(
            df, end_df,
            window=window,  # pass single window value
            holding_horizon=holding_horizon,
            entry_price_type="close",
            exit_price_type="close",
            trade_type=trade_type,
            dollar_amount=1000.0
        )
        print("\nTrade simulation results:")
        print(trade_df)
        # Print total profit
        total_profit = trade_df['profit'].sum() if 'profit' in trade_df.columns else 0.0
        num_trades = trade_df.height
        num_winners = (trade_df['profit'] > 0).sum()
        num_losers = (trade_df['profit'] < 0).sum()
        win_loss_ratio = num_winners / num_losers if num_losers > 0 else float('inf')
        print(f"Total profit from all simulated trades: {total_profit:.2f}")
        print(f"Number of trades: {num_trades}")
        print(f"Number of winners (profit > 0): {num_winners}")
        print(f"Number of losers (profit < 0): {num_losers}")
        print(f"Win/Loss ratio: {win_loss_ratio:.2f}")

if __name__ == "__main__":
    main()
