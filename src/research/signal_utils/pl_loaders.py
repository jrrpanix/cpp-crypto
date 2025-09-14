import polars as pl
import os
import sys

def load_all_parquet_files(parquet_dir: str) -> pl.DataFrame:
    """
    Loads and concatenates all Parquet files from the given directory into a single Polars DataFrame.
    """
    if not os.path.isdir(parquet_dir):
        raise ValueError(f"❌ Not a valid directory: {parquet_dir}")

    files = [
        os.path.join(parquet_dir, f)
        for f in os.listdir(parquet_dir)
        if f.endswith(".parquet")
    ]

    if not files:
        raise FileNotFoundError(f"⚠️ No .parquet files found in {parquet_dir}")

    print(f"📂 Found {len(files)} parquet files. Loading...")

    dfs = [pl.read_parquet(f) for f in sorted(files)]
    df = pl.concat(dfs, how="vertical")

    print(f"✅ Combined DataFrame shape: {df.shape}")
    return df

if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "parquet"
    df = load_all_parquet_files(directory)

    # Preview
    print(df.head())

