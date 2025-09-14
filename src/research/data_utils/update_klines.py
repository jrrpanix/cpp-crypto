import argparse
import sys
import os
from datetime import datetime
import polars as pl
import zipfile
import io

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
                symbol = f.split('_')[0]
                kline_files[symbol] = f
    
    print(f"Found {len(kline_files)} unique symbols in {kline_dir}")

    # Iterate through the new downloads
    for download_file in sorted(os.listdir(download_dir)):
        if not download_file.endswith('.zip'):
            continue
        
        # Extract symbol, year, and month from download filename
        # e.g., 'BTCUSDT-1m-2025-08.zip'
        filename_no_ext = download_file[:-4] # Remove .zip
        parts = filename_no_ext.split('-')
        
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
            kline_parts = kline_filename.replace('.parquet', '').split('_')
            
            end_year_str, end_month_str = None, None

            # Format 2: ['symbol', '1m', 'start-YYYY', 'start-MM', 'end-YYYY', 'end-MM']
            if len(kline_parts) == 6:
                end_year_str = kline_parts[-2]
                end_month_str = kline_parts[-1]
            # Format 1: ['symbol', '1m', 'start-YYYY-MM', 'end-YYYY-MM']
            elif len(kline_parts) == 4:
                end_date_parts = kline_parts[-1].split('-')
                if len(end_date_parts) == 2:
                    end_year_str, end_month_str = end_date_parts

            if end_year_str and end_month_str:
                # Convert to datetime objects for comparison
                try:
                    kline_end_date = datetime(int(end_year_str), int(end_month_str), 1)
                    new_data_date = datetime(int(year), int(month), 1)

                    if new_data_date > kline_end_date:
                        print(f"Updating {download_symbol}: new data for {year}-{month} is available.")

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
                        
                        # Read new data from the zip file
                        with zipfile.ZipFile(download_file_path, 'r') as z:
                            csv_name = z.namelist()[0]
                            with z.open(csv_name) as f:
                                # polars can't read directly from the zip stream, so read into bytes
                                csv_bytes = f.read()
                                new_df = pl.read_csv(io.BytesIO(csv_bytes), has_header=True)
                                
                                # Match the schema of new_df to existing_df before concatenating
                                for col_name, col_type in existing_df.schema.items():
                                    if col_name in new_df.columns:
                                        try:
                                            new_df = new_df.with_columns(pl.col(col_name).cast(col_type))
                                        except Exception as e:
                                            print(f"    ⚠️ Could not cast column '{col_name}' to {col_type}. Error: {e}")

                        # Append the new data to the existing dataframe
                        merged_df = pl.concat([existing_df, new_df])

                        # --- SAVE NEW FILE AND DELETE OLD ONE ---
                        
                        new_kline_file_path = os.path.join(kline_dir, new_kline_filename)
                        
                        merged_df.write_parquet(new_kline_file_path)
                        os.remove(kline_file_path)
                        print(f"  ✅ Successfully updated {kline_filename} -> {new_kline_filename}")
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
    parser.add_argument(
        "--kline-dir",
        type=str,
        required=True,
        help="Directory containing the existing kline files (e.g., in Parquet format)."
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        required=True,
        help="Directory containing the latest monthly Binance downloads (zip files)."
    )

    args = parser.parse_args()

    # Assert that the directories exist
    assert os.path.isdir(args.kline_dir), f"❌ Error: Kline directory not found at '{args.kline_dir}'"
    assert os.path.isdir(args.download_dir), f"❌ Error: Download directory not found at '{args.download_dir}'"

    print("Input directories:")
    print(f"  Kline Directory:    {args.kline_dir}")
    print(f"  Download Directory: {args.download_dir}")

    update_klines(args.kline_dir, args.download_dir)

if __name__ == "__main__":
    main()
