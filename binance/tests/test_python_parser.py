import json
import time
from pathlib import Path

def benchmark_book_ticker_parsing(filename: str):
    file_path = Path(filename)

    if not file_path.exists():
        print(f"❌ File not found: {filename}")
        return

    lines = file_path.read_text().splitlines()
    total_lines = len(lines)

    print(f"📄 Loaded {total_lines} bookTicker messages")

    start_time = time.perf_counter()

    for line in lines:
        try:
            parsed = json.loads(line)
            # Access a couple of fields to simulate real usage
            _ = parsed["s"], parsed["b"], parsed["a"]
        except json.JSONDecodeError as e:
            print(f"⚠️ Skipping malformed line: {e}")

    end_time = time.perf_counter()
    total_time = end_time - start_time
    avg_time_ns = (total_time / total_lines) * 1e9 if total_lines else 0

    print(f"\n✅ Completed parsing.")
    print(f"⏱ Total time: {total_time:.6f} seconds")
    print(f"📈 Avg time per message: {avg_time_ns:.2f} ns")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python benchmark_parse_bookticker.py <input_file>")
        sys.exit(1)

    benchmark_book_ticker_parsing(sys.argv[1])

