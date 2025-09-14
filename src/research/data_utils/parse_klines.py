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

def parse_all_symbol_intervals(download_dir: str, output_dir: str = "parquet"):
    # Traverse download_dir/symbol/interval/*.zip
    import re
    os.makedirs(output_dir, exist_ok=True)
    for symbol in os.listdir(download_dir):
        symbol_path = os.path.join(download_dir, symbol)
        if not os.path.isdir(symbol_path):
            continue
        for interval in os.listdir(symbol_path):
            interval_path = os.path.join(symbol_path, interval)
            if not os.path.isdir(interval_path):
                continue
            files = [f for f in os.listdir(interval_path) if f.endswith('.zip')]
            if not files:
                continue
            # Parse year/month from filename
            pattern = re.compile(rf"{symbol}-{interval}-(\d+)-(\d{{2}})\.zip")
            fileinfos = []
            for f in files:
                m = pattern.match(f)
                if m:
                    fileinfos.append((f, int(m.group(1)), int(m.group(2))))
            if not fileinfos:
                continue
            fileinfos.sort(key=lambda x: (x[1], x[2]))
            dfs = []
            for fname, year, month in fileinfos:
                zip_path = os.path.join(interval_path, fname)
                try:
                    with zipfile.ZipFile(zip_path, 'r') as z:
                        csv_name = z.namelist()[0]
                        print(f"📄 Extracting {csv_name} from {fname}...")
                        with z.open(csv_name) as f:
                            df = pl.read_csv(f, has_header=True)
                            df = df.with_columns([
                                pl.col("open_time").cast(pl.Datetime("ms")),
                                pl.col("close_time").cast(pl.Datetime("ms")),
                            ])
                            # Cast all numeric columns except time columns to Float64
                            for col in df.columns:
                                if col not in ["open_time", "close_time"] and df[col].dtype in [pl.Int64, pl.UInt64, pl.Float32, pl.Int32, pl.UInt32]:
                                    df = df.with_columns([pl.col(col).cast(pl.Float64)])
                            dfs.append(df)
                except Exception as e:
                    print(f"⚠️ Error processing {zip_path}: {e}")
            if dfs:
                big_df = pl.concat(dfs)
                start_year, start_month = fileinfos[0][1], fileinfos[0][2]
                end_year, end_month = fileinfos[-1][1], fileinfos[-1][2]
                out_name = f"{symbol}_{interval}_{start_year:04d}-{start_month:02d}_{end_year:04d}-{end_month:02d}.parquet"
                out_path = os.path.join(output_dir, out_name)
                if os.path.exists(out_path):
                    print(f"⏩ Already parsed: {out_path}")
                else:
                    big_df.write_parquet(out_path)
                    print(f"✅ Saved {out_path} ({big_df.height} rows)")
                #breakpoint()  # Optional: pause after each symbol/interval for debugging

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
    parse_all_symbol_intervals(download_dir, parsed_dir)

