import sys
from trade_move import symbol_trade_move


def main():
    if len(sys.argv) < 7:
        print(
            "Usage: python calc4.py <parquet_directory> <symbol> <window> <threshold> <holding_horizon> <price_type>"
        )
        return
    parquet_dir = sys.argv[1]
    symbol = sys.argv[2]
    window = int(sys.argv[3])
    threshold = float(sys.argv[4])
    holding_horizon = int(sys.argv[5])
    price_type = sys.argv[6]
    try:
        trade_df, summary = symbol_trade_move(
            parquet_dir, symbol, window, threshold, holding_horizon, price_type
        )
    except Exception as e:
        print(f"Error: {e}")
        return
    print("\nTrade simulation results:")
    print(trade_df)
    print("\nTrade summary:")
    print(
        f"Total rows: {summary['summary_stats']['total_rows']} | Date range: {summary['summary_stats']['min_date']} to {summary['summary_stats']['max_date']}"
    )
    print(
        f"Starting price: {summary['summary_stats'].get('open_price')} occurs on date {summary['summary_stats'].get('open_price_date')}"
    )
    print(
        f"Min price (low): {summary['summary_stats'].get('min_price')} occurs on date {summary['summary_stats'].get('min_price_date')}"
    )
    print(
        f"Max price (high): {summary['summary_stats'].get('max_price')} occurs on date {summary['summary_stats'].get('max_price_date')}"
    )
    print(
        f"Ending price: {summary['summary_stats'].get('close_price')} occurs on date {summary['summary_stats'].get('close_price_date')}"
    )
    print(f"Number of triggers: {summary['num_triggers']}")
    print(f"Total dollar trade volume (entry): {summary['total_dollar_entry']}")
    print(f"Total dollar trade volume (exit): {summary['total_dollar_exit']}")
    print(f"Total dollar trade volume (entry + exit): {summary['total_dollar_volume']}")
    print(
        f"Total profit before transaction costs: {summary['total_profit_before_fees']}"
    )
    print(f"Total transaction fees: {summary['total_transaction_fees']}")
    print(f"Total profit after transaction costs: {summary['total_profit_after_fees']}")
    print(f"Number of trades: {summary['num_trades']}")
    print(f"Number of winners (profit > 0): {summary['num_winners']}")
    print(f"Number of losers (profit < 0): {summary['num_losers']}")
    print(f"Win/Loss ratio: {summary['win_loss_ratio']}")
    print(f"Average profit per trade before fees: {summary['avg_profit_before_fees']}")
    print(f"Average profit per trade after fees: {summary['avg_profit_after_fees']}")


if __name__ == "__main__":
    main()
