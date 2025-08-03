import requests
import os
from datetime import datetime, timedelta

def download_kline_zip(symbol: str, interval: str, year: int, month: int, out_dir: str):
    """
    Downloads a Binance Kline ZIP file for a given symbol/year/month if not already present.
    """
    base_url = "https://data.binance.vision/data/futures/um/monthly/klines"
    filename = f"{symbol}-{interval}-{year}-{month:02d}.zip"
    url = f"{base_url}/{symbol}/{interval}/{filename}"
    local_path = os.path.join(out_dir, filename)

    os.makedirs(out_dir, exist_ok=True)
    if os.path.exists(local_path):
        print(f"✅ Already downloaded: {filename}")
        return

    print(f"⬇️ Downloading {filename}...")
    try:
        resp = requests.get(url, timeout=20)
        if resp.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(resp.content)
            print(f"✅ Saved to {local_path}")
        else:
            print(f"❌ {filename}: HTTP {resp.status_code}")
    except Exception as e:
        print(f"⚠️ {filename}: {e}")

def download_last_year(symbol="BTCUSDT", interval="1m", last="2025-07-01"):
    """
    Downloads the last 12 full months of Kline ZIP files, ending with the month in `last`.
    """
    try:
        end_date = datetime.strptime(last, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Parameter 'last' must be in 'YYYY-MM-DD' format.")

    out_dir = os.path.join("downloads", symbol, interval)

    for i in range(12):
        target = end_date - timedelta(days=30 * i)
        year = target.year
        month = target.month
        download_kline_zip(symbol, interval, year, month, out_dir)

if __name__ == "__main__":
    download_last_year(symbol="BTCUSDT", interval="1m", last="2025-07-01")

