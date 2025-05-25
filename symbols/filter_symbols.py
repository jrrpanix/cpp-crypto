import json
from pathlib import Path

def filter_symbols(input_path: str, output_path: str, keyword: str = "USDT"):
    input_file = Path(input_path)
    output_file = Path(output_path)

    if not input_file.exists():
        print(f"❌ Input file does not exist: {input_path}")
        return

    with input_file.open("r") as f:
        symbol_map = json.load(f)

    keyword = keyword.lower()

    # Filter keys while preserving order and original casing
    filtered = {
        sym: id_
        for sym, id_ in symbol_map.items()
        if keyword in sym.lower()
    }

    with output_file.open("w") as f:
        json.dump(filtered, f, indent=2)

    print(f"✅ Filtered {len(filtered)} symbols into {output_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python filter_symbols.py <input.json> <output.json> [FILTER]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    filter_keyword = sys.argv[3] if len(sys.argv) > 3 else "USDT"

    filter_symbols(input_file, output_file, filter_keyword)

