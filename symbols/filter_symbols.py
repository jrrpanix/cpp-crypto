import json
from pathlib import Path
import argparse

def filter_symbols(input_path: Path, output_path: Path, keyword: str, capitalize: bool):
    if not input_path.exists():
        print(f"❌ Input file does not exist: {input_path}")
        return

    with input_path.open("r") as f:
        symbol_map = json.load(f)

    keyword = keyword.lower()

    # Filter and optionally capitalize
    filtered = {
        (sym.upper() if capitalize else sym): id_
        for sym, id_ in symbol_map.items()
        if keyword in sym.lower()
    }

    with output_path.open("w") as f:
        json.dump(filtered, f, indent=2)

    print(f"✅ Filtered {len(filtered)} symbols → {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Filter symbols from JSON by keyword.")
    parser.add_argument("-i", "--input-file", required=True, help="Path to input symbols.json")
    parser.add_argument("-o", "--output-file", required=True, help="Path to output filtered.json")
    parser.add_argument("-k", "--keyword", default="USDT", help="Substring to match (case-insensitive)")
    parser.add_argument("-c", "--capitalize", action="store_true", help="Capitalize output keys")

    args = parser.parse_args()

    filter_symbols(
        input_path=Path(args.input_file),
        output_path=Path(args.output_file),
        keyword=args.keyword,
        capitalize=args.capitalize
    )

