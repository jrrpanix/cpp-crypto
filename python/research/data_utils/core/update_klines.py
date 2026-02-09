import argparse
import io
import os
import zipfile
from datetime import datetime

import polars as pl

from cli_utils import add_dir_arg


def read_binance_zip(zip_path: str, existing_schema: dict = None) -> pl.DataFrame:
    """
    Read a Binance kline CSV from a zip file and optionally match schema.

    This function can be imported by other scripts that need to read Binance zip files.

    Args:
        zip_path: Path to the zip file
        existing_schema: Optional schema dict to match column types

    Returns:
        Polars DataFrame with the kline data
    """
    with zipfile.ZipFile(zip_path, "r") as z:
        csv_name = z.namelist()[0]
        with z.open(csv_name) as f:
            # polars can't read directly from the zip stream, so read into bytes
            csv_bytes = f.read()

            # Always read CSV with default inference first
            # Use infer_schema_length=0 to scan all rows for proper type inference
            # This prevents issues where early rows have integer-like floats
            df = pl.read_csv(io.BytesIO(csv_bytes), has_header=True, infer_schema_length=0)

            # Convert timestamp columns from milliseconds to datetime
            # Timestamps can be either Int64 or String in the CSV
            if "open_time" in df.columns:
                if df["open_time"].dtype == pl.Int64:
                    df = df.with_columns(
                        pl.from_epoch(pl.col("open_time"), time_unit="ms").alias("open_time")
                    )
                elif df["open_time"].dtype == pl.String or df["open_time"].dtype == pl.Utf8:
                    # Parse string as int64 first, then convert to datetime
                    df = df.with_columns(
                        pl.from_epoch(pl.col("open_time").cast(pl.Int64), time_unit="ms").alias(
                            "open_time"
                        )
                    )

            if "close_time" in df.columns:
                if df["close_time"].dtype == pl.Int64:
                    df = df.with_columns(
                        pl.from_epoch(pl.col("close_time"), time_unit="ms").alias("close_time")
                    )
                elif df["close_time"].dtype == pl.String or df["close_time"].dtype == pl.Utf8:
                    # Parse string as int64 first, then convert to datetime
                    df = df.with_columns(
                        pl.from_epoch(pl.col("close_time").cast(pl.Int64), time_unit="ms").alias(
                            "close_time"
                        )
                    )

            # If schema is provided, cast columns to match
            if existing_schema:
                for col_name, col_type in existing_schema.items():
                    if col_name in df.columns:
                        # Only cast if types don't match
                        if df[col_name].dtype != col_type:
                            try:
                                df = df.with_columns(pl.col(col_name).cast(col_type))
                            except Exception as e:
                                print(
                                    f"    ⚠️ Could not cast column '{col_name}' to {col_type}. Error: {e}"
                                )

            return df


def update_klines(kline_dir: str, download_dir: str):
    """
    Update kline files with the latest monthly downloads.
    """
    # Create a map of symbol -> filename from the kline directory
    kline_files = {}
    if os.path.exists(kline_dir):
        for f in os.listdir(kline_dir):
            # Assuming kline filename format is SYMBOL_INTERVAL_...
            if f.endswith(".parquet"):
                symbol = f.split("_")[0]
                kline_files[symbol] = f

    print(f"Found {len(kline_files)} unique symbols in {kline_dir}")

    # Iterate through the new downloads
    for download_file in sorted(os.listdir(download_dir)):
        if not download_file.endswith(".zip"):
            continue

        # Extract symbol, year, and month from download filename
        # e.g., 'BTCUSDT-1m-2025-08.zip'
        filename_no_ext = download_file[:-4]  # Remove .zip
        parts = filename_no_ext.split("-")

        if len(parts) < 4:
            print(f"⚠️ Skipping malformed file: {download_file}")
            continue

        download_symbol = parts[0]
        year = parts[-2]
        month = parts[-1]

        # Check if the symbol from the download exists in the kline files
        if download_symbol in kline_files:
            kline_filename = kline_files[download_symbol]
            # Parse end year/month from kline filename.
            # Handles two formats:
            # 1. symbol_1m_YYYY-MM_YYYY-MM.parquet
            # 2. symbol_1m_YYYY_MM_YYYY_MM.parquet
            kline_parts = kline_filename.replace(".parquet", "").split("_")

            end_year_str, end_month_str = None, None

            # Format 2: ['symbol', '1m', 'start-YYYY', 'start-MM', 'end-YYYY', 'end-MM']
            if len(kline_parts) == 6:
                end_year_str = kline_parts[-2]
                end_month_str = kline_parts[-1]
            # Format 1: ['symbol', '1m', 'start-YYYY-MM', 'end-YYYY-MM']
            elif len(kline_parts) == 4:
                end_date_parts = kline_parts[-1].split("-")
                if len(end_date_parts) == 2:
                    end_year_str, end_month_str = end_date_parts

            if end_year_str and end_month_str:
                # Convert to datetime objects for comparison
                try:
                    kline_end_date = datetime(int(end_year_str), int(end_month_str), 1)
                    new_data_date = datetime(int(year), int(month), 1)

                    if new_data_date > kline_end_date:
                        print(
                            f"Updating {download_symbol}: new data for {year}-{month} is available."
                        )

                        # --- CORRECTED FILENAME LOGIC ---
                        new_kline_filename = ""
                        # Format 2: symbol_1m_YYYY_MM_YYYY_MM.parquet -> symbol_1m_YYYY_MM_newY_newM.parquet
                        if len(kline_parts) == 6:
                            base_name = "_".join(kline_parts[:-2])
                            new_kline_filename = f"{base_name}_{year}_{month}.parquet"
                        # Format 1: symbol_1m_YYYY-MM_YYYY-MM.parquet -> symbol_1m_YYYY-MM_newY-newM.parquet
                        elif len(kline_parts) == 4:
                            base_name = "_".join(kline_parts[:-1])
                            new_kline_filename = f"{base_name}_{year}-{month}.parquet"

                        # --- END CORRECTION ---

                        # Construct full file paths
                        kline_file_path = os.path.join(kline_dir, kline_filename)
                        download_file_path = os.path.join(download_dir, download_file)

                        # Read existing kline parquet file
                        existing_df = pl.read_parquet(kline_file_path)

                        # Read new data from the zip file using shared function
                        new_df = read_binance_zip(download_file_path, existing_df.schema)

                        # Append the new data to the existing dataframe
                        merged_df = pl.concat([existing_df, new_df])

                        # --- SAVE NEW FILE AND DELETE OLD ONE ---

                        new_kline_file_path = os.path.join(kline_dir, new_kline_filename)

                        merged_df.write_parquet(new_kline_file_path)
                        os.remove(kline_file_path)
                        print(f"  ✅ Successfully updated {kline_filename} -> {new_kline_filename}")
                        # Update the map with the new filename for subsequent updates
                        kline_files[download_symbol] = new_kline_filename
                        # --- END ---

                except ValueError:
                    print(f"⚠️ Could not parse date for {download_symbol}. Skipping comparison.")
            else:
                print(f"⚠️ Could not parse kline filename: {kline_filename}")

        else:
            # This can be noisy if there are many new symbols, so we'll comment it out for now.
            # print(f"Info: {download_symbol} (from {download_file}) is new. No existing kline file to update.")
            pass


def main():
    """
    Main function to parse arguments and print them.
    """
    parser = argparse.ArgumentParser(
        description="Update kline files with the latest monthly downloads."
    )
    add_dir_arg(
        parser,
        "kline-dir",
        required=True,
        help_text="Directory containing the existing kline files (e.g., in Parquet format)",
    )
    add_dir_arg(
        parser,
        "download-dir",
        required=True,
        help_text="Directory containing the latest monthly Binance downloads (zip files)",
    )

    args = parser.parse_args()

    # Assert that the directories exist
    assert os.path.isdir(
        args.kline_dir
    ), f"❌ Error: Kline directory not found at '{args.kline_dir}'"
    assert os.path.isdir(
        args.download_dir
    ), f"❌ Error: Download directory not found at '{args.download_dir}'"

    print("Input directories:")
    print(f"  Kline Directory:    {args.kline_dir}")
    print(f"  Download Directory: {args.download_dir}")

    update_klines(args.kline_dir, args.download_dir)


if __name__ == "__main__":
    main()
