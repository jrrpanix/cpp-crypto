import zipfile
import os
import sys
import polars as pl

def parse_kline_zip_to_parquet(zip_path: str, output_dir: str = "parquet"):
    if not os.path.exists(zip_path):
        print(f"❌ File not found: {zip_path}")
        return

    filename = os.path.basename(zip_path).replace(".zip", ".parquet")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    if os.path.exists(output_path):
        print(f"⏩ Already parsed: {output_path}")
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
        df.write_parquet(output_path)
        print(f"✅ Saved to {output_path}")
    except Exception as e:
        print(f"⚠️ Error processing {zip_path}: {e}")

if __name__ == "__main__":
    # Usage: python parse_kline.py <download_dir> [parsed_dir]
    if len(sys.argv) < 2:
        print("Usage: python parse_kline.py <download_dir> [parsed_dir]")
        sys.exit(1)
    download_dir = sys.argv[1]
    parsed_dir = sys.argv[2] if len(sys.argv) > 2 else "parquet"
    if not os.path.exists(download_dir):
        print(f"❌ Download directory not found: {download_dir}")
        sys.exit(1)
    zip_files = [f for f in os.listdir(download_dir) if f.endswith('.zip')]
    if not zip_files:
        print(f"❌ No zip files found in {download_dir}")
        sys.exit(1)
    for zip_name in zip_files:
        zip_path = os.path.join(download_dir, zip_name)
        parse_kline_zip_to_parquet(zip_path, parsed_dir)

