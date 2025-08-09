import polars as pl
from moves import trigger
from patterns import summary
import os

def main():
    import sys
    if len(sys.argv) < 7:
        print("Usage: python calc3.py <parquet_directory> <symbol> <window> <threshold> <holding_horizon> <price_type>")
        return
    parquet_dir = sys.argv[1]
    symbol = sys.argv[2]
    window = int(sys.argv[3])
    threshold = float(sys.argv[4])
    holding_horizon = int(sys.argv[5])
    price_type = sys.argv[6]
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
            entry_price_type=price_type,
            exit_price_type=price_type,
            trade_type=trade_type,
            dollar_amount=1000.0
        )
        print("\nTrade simulation results:")
        print(trade_df)
        # Print profit and transaction cost stats
        total_profit_before_fees = trade_df['profit'].sum() if 'profit' in trade_df.columns else 0.0
        total_entry_fees = trade_df['entry_transaction_fee'].sum() if 'entry_transaction_fee' in trade_df.columns else 0.0
        total_exit_fees = trade_df['exit_transaction_fee'].sum() if 'exit_transaction_fee' in trade_df.columns else 0.0
        total_fees = total_entry_fees + total_exit_fees
        total_profit_after_fees = total_profit_before_fees - total_fees
        total_dollar_entry = trade_df['dollar_amount_entry'].sum() if 'dollar_amount_entry' in trade_df.columns else 0.0
        total_dollar_exit = trade_df['dollar_amount_exit'].sum() if 'dollar_amount_exit' in trade_df.columns else 0.0
        num_trades = trade_df.height
        num_winners = (trade_df['profit'] > 0).sum()
        num_losers = (trade_df['profit'] < 0).sum()
        win_loss_ratio = num_winners / num_losers if num_losers > 0 else float('inf')
        avg_profit = total_profit_before_fees / num_trades if num_trades > 0 else 0.0
        def human_readable(n):
            if abs(n) >= 1e9:
                return f"{n/1e9:.2f}B"
            elif abs(n) >= 1e6:
                return f"{n/1e6:.2f}M"
            elif abs(n) >= 1e3:
                return f"{n/1e3:.2f}K"
            else:
                return f"{n:.2f}"
        print(f"Total dollar trade volume (entry): {human_readable(total_dollar_entry)}")
        print(f"Total dollar trade volume (exit): {human_readable(total_dollar_exit)}")
        total_dollar_volume = total_dollar_entry + total_dollar_exit
        print(f"Total dollar trade volume (entry + exit): {human_readable(total_dollar_volume)}")
        print(f"Total profit before transaction costs: {human_readable(total_profit_before_fees)}")
        print(f"Total transaction fees: {human_readable(total_fees)}")
        print(f"Total profit after transaction costs: {human_readable(total_profit_after_fees)}")
        print(f"Number of trades: {num_trades}")
        print(f"Number of winners (profit > 0): {num_winners}")
        print(f"Number of losers (profit < 0): {num_losers}")
        print(f"Win/Loss ratio: {win_loss_ratio:.2f}")
        print(f"Average profit per trade: {human_readable(avg_profit)}")

if __name__ == "__main__":
    main()
