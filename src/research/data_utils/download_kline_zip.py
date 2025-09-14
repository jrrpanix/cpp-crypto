import requests
import os


def download_kline_zip(symbol: str, interval: str, year: int, month: int, out_dir: str):
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
