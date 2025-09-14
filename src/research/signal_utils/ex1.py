import sys
import os
from trade_move import symbol_trade_move
import polars as pl


def main():
    if len(sys.argv) < 6:
        print(
            "Usage: python ex1.py <parquet_directory> <window> <threshold> <holding_horizon> <price_type>"
        )
        return
    parquet_dir = sys.argv[1]
    window = int(sys.argv[2])
    threshold = float(sys.argv[3])
    holding_horizon = int(sys.argv[4])
    price_type = sys.argv[5]
    result_dicts = []
    symbol_names = []
    # Get all symbol names from files and sort
    file_names = [f for f in os.listdir(parquet_dir) if f.endswith(".parquet")]
    symbol_names_sorted = sorted([fn.split("_")[0] for fn in file_names])
    running_total_after_fees = 0.0
    for symbol_name in symbol_names_sorted:
        try:
            _, summary = symbol_trade_move(
                parquet_dir, symbol_name, window, threshold, holding_horizon, price_type
            )
            summary["symbol"] = symbol_name
            result_dicts.append(summary)
            symbol_names.append(symbol_name)
            running_total_after_fees += summary["total_profit_after_fees"]
            print(
                f"Processed {symbol_name}: Total PnL after fees = {summary['total_profit_after_fees']:.2f} | Running total after fees = {running_total_after_fees:.2f}"
            )
        except Exception as e:
            print(f"Error processing {symbol_name}: {e}")
    if not result_dicts:
        print("No symbols processed.")
        return
    df = pl.DataFrame(result_dicts)
    print("\nSymbol summary DataFrame:")
    print(df)
    # Print aggregate stats
    total_symbols = len(symbol_names)
    total_pnl_before = df["total_profit_before_fees"].sum()
    total_fees = df["total_transaction_fees"].sum()
    total_pnl_after = df["total_profit_after_fees"].sum()
    total_trade_volume = df["total_dollar_volume"].sum()
    print(f"\nNumber of symbols processed: {total_symbols}")
    print(f"Total PnL before fees: {total_pnl_before:.2f}")
    print(f"Total transaction fees: {total_fees:.2f}")
    print(f"Total PnL after fees: {total_pnl_after:.2f}")
    print(f"Total trade volume: {total_trade_volume:.2f}")


if __name__ == "__main__":
    main()
