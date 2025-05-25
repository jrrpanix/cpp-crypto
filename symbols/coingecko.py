import json
import requests
from pathlib import Path

CACHE_FILE = Path("top_coins.json")

def get_top_symbols_coingecko(limit=50, refresh=False):
    if CACHE_FILE.exists() and not refresh:
        print(f"📦 Loading cached CoinGecko data from {CACHE_FILE}")
        data = json.loads(CACHE_FILE.read_text())
    else:
        print(f"🌐 Fetching top {limit} coins from CoinGecko...")
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": "false"
        }

        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        CACHE_FILE.write_text(json.dumps(data, indent=2))
        print(f"✅ Saved response to {CACHE_FILE}")

    return [coin["symbol"].lower() for coin in data]

def filter_symbol_map(symbol_file: str, output_file: str, top_symbols: list):
    with open(symbol_file, "r") as f:
        symbols = json.load(f)

    filtered = {
        sym: id_
        for sym, id_ in symbols.items()
        if any(sym.startswith(prefix) for prefix in top_symbols) and
        'usdt' in sym and not sym.startswith('usdt')
    }

    with open(output_file, "w") as f:
        json.dump(filtered, f, indent=2)

    print(f"✅ Wrote {len(filtered)} filtered symbols to {output_file}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True, help="Path to symbols.json")
    parser.add_argument("-o", "--output", required=True, help="Path to output filtered.json")
    parser.add_argument("-n", "--limit", type=int, default=50, help="Top N coins by market cap")
    parser.add_argument("--refresh", action="store_true", help="Force refresh of CoinGecko data")

    args = parser.parse_args()

    top_symbols = get_top_symbols_coingecko(args.limit, args.refresh)
    filter_symbol_map(args.input, args.output, top_symbols)

