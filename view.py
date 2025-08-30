import polars as pl
import sys

data = pl.read_parquet(sys.argv[1])
print(data)
print(data.columns)

