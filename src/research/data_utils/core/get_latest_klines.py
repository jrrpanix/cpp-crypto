import os

import requests


def get_all_perpetual_symbols():
    """
    Fetches all perpetual futures symbols from Binance API.
    Returns a list of symbol strings.
    """
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        symbols = [s["symbol"] for s in data["symbols"] if s.get("contractType") == "PERPETUAL"]
        return sorted(symbols)
    except Exception as e:
        print(f"⚠️ Error fetching perpetual symbols: {e}")
        return []


def download_kline(year, month, symbol, output_dir, dry_run=False):
    """
    Downloads a single monthly kline data file from Binance.
    """
    url = f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1m/{symbol}-1m-{year}-{month:02}.zip"

    if dry_run:
        print(f"[DRY RUN] Would download from: {url}")
        return

    output_filename = f"{symbol}-1m-{year}-{month:02}.zip"
    output_path = os.path.join(output_dir, output_filename)

    print(f"⏳ Downloading {url} to {output_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # Raise an exception for bad status codes
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Successfully downloaded {output_filename}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to download {url}. Error: {e}")


if __name__ == "__main__":
    import argparse
    import csv
    import sys

    parser = argparse.ArgumentParser(description="Download monthly kline data from Binance.")
    parser.add_argument("--year", type=int, help="Year to download (e.g., 2024).")
    parser.add_argument("--month", type=int, help="Month to download (e.g., 7).")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/downloads",
        help="Directory to save the downloaded zip files.",
    )
    parser.add_argument(
        "--symbols-file",
        type=str,
        default="data/symbols.csv",
        help="Path to the symbols CSV file.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, print download URLs without downloading.",
    )
    parser.add_argument(
        "--symbols-only",
        action="store_true",
        help="If set, just fetch symbols and exit.",
    )

    args = parser.parse_args()

    # Create the output directory if it doesn't exist
    os.makedirs(args.output_dir, exist_ok=True)
    print(f"✅ Output directory is '{args.output_dir}'")

    # Check if the symbols file exists, create it if it doesn't
    if not os.path.exists(args.symbols_file):
        print(f"⏳ Symbols file not found at '{args.symbols_file}'. Fetching from Binance API...")
        symbols = get_all_perpetual_symbols()
        if symbols:
            # Ensure the directory for the symbols file exists
            os.makedirs(os.path.dirname(args.symbols_file), exist_ok=True)
            with open(args.symbols_file, "w", newline="") as f:
                writer = csv.writer(f)
                for symbol in symbols:
                    writer.writerow([symbol])
            print(f"✅ Saved {len(symbols)} symbols to '{args.symbols_file}'")
        else:
            print("❌ Could not fetch symbols. Exiting.")
            sys.exit(1)

    # If --symbols-only is specified, exit after creating the file
    if args.symbols_only:
        print("✅ Symbols file created. Exiting as requested by --symbols-only.")
        sys.exit(0)

    # Read symbols from the file
    with open(args.symbols_file) as f:
        reader = csv.reader(f)
        symbols = [row[0] for row in reader]

    print(f"Found {len(symbols)} symbols to process.")

    # Main download loop
    for i, symbol in enumerate(symbols):
        print(f"--- Processing symbol {i+1}/{len(symbols)}: {symbol} ---")
        download_kline(args.year, args.month, symbol, args.output_dir, args.dry_run)

    print("\n🎉 All symbols processed.")
