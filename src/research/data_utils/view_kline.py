import zipfile
import os
import sys


def print_zip_lines(zip_path: str, n: int = 10):
    """
    Opens a Binance .zip Kline file and prints the first `n` lines from the enclosed CSV.
    """
    if not os.path.exists(zip_path):
        print(f"❌ File not found: {zip_path}")
        return

    try:
        with zipfile.ZipFile(zip_path, "r") as z:
            csv_name = z.namelist()[0]
            with z.open(csv_name) as f:
                print(f"📄 Contents of {csv_name} in {os.path.basename(zip_path)}:")
                for i, line in enumerate(f):
                    print(line.decode().strip())
                    if i + 1 >= n:
                        break
    except Exception as e:
        print(f"⚠️ Error reading {zip_path}: {e}")


if __name__ == "__main__":
    # Default values
    default_path = "downloads/BTCUSDT/1m/BTCUSDT-1m-2025-07.zip"
    default_n = 10

    # Parse args
    zip_file = sys.argv[1] if len(sys.argv) > 1 else default_path
    try:
        n_lines = int(sys.argv[2]) if len(sys.argv) > 2 else default_n
    except ValueError:
        print("❌ Second argument must be an integer (number of lines).")
        sys.exit(1)

    print_zip_lines(zip_file, n_lines)
