import zipfile
import os
import sys
import polars as pl

def parse_kline_zip_to_parquet(zip_path: str, output_path: str = None, output_dir: str = "parquet"):
    if not os.path.exists(zip_path):
        print(f"❌ File not found: {zip_path}")
        return

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            csv_name = z.namelist()[0]
            print(f"📄 Extracting {csv_name} from {os.path.basename(zip_path)}...")

            with z.open(csv_name) as f:
                df = pl.read_csv(f, has_header=True)
                df = df.with_columns([
                    pl.col("open_time").cast(pl.Datetime("ms")),
                    pl.col("close_time").cast(pl.Datetime("ms")),
                ])
    except Exception as e:
        print(f"⚠️ Error reading zip file: {e}")
        return

    # Set default output path if not provided
    if output_path is None:
        filename = os.path.basename(zip_path).replace(".zip", ".parquet")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

    try:
        df.write_parquet(output_path)
        print(f"✅ Saved to {output_path}")
    except Exception as e:
        print(f"❌ Failed to write parquet: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python parse_to_parquet.py <zip_file_path> [output_file_path]")
        sys.exit(1)

    zip_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else None
    parse_kline_zip_to_parquet(zip_path, out_path)

