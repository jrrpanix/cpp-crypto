import polars as pl
import sys
import plotly.graph_objects as go

import mplfinance as mpf



fname = sys.argv[1]
df = pl.read_parquet(fname)
df1 = df.clone()
print(df)
print(df.columns)

time_diff = df['close_time'][0] - df['open_time'][0]
print("Time differential (first row):", time_diff)


df = df.with_columns(
    (pl.col("close") > pl.col("close").shift(1)).alias("close_gt_prev"),
    (pl.col("high").rolling_max(window_size=3) > pl.col("close")).alias("pattern_window"),
)

print(df)
df_filtered = df.filter(
    (pl.col("close_gt_prev") == True) & (pl.col("pattern_window") == True)
)
print(df_filtered)

pdf = df1
fig = go.Figure(data=[go.Candlestick(
    x=pdf["open_time"],
    open=pdf["open"],
    high=pdf["high"],
    low=pdf["low"],
    close=pdf["close"]
)])

fig.update_layout(title="Candlestick Chart", xaxis_rangeslider_visible=False)
#fig.show()
#fig.write_image("cs.png")

zdf = pdf.to_pandas().set_index("open_time")
mpf.plot(zdf, type="line", style="charles", savefig="candlestick.png")

