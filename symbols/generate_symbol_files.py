from pathlib import Path
import json
import requests

EXCHANGE_INFO_FILE = Path("binance.json")
GPERF_FILE = Path("symbol_keywords.gperf")
SYMBOLS_JSON_FILE = Path("symbols.json")

def load_exchange_info():
    if EXCHANGE_INFO_FILE.exists():
        print(f"📄 Loading cached exchange info from {EXCHANGE_INFO_FILE}")
        return json.loads(EXCHANGE_INFO_FILE.read_text())
    else:
        print("🌐 Fetching exchange info from Binance API...")
        url = "https://api.binance.com/api/v3/exchangeInfo"
        response = requests.get(url)
        if response.status_code != 200:
            raise RuntimeError(f"Failed to fetch exchange info: {response.status_code}")
        data = response.json()
        EXCHANGE_INFO_FILE.write_text(json.dumps(data, indent=2))
        return data

def extract_symbols(exchange_info):
    return sorted([
        s["symbol"].lower() for s in exchange_info["symbols"]
        if s["status"] == "TRADING"
    ])

def write_gperf_file(symbols):
    print(f"📝 Writing {len(symbols)} symbols to {GPERF_FILE}")
    lines = [
        "%language=C++",
        "%readonly-tables",
        "%struct-type",
        "%define hash-function-name symbol_hash",
        "%define lookup-function-name lookup_symbol",
        "",
        "struct SymbolEntry {",
        "    const char* name;",
        "    int32_t id;",
        "};",
        "",
        "%%"
    ]
    lines += [f"{symbol}, {i}" for i, symbol in enumerate(symbols)]
    lines.append("%%")

    GPERF_FILE.write_text("\n".join(lines))

def write_symbols_json(symbols):
    symbol_map = {symbol: i for i, symbol in enumerate(symbols)}
    SYMBOLS_JSON_FILE.write_text(json.dumps(symbol_map, indent=2))
    print(f"📦 Wrote {len(symbol_map)} entries to {SYMBOLS_JSON_FILE}")

if __name__ == "__main__":
    data = load_exchange_info()
    symbols = extract_symbols(data)
    write_gperf_file(symbols)
    write_symbols_json(symbols)

