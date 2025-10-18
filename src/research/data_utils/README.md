# Binance Kline Data Pipeline

A comprehensive toolkit for downloading, processing, and analyzing Binance perpetual futures kline (candlestick) data at 1-minute resolution.

## Overview

This pipeline enables you to:
1. **Bootstrap** historical data from Binance
2. **Update** with latest klines 
3. **Aggregate** minute-level data to daily resolution
4. **Detect and repair** missing data gaps
5. **Calculate** Average Daily Volume (ADV) metrics
6. **Generate** weighted indexes for portfolio construction

## Directory Structure

```
data/
├── downloads/           # Raw monthly ZIP files from Binance
├── klines/             # Minute-level parquet files (per symbol)
├── klines_daily/       # Daily aggregated parquet files (per symbol)
├── klines_aggregate/   # Combined aggregate files (all symbols)
│   ├── AGG_2024-07-01_2025-09-30.pq       # Daily data, all symbols
│   ├── ADV_1_WEEK_2024-07-01_2025-09-30.pq    # Weekly ADV
│   └── WEIGHTS_25_1_WEEK_2024-07-01_2025-09-30.pq  # Top 25 with weights
├── missing/            # Downloaded gap-fill data
└── check/              # Gap detection output
```

---

## Complete Workflow

### Step 1: Bootstrap Initial Data

**First-time setup**: Download historical kline data for all perpetual futures symbols.

```bash
# Download last N months of data for all perpetual symbols
uv run python src/research/data_utils/bootstrap_klines.py \
  --last 2025-09-30 \
  --months 15 \
  --interval 1m

# Downloads to: data/downloads/{SYMBOL}/1m/{SYMBOL}-1m-YYYY-MM.zip
```

**What it does:**
- Fetches all perpetual futures symbols from Binance API
- Downloads monthly kline ZIP files (last N months)
- Skips already downloaded files
- Stores in `data/downloads/`

**Output:** Raw monthly ZIP files organized by symbol

---

### Step 2: Convert Downloads to Parquet

**Convert** monthly ZIP files to efficient parquet format (minute-level data).

```bash
# Convert all downloaded ZIPs to minute-level parquet files
uv run python src/research/data_utils/update_klines.py \
  --downloads-dir data/downloads \
  --output-dir data/klines

# Processes: data/downloads/{SYMBOL}/1m/*.zip 
# Creates:   data/klines/{SYMBOL}.pq
```

**What it does:**
- Reads CSV data from Binance ZIP files
- Handles timestamp conversion (string milliseconds → datetime)
- Merges/appends data to existing parquet files
- Removes duplicates and sorts by time
- Schema casting for consistency

**Output:** `data/klines/{SYMBOL}.pq` - one parquet file per symbol with minute-level OHLCV data

**Key Features:**
- Shared `read_binance_zip()` function for consistent parsing
- Handles both String and Int64 timestamp formats
- Automatic schema matching

---

### Step 3: Get Latest Data from Binance

**Update** your data with the most recent klines (incremental updates).

```bash
# Download latest monthly data for all symbols
uv run python src/research/data_utils/get_latest_klines.py \
  --year 2025 \
  --month 10 \
  --output-dir data/downloads

# Then update parquet files
uv run python src/research/data_utils/update_klines.py \
  --downloads-dir data/downloads \
  --output-dir data/klines
```

**What it does:**
- Downloads the current/latest month's data
- Fetches data for all perpetual symbols
- Appends to existing minute-level parquet files

**Best Practice:** Run this monthly or weekly to keep data current

---

### Step 4: Create Daily Aggregates

**Aggregate** minute-level data to daily OHLCV bars.

```bash
# Generate daily parquet files from minute data
uv run python src/research/data_utils/make_daily.py \
  --input-dir data/klines \
  --output-dir data/klines_daily

# Creates: data/klines_daily/{SYMBOL}.pq
```

**What it does:**
- Groups minute bars by calendar day
- Calculates daily OHLCV: 
  - `open`: First minute's open
  - `high`: Max of all highs
  - `low`: Min of all lows  
  - `close`: Last minute's close
  - `volume`: Sum of all volumes
  - `quote_volume`: Sum of all quote volumes

**Output:** `data/klines_daily/{SYMBOL}.pq` - one parquet file per symbol with daily OHLCV

---

### Step 5: Create Combined Aggregate File

**Combine** all symbols into a single aggregate file for analysis.

```bash
# Combine all daily files into one aggregate
uv run python src/research/data_utils/make_aggregate.py \
  --input-dir data/klines_daily \
  --output-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --start-date 2024-07-01 \
  --end-date 2025-09-30

# Creates: data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq
```

**What it does:**
- Reads all daily parquet files
- Filters to specified date range
- Combines into single file with `symbol` column
- Optimized for cross-symbol analysis

**Output:** Single parquet file with schema:
```
┌────────────┬────────┬──────┬──────┬──────┬───────┬────────┬──────────────┐
│ open_time  │ symbol │ open │ high │ low  │ close │ volume │ quote_volume │
│ datetime   │ str    │ f64  │ f64  │ f64  │ f64   │ f64    │ f64          │
└────────────┴────────┴──────┴──────┴──────┴───────┴────────┴──────────────┘
```

---

### Step 6: Check for Missing Data

**Detect** gaps in your time series data.

```bash
# Check for missing days in minute-level data
uv run python src/research/data_utils/check_missing.py \
  --input-dir data/klines \
  --output-dir data/check \
  --start-date 2024-07-01 \
  --end-date 2025-09-30

# Creates: data/check/missing_*.csv files
```

**What it does:**
- Scans all parquet files for date gaps
- Identifies missing days/months
- Generates CSV reports per symbol
- Lists exactly which data needs to be downloaded

**Output:** CSV files listing missing dates:
```
symbol,missing_dates
BTCUSDT,2024-08-15
ETHUSDT,2024-08-15,2024-08-16
```

---

### Step 7: Download Missing Data

**Fill gaps** by downloading missing monthly files.

```bash
# Download missing data based on check results
uv run python src/research/data_utils/download_missing.py \
  --check-dir data/check \
  --output-dir data/missing

# Downloads to: data/missing/{SYMBOL}/1m/*.zip
```

**What it does:**
- Reads missing data reports from check step
- Downloads required monthly ZIP files from Binance
- Organizes downloads by symbol
- Skips already downloaded files

**Output:** ZIP files in `data/missing/` ready for repair

---

### Step 8: Repair Missing Data

**Merge** downloaded gap-fill data into existing parquet files.

```bash
# Repair gaps in minute-level data
uv run python src/research/data_utils/repair_missing.py \
  --missing-dir data/missing \
  --klines-dir data/klines

# Updates: data/klines/{SYMBOL}.pq
```

**What it does:**
- Reads ZIP files from missing data directory
- Merges new data with existing parquet files
- Removes duplicates and sorts
- Validates schema consistency

**Important:** After repair, regenerate daily and aggregate files:
```bash
# Regenerate daily files
uv run python src/research/data_utils/make_daily.py \
  --input-dir data/klines \
  --output-dir data/klines_daily

# Regenerate aggregate
uv run python src/research/data_utils/make_aggregate.py \
  --input-dir data/klines_daily \
  --output-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --start-date 2024-07-01 \
  --end-date 2025-09-30
```

---

### Step 9: Calculate Average Daily Volume (ADV)

**Compute** trading volume metrics for symbol ranking and filtering.

```bash
# Calculate weekly ADV for all USDT symbols
uv run python src/research/data_utils/calc_adv.py \
  --input-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --interval 1 \
  --units weeks \
  --index-start-day monday \
  --output-dir data/klines_aggregate

# Creates: data/klines_aggregate/ADV_1_WEEK_2024-07-01_2025-09-30.pq
```

**Interval Options:**
- `--interval N`: Number of units (weeks/months)
- `--units weeks`: Weekly intervals
- `--units months`: Monthly intervals

**Alignment Options:**
- `--index-start-day monday`: Start weekly intervals on Mondays (recommended for indexes)
- `--start-of-month`: Align to calendar month start
- Default: Rolling from first data point

**Filtering Options:**
- `--suffix USDT`: Filter by quote currency (default: USDT)
- `--symbol BTC`: Filter by symbol prefix (e.g., BTC, ETH)

**Output:**
```
┌────────────┬────────────┬─────────┬─────────────┐
│ begin_date │ end_date   │ symbol  │ adv         │
│ date       │ date       │ str     │ f64         │
├────────────┼────────────┼─────────┼─────────────┤
│ 2024-07-01 │ 2024-07-07 │ BTCUSDT │ 17212737298 │
│ 2024-07-01 │ 2024-07-07 │ ETHUSDT │ 8268900000  │
└────────────┴────────────┴─────────┴─────────────┘
```

---

### Step 10: Generate Weighted Indexes

**Create** portfolio weights for top N symbols based on ADV.

```bash
# Top 25 symbols by ADV, weekly rebalancing on Mondays
uv run python src/research/data_utils/calc_adv.py \
  --input-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --interval 1 \
  --units weeks \
  --index-start-day monday \
  --nsymbols 25 \
  --output-dir data/klines_aggregate \
  --plot

# Creates: 
#   - data/klines_aggregate/WEIGHTS_25_1_WEEK_2024-07-01_2025-09-30.pq
#   - data/klines_aggregate/ADV_PLOT_1_WEEK_2024-07-01_2025-09-30.png
#   - data/klines_aggregate/WEIGHTS_PLOT_25_1_WEEK_2024-07-01_2025-09-30.png
```

**Key Options:**
- `--nsymbols 25`: Keep top 25 symbols per interval
- `--plot`: Generate visualization charts
- `--plot-symbols 10`: Number of symbols in plot (default: 10)
- `--show-all`: Display all rows (no truncation)

**What it does:**
- Ranks symbols by ADV within each interval
- Keeps top N symbols per interval
- Calculates weights: `weight_i = adv_i / sum(top N adv)`
- Weights sum to 1.0 per interval
- Filters out mid-interval new listings
- Ensures symbols have data from interval start

**Output Schema:**
```
┌────────────┬────────────┬─────────┬─────────────┬────────┐
│ begin_date │ end_date   │ symbol  │ adv         │ weight │
│ date       │ date       │ str     │ f64         │ f64    │
├────────────┼────────────┼─────────┼─────────────┼────────┤
│ 2024-07-01 │ 2024-07-07 │ BTCUSDT │ 17212737298 │ 0.5697 │
│ 2024-07-01 │ 2024-07-07 │ ETHUSDT │ 8268900000  │ 0.2737 │
│ 2024-07-01 │ 2024-07-07 │ SOLUSDT │ 2648400000  │ 0.0877 │
│ ...        │ ...        │ ...     │ ...         │ ...    │
│ (sum of weights = 1.0 per interval)               │        │
└────────────┴────────────┴─────────┴─────────────┴────────┘
```

**Use Cases:**
- **Index Construction**: Use weights for portfolio allocation
- **Rebalancing**: Update positions based on new weights each interval
- **Backtesting**: Historical weights for strategy simulation
- **Risk Management**: Diversification based on liquidity

---

## Common Workflows

### Initial Setup (First Time)

```bash
# 1. Bootstrap data (last 15 months)
uv run python src/research/data_utils/bootstrap_klines.py --last 2025-09-30 --months 15

# 2. Convert to parquet
uv run python src/research/data_utils/update_klines.py --downloads-dir data/downloads --output-dir data/klines

# 3. Create daily aggregates
uv run python src/research/data_utils/make_daily.py --input-dir data/klines --output-dir data/klines_daily

# 4. Create combined aggregate
uv run python src/research/data_utils/make_aggregate.py \
  --input-dir data/klines_daily \
  --output-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --start-date 2024-07-01 --end-date 2025-09-30

# 5. Generate weekly index weights
uv run python src/research/data_utils/calc_adv.py \
  --input-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --interval 1 --units weeks --index-start-day monday --nsymbols 25 \
  --output-dir data/klines_aggregate --plot
```

### Monthly Update

```bash
# 1. Download latest month
uv run python src/research/data_utils/get_latest_klines.py --year 2025 --month 10 --output-dir data/downloads

# 2. Update minute-level parquet
uv run python src/research/data_utils/update_klines.py --downloads-dir data/downloads --output-dir data/klines

# 3. Regenerate daily files
uv run python src/research/data_utils/make_daily.py --input-dir data/klines --output-dir data/klines_daily

# 4. Update aggregate
uv run python src/research/data_utils/make_aggregate.py \
  --input-dir data/klines_daily \
  --output-file data/klines_aggregate/AGG_2024-07-01_2025-10-31.pq \
  --start-date 2024-07-01 --end-date 2025-10-31

# 5. Recalculate weights
uv run python src/research/data_utils/calc_adv.py \
  --input-file data/klines_aggregate/AGG_2024-07-01_2025-10-31.pq \
  --interval 1 --units weeks --index-start-day monday --nsymbols 25 \
  --output-dir data/klines_aggregate
```

### Gap Detection and Repair

```bash
# 1. Check for gaps
uv run python src/research/data_utils/check_missing.py \
  --input-dir data/klines --output-dir data/check \
  --start-date 2024-07-01 --end-date 2025-09-30

# 2. Download missing data
uv run python src/research/data_utils/download_missing.py \
  --check-dir data/check --output-dir data/missing

# 3. Repair gaps
uv run python src/research/data_utils/repair_missing.py \
  --missing-dir data/missing --klines-dir data/klines

# 4. IMPORTANT: Regenerate downstream files
uv run python src/research/data_utils/make_daily.py --input-dir data/klines --output-dir data/klines_daily

uv run python src/research/data_utils/make_aggregate.py \
  --input-dir data/klines_daily \
  --output-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --start-date 2024-07-01 --end-date 2025-09-30
```

---

## File Descriptions

### Core Pipeline Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `bootstrap_klines.py` | Initial historical download | Binance API | `data/downloads/` ZIPs |
| `get_latest_klines.py` | Download latest month | Binance API | `data/downloads/` ZIPs |
| `update_klines.py` | Convert ZIPs to parquet | `data/downloads/` | `data/klines/*.pq` |
| `make_daily.py` | Aggregate to daily bars | `data/klines/` | `data/klines_daily/*.pq` |
| `make_aggregate.py` | Combine all symbols | `data/klines_daily/` | `data/klines_aggregate/*.pq` |
| `check_missing.py` | Detect data gaps | `data/klines/` | `data/check/*.csv` |
| `download_missing.py` | Download gap-fill data | `data/check/` | `data/missing/` ZIPs |
| `repair_missing.py` | Merge gap-fill data | `data/missing/` | Updates `data/klines/` |
| `calc_adv.py` | Calculate ADV & weights | `data/klines_aggregate/` | ADV/WEIGHTS parquet + plots |

### Utility Scripts

| Script | Purpose |
|--------|---------|
| `view_kline.py` | View parquet file contents |
| `viewp.py` | View parquet with Polars |
| `plot_daily.py` | Plot daily price charts |
| `debug_gaps.py` | Debug time series gaps |
| `debug_daily.py` | Validate daily aggregation |
| `test_parse.py` | Test Binance ZIP parsing |

---

## Data Schema

### Minute-Level (klines)
```python
{
    'open_time': datetime[ms],      # Bar start time
    'open': float64,                # Open price
    'high': float64,                # High price
    'low': float64,                 # Low price
    'close': float64,               # Close price
    'volume': float64,              # Base asset volume
    'close_time': datetime[ms],     # Bar end time
    'quote_volume': float64,        # Quote asset volume (USD)
    'count': int64,                 # Number of trades
    'taker_buy_volume': float64,    # Taker buy base volume
    'taker_buy_quote_volume': float64  # Taker buy quote volume
}
```

### Daily-Level (klines_daily)
```python
{
    'open_time': datetime[ms],      # Day start (00:00:00)
    'open': float64,                # First minute open
    'high': float64,                # Max of all minute highs
    'low': float64,                 # Min of all minute lows
    'close': float64,               # Last minute close
    'volume': float64,              # Sum of minute volumes
    'quote_volume': float64         # Sum of quote volumes (USD)
}
```

### Aggregate (all symbols combined)
```python
{
    'open_time': datetime[ms],      # Day start
    'symbol': str,                  # Trading pair (e.g., BTCUSDT)
    'open': float64,
    'high': float64,
    'low': float64,
    'close': float64,
    'volume': float64,
    'quote_volume': float64
}
```

### ADV Output
```python
{
    'begin_date': date,             # Interval start
    'end_date': date,               # Interval end
    'symbol': str,
    'adv': float64,                 # Average daily volume (USD)
    'weight': float64               # Portfolio weight (if --nsymbols used)
}
```

---

## Advanced Options

### Custom Index Examples

**Top 10 Monthly ADV (USDT pairs only):**
```bash
uv run python src/research/data_utils/calc_adv.py \
  --input-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --interval 1 --units months --nsymbols 10 \
  --suffix USDT --output-dir data/klines_aggregate
```

**BTC-related symbols, weekly, top 5:**
```bash
uv run python src/research/data_utils/calc_adv.py \
  --input-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --interval 1 --units weeks --index-start-day monday \
  --symbol BTC --nsymbols 5 --output-dir data/klines_aggregate
```

**Bi-weekly rebalancing, all symbols:**
```bash
uv run python src/research/data_utils/calc_adv.py \
  --input-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --interval 2 --units weeks --index-start-day monday \
  --suffix '' --output-dir data/klines_aggregate
```

**Quarterly review, top 50:**
```bash
uv run python src/research/data_utils/calc_adv.py \
  --input-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --interval 3 --units months --nsymbols 50 \
  --output-dir data/klines_aggregate --plot --plot-symbols 20
```

---

## Troubleshooting

### Common Issues

**1. Schema Mismatch Errors**
```
Error: Cannot cast column 'quote_volume' from Int64 to Float64
```
**Solution:** Use `update_klines.py` which handles automatic schema casting.

**2. Missing Data After Repair**
```
Gaps still showing after repair_missing.py
```
**Solution:** Remember to regenerate daily and aggregate files:
```bash
uv run python src/research/data_utils/make_daily.py --input-dir data/klines --output-dir data/klines_daily
uv run python src/research/data_utils/make_aggregate.py ...
```

**3. Symbols Starting Mid-Week in Weights**
```
VOXELUSDT appearing with start time 10:30:00
```
**Solution:** This is now automatically filtered. The tool only includes symbols with data from the interval start (00:00:00).

**4. Timestamp Parsing Errors**
```
TypeError: cannot create expression literal for value of type Expr
```
**Solution:** Updated code now uses Python `date` objects instead of Polars expressions.

---

## Performance Tips

1. **Incremental Updates**: Only download and process new months
2. **Parallel Processing**: Process multiple symbols simultaneously (future enhancement)
3. **Parquet Compression**: Default zstd compression balances size and speed
4. **Filter Early**: Use `--suffix` and `--symbol` to reduce data volume
5. **Plot Selectively**: Use `--plot-symbols` to limit chart complexity

---

## Dependencies

- Python 3.12+
- Polars (DataFrame library)
- Matplotlib (plotting)
- Requests (HTTP downloads)

Install with:
```bash
uv sync
```

---

## Notes

- **Data Source**: Binance perpetual futures historical data
- **Resolution**: 1-minute bars (can aggregate to any timeframe)
- **Update Frequency**: Monthly files available ~1 week after month end
- **Symbol Coverage**: All PERPETUAL contract types
- **Date Format**: UTC timezone, ISO 8601
- **File Format**: Parquet with zstd compression

---

## Support & Documentation

For issues or questions:
1. Check error messages in terminal output
2. Review troubleshooting section above
3. Verify file paths and date ranges
4. Ensure all dependencies are installed

---

## License

Part of the cpp-crypto project.
