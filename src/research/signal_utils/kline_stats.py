import argparse
import os

import matplotlib.pyplot as plt
import polars as pl
from scipy.signal import savgol_filter


def get_kline_stats(file_path: str, plot: bool = False, ema_window: int = None, sg_params=None):
    """
    Reads a Parquet kline file and prints statistics.
    Optionally plots the daily closing price and smoothed versions.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at '{file_path}'")
        return

    try:
        # Read the Parquet file
        df = pl.read_parquet(file_path)

        # --- Calculate Statistics ---
        start_time = df.select(pl.col("open_time").min()).item()
        end_time = df.select(pl.col("close_time").max()).item()
        initial_price = df.select(pl.col("open").first()).item()
        ending_price = df.select(pl.col("close").last()).item()
        min_price = df.select(pl.col("low").min()).item()
        max_price = df.select(pl.col("high").max()).item()
        total_volume = df.select(pl.col("volume").sum()).item()
        num_rows = df.height

        # Calculate the number of days
        duration = end_time - start_time
        num_days = duration.days

        # --- Print Statistics ---
        print(f"📊 Statistics for: {os.path.basename(file_path)}")
        print("-" * 40)
        print(f"  Start Time:       {start_time}")
        print(f"  End Time:         {end_time}")
        print(f"  Duration (days):  {num_days}")
        print(f"  Number of Rows:   {num_rows:,}")
        print(f"  Initial Price:    {initial_price:,.4f}")
        print(f"  Ending Price:     {ending_price:,.4f}")
        print(f"  Min Price:        {min_price:,.4f}")
        print(f"  Max Price:        {max_price:,.4f}")
        print(f"  Total Volume:     {total_volume:,.2f}")
        print("-" * 40)

        # --- Plotting ---
        if plot:
            print("📈 Generating plot...")
            # Resample to daily, taking the last close price of each day
            daily_close = df.group_by_dynamic("open_time", every="1d").agg(pl.col("close").last())

            plt.figure(figsize=(15, 7))
            plt.plot(daily_close["open_time"], daily_close["close"], label="Daily Close", alpha=0.4)

            # --- Smoothing ---
            if ema_window and ema_window > 0:
                daily_close = daily_close.with_columns(
                    pl.col("close").ewm_mean(span=ema_window).alias(f"{ema_window}-Day EMA")
                )
                plt.plot(
                    daily_close["open_time"],
                    daily_close[f"{ema_window}-Day EMA"],
                    label=f"{ema_window}-Day EMA",
                )

            if sg_params:
                for window, polyorder in sg_params:
                    if window > polyorder and window % 2 != 0:
                        sg_filtered = savgol_filter(daily_close["close"], window, polyorder)
                        col_name = f"sg_filter_{window}_{polyorder}"
                        daily_close = daily_close.with_columns(
                            pl.Series(name=col_name, values=sg_filtered)
                        )
                        plt.plot(
                            daily_close["open_time"],
                            daily_close[col_name],
                            label=f"SG Filter (w={window}, p={polyorder})",
                        )
                    else:
                        print(
                            f"⚠️ SG filter window must be an odd number and greater than the polyorder (w={window}, p={polyorder}). Skipping."
                        )
            # --- END ---

            # --- Generate Filename and Save Plot ---
            base_name = os.path.basename(file_path)
            symbol = base_name.split("_")[0]
            plot_filename = f"{symbol}.png"

            plt.title(f"Daily Close Price for {symbol}")
            plt.xlabel("Date")
            plt.ylabel("Close Price (USD)")
            plt.grid(True)
            plt.legend()

            plt.savefig(plot_filename)
            plt.close()  # Close the figure to free up memory
            print(f"✅ Plot saved to {plot_filename}")
            # --- END ---

    except Exception as e:
        print(f"❌ An error occurred: {e}")


def main():
    """
    Main function to parse arguments and run the stats calculation.
    """
    parser = argparse.ArgumentParser(
        description="Calculate and display statistics for a Binance kline Parquet file."
    )
    parser.add_argument("parquet_file", type=str, help="Path to the Parquet kline file.")
    parser.add_argument(
        "--plot", action="store_true", help="Display a plot of the daily closing prices."
    )
    parser.add_argument(
        "--ema",
        type=int,
        nargs="?",
        const=7,
        default=None,
        help="Apply an Exponential Moving Average. Provide an optional window size (default: 7).",
    )
    parser.add_argument(
        "--sg",
        type=int,
        nargs=2,
        metavar=("window", "polyorder"),
        action="append",
        help="Apply a Savitzky-Golay filter. Can be used multiple times. Provide window size and polyorder (e.g., --sg 7 3).",
    )
    args = parser.parse_args()

    get_kline_stats(args.parquet_file, args.plot, args.ema, args.sg)


if __name__ == "__main__":
    main()
