import polars as pl
import glob
import re

# Load all files
files = glob.glob("sims/results/*.parquet")  # adjust path
dfs = []

for f in files:
    # parse interval-threshold-horizon from filename
    m = re.search(r"(\d+)m-(\d+\.\d+)-(\d+)m", f)
    if m:
        interval, threshold, horizon = m.groups()
    else:
        interval, threshold, horizon = None, None, None
    n = f.split('/')[-1].replace('.parquet','')
    #print(n)
    interval = int(n.split('-')[0])
    threshold = float(n.split('-')[1])
    horizon = int(n.split('-')[2])
    df = pl.read_parquet(f)
    #breakpoint()
    df = df.with_columns([
        pl.lit(int(interval)).alias("interval"),
        pl.lit(float(threshold)).alias("threshold"),
        pl.lit(int(horizon)).alias("horizon"),
    ])
    dfs.append(df)

all_data = pl.concat(dfs)

# Basic comparisons
summary = (
    all_data.group_by("symbol")
    .agg([
        pl.mean("avg_profit_after_fees").alias("mean_avg_profit"),
        pl.mean("win_loss_ratio").alias("mean_wl"),
        pl.sum("num_triggers").alias("total_triggers"),
        pl.sum("total_profit_after_fees").alias("cumulative_profit"),
    ])
    .sort("mean_avg_profit", descending=True)
)

# Sort by highest cumulative profit
summary = summary.sort("cumulative_profit", descending=True)

# Print each row formatted: symbol (15 chars), total_triggers (in thousands), mean_wl, cumulative_profit (in millions)
for row in summary.iter_rows(named=True):
    symbol = f"{row['symbol'][:15]:15}"
    total_triggers_k = row['total_triggers'] / 1000
    mean_wl = row['mean_wl']
    cumulative_profit_m = row['cumulative_profit'] / 1_000_000
    print(f"{symbol} {total_triggers_k:7.2f}k {mean_wl:.3f} {cumulative_profit_m:8.3f}M")

