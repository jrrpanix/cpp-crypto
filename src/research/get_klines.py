import requests
import os
import time
from datetime import datetime


def download_last_year(symbol="BTCUSDT", interval="1m", last="2025-07-01", N=3):
    now = datetime.strptime(last, "%Y-%m-%d")
    current_year = now.year
    current_month = now.month
    out_dir = os.path.join("downloads", symbol, interval)

    for i in range(0, N):  # <-- start at 0 to include the current month
        month_offset = current_month - i
        if month_offset > 0:
            year = current_year
            month = month_offset
        else:
            year = current_year - 1
            month = 12 + month_offset
        # Try to download, break if 404
        base_url = "https://data.binance.vision/data/futures/um/monthly/klines"
        filename = f"{symbol}-{interval}-{year}-{month:02d}.zip"
        url = f"{base_url}/{symbol}/{interval}/{filename}"
        local_path = os.path.join(out_dir, filename)
        os.makedirs(out_dir, exist_ok=True)
        if os.path.exists(local_path):
            print(f"✅ Already downloaded: {filename}")
            continue
        print(f"⬇️ Downloading {filename}...")
        try:
            resp = requests.get(url, timeout=20)
            if resp.status_code == 200:
                with open(local_path, "wb") as f:
                    f.write(resp.content)
                print(f"✅ Saved to {local_path}")
            elif resp.status_code == 404:
                print(f"❌ {filename}: HTTP 404 (no more history, stopping)")
                break
            else:
                print(f"❌ {filename}: HTTP {resp.status_code}")
        except Exception as e:
            print(f"⚠️ {filename}: {e}")


def download_all_last_year(symbols, interval="1m", last="2025-07-01", N=3, delay=1.5):
    """
    Download klines for all symbols, rate limiting requests to avoid Binance cutoff.
    """
    for symbol in symbols:
        print(f"\n=== Downloading for {symbol} ===")
        download_last_year(symbol, interval, last, N)
        time.sleep(delay)  # Rate limit between requests


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
        symbols = [
            s["symbol"] for s in data["symbols"] if s.get("contractType") == "PERPETUAL"
        ]
        return sorted(symbols)
    except Exception as e:
        print(f"⚠️ Error fetching perpetual symbols: {e}")
        return []


if __name__ == "__main__":
    if os.path.exists("symbols.csv"):
        with open("symbols.csv", "r") as f:
            symbols = [line.strip() for line in f if line.strip()]
    else:
        symbols = get_all_perpetual_symbols()
        with open("symbols.csv", "w") as f:
            for symbol in symbols:
                f.write(f"{symbol}\n")
    print(symbols)
    # symbols = symbols[:4]  # Limit to first 10 for testing
    # breakpoint()
    # Download klines for all perpetual symbols with rate limiting
    download_all_last_year(symbols, interval="1m", last="2025-07-01", N=13, delay=1.5)
