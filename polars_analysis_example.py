import polars as pl
import argparse
import os

def demonstrate_patterns(file_path: str):
    """
    Demonstrates how to perform common financial calculations in Polars
    without iterating over rows.
    """
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found at '{file_path}'")
        return

    try:
        # Read the data and limit to a reasonable size for the example
        df = pl.read_parquet(file_path)

        print(f"Original DataFrame shape: {df.shape}")
        print("Demonstrating calculations...")

        # --- Core Concept: Expressions ---
        # Most operations are done inside a .with_columns() call.
        # Each argument is an "expression" that creates a new column.

        df_with_patterns = df.with_columns(
            # 1. Simple Moving Average (SMA)
            # .rolling() creates a window over which to compute.
            pl.col("close").rolling_mean(window_size=10).alias("sma_10"),

            # 2. Exponential Moving Average (EMA / EWMA)
            # Polars has a built-in function for this.
            pl.col("close").ewm_mean(span=10).alias("ema_10"),

            # 3. Calculations depending on prior rows using .shift()
            # This calculates the daily change in price.
            (pl.col("close") - pl.col("close").shift(1)).alias("daily_change"),

            # 4. More complex custom rolling calculation
            # Example: Find the max "high" in a 5-day rolling window
            pl.col("high").rolling_max(window_size=5).alias("rolling_5d_high"),

            # 5. Conditional logic with pl.when().then().otherwise()
            # Flag rows where the close is above the 10-day SMA
            pl.when(pl.col("close") > pl.col("close").rolling_mean(window_size=10))
            .then(True)
            .otherwise(False)
            .alias("is_above_sma_10")
        )

        # --- Displaying Results ---
        # We'll show the last 15 rows so you can see the rolling calculations.
        print("\n--- DataFrame with new calculated columns (last 15 rows) ---")

        # Select a subset of columns to make the output readable
        display_cols = [
            "open_time",
            "close",
            "sma_10",
            "ema_10",
            "daily_change",
            "rolling_5d_high",
            "is_above_sma_10",
        ]
        print(df_with_patterns.select(display_cols).tail(15))

    except Exception as e:
        print(f"❌ An error occurred: {e}")

def main():
    """
    Main function to parse arguments.
    """
    parser = argparse.ArgumentParser(
        description="Demonstrate advanced pattern calculations in Polars."
    )
    parser.add_argument(
        "parquet_file",
        type=str,
        help="Path to the Parquet kline file."
    )
    args = parser.parse_args()

    demonstrate_patterns(args.parquet_file)

if __name__ == "__main__":
    main()
