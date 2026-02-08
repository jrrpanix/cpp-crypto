# Monthly Data Update Workflow

Complete guide for updating crypto market data every month.

## Prerequisites

- Docker container running with workspace mounted
- Python environment configured with `uv`
- Binance API access (public endpoints, no auth required)

---

## Monthly Update Steps

### Step 1: Download New Data from Binance

Download the latest monthly kline data (1-minute bars):

```bash
# Inside Docker container at /workspace
# Replace <year> with prior month's year (e.g., 2026)
# Replace <month> with prior month number (e.g., 1 for January)

uv run python src/research/data_utils/get_latest_klines.py \
  --year <year> \
  --month <month> \
  --output-dir /workspace/data/downloads
```

**Example for February 2026 update (downloading January 2026 data):**
```bash
uv run python src/research/data_utils/get_latest_klines.py \
  --year 2026 \
  --month 1 \
  --output-dir /workspace/data/downloads
```

**What it does:**
- Fetches all perpetual futures symbols from Binance API
- Downloads specified month's 1m kline ZIPs for all symbols
- Saves to `/workspace/data/downloads/`
- Creates `symbols.csv` if not present
- Automatically handles request failures

---

### Step 2: Parse Downloads → Append to Minute Klines

Parse ZIP files and append to existing parquet files:

```bash
uv run python src/research/data_utils/update_klines.py \
  --download-dir /workspace/data/downloads \
  --kline-dir /workspace/data/klines
```

**What it does:**
- Reads ZIP files from downloads directory
- Parses CSV data from Binance format
- Appends new data to existing parquet files in `/workspace/data/klines/`
- Creates new parquet files for new symbols
- Output: `{SYMBOL}_1m_{start}_{end}.parquet`

---

### Step 3: Aggregate Minute → Daily Klines

Convert 1-minute bars to daily OHLCV:

```bash
uv run python src/research/data_utils/make_daily.py \
  --input-dir /workspace/data/klines \
  --output-dir /workspace/data/klines_daily
```

**What it does:**
- Reads minute-level parquet files
- Aggregates to daily bars (OHLCV)
- Saves to `/workspace/data/klines_daily/`
- Output: `{SYMBOL}_daily_{start}_{end}.parquet`

---

### Step 4: Run Monthly Update Script

**This single script handles everything else:**

```bash
cd /workspace
chmod +x scripts/monthly_data_update.sh
./scripts/monthly_data_update.sh
```

**What it does:**
1. Creates aggregate file (`AGG_*.pq`)
2. Builds 5 market indexes with monthly rebalancing:
   - **IX10** - Top 10 including BTC
   - **IX10EXBTC** - Top 10 excluding BTC
   - **IX60** - Mid 60 (ranks 11-70)
   - **IX100** - Small 100 (ranks 71-170)
   - **IX130** - Tiny 130 (ranks 171-300)
3. Combines Binance data + indexes → `AGG_WITH_INDEXES_*.pq`
4. Generates WEIGHTS files for universe filtering (weekly for backtesting)

---

## Output Files

### `/workspace/data/klines_aggregate/`

**Main aggregate file (REQUIRED for frontend):**
- `AGG_WITH_INDEXES_2024-07-01_2026-02-28.pq` - All symbols + indexes

**WEIGHTS files (for universe filtering):**
- `WEIGHTS_10_1_WEEK_*.pq` - Top 10 with BTC
- `WEIGHTS_10_DROP1_1_WEEK_*.pq` - Top 10 excluding BTC
- `WEIGHTS_70_DROP10_1_WEEK_*.pq` - Mid 60
- `WEIGHTS_170_DROP70_1_WEEK_*.pq` - Small 100
- `WEIGHTS_300_DROP170_1_WEEK_*.pq` - Tiny 130

### `/workspace/data/klines_index/`

**Index files:**
- `IX10_daily_*.parquet`
- `IX10EXBTC_daily_*.parquet`
- `IX60_daily_*.parquet`
- `IX100_daily_*.parquet`
- `IX130_daily_*.parquet`

---

## Frontend Requirements

The frontend needs these files to work:

### **Critical (Must Have):**
1. ✅ `/workspace/data/klines/` - Minute-level data for backtests
2. ✅ `/workspace/data/klines (e.g., January 2026)
uv run python src/research/data_utils/get_latest_klines.py \
  --year 2026 \
  --month 1 \
  --output-dir /workspace/data/downloads

# Step 2: Parse ZIPs → append to minute klines
uv run python src/research/data_utils/update_klines.py \
  --download-dir /workspace/data/downloads \
  --kline-dir /workspace/data/klines

# Step 3: Minute → daily klines
uv run python src/research/data_utils/make_daily.py \
  --input-dir /workspace/data/klines \
  --output-dir /workspace/data/klines_daily

# Step 4: Run monthly update script (aggregates, indexes, weights)
cd /workspace
uv run python src/research/data_utils/bootstrap_klines.py

# Step 2: Parse ZIPs → minute klines
uv run python src/research/data_utils/update_klines.py \
  /workspace/data/klines /workspace/data/downloads

# Step 3: Minute → daily klines
uv run python src/research/data_utils/make_daily.py \
  --input-dir /workspace/data/klines \
  --output-dir /workspace/data/klines_daily

# Step 4: Run monthly update (everything else)
./scripts/monthly_data_update.sh

# Step 5: Restart backend
docker restart cpp-crypto-backend
```

---

## Troubleshooting

### "No aggregate data file found" in frontend
- Missing `AGG_WITH_INDEXES_*.pq` file
- Run: `./scripts/monthly_data_update.sh`

### Index values dropping to zero
- **Use monthly rebalancing only** (default in script)
- Weekly rebalancing has known issues

### "No symbols found" in frontend
- Missing daily kline files
- Run step 3 (make_daily.py)

### Indexes not showing in symbol list
- AGG_WITH_INDEXES not generated
- Run: `make_aggregate_with_indexes.py`

---

## Archive Old Data

After successful update, archive the previous month's files:

```bash
# Create archive directory
mkdir -p /workspace/data/archive/klines_aggregate_$(date +%Y%m)
mkdir -p /workspace/data/archive/klines_index_$(date +%Y%m)

# Move old files
mv /workspace/data/klines_aggregate/AGG_WITH_INDEXES_*_*_OLD.pq \
   /workspace/data/archive/klines_aggregate_$(date +%Y%m)/

mv /workspace/data/klines_index/*.parquet \
   /workspace/data/archive/klines_index_$(date +%Y%m)/

```bash
# 1. Download January 2026 data (~30 min)
uv run python src/research/data_utils/get_latest_klines.py \
  --year 2026 --month 1 \
  --output-dir /workspace/data/downloads

# 2. Parse and append to klines (~10 min)
uv run python src/research/data_utils/update_klines.py \
  --download-dir /workspace/data/downloads \
  --kline-dir /workspace/data/klines

# 3. Aggregate to daily (~5 min)
uv run python src/research/data_utils/make_daily.py \
  --input-dir /workspace/data/klines \
  --output-dir /workspace/data/klines_daily

# 4. Run monthly update script (~15 min)
cd /workspace
./scripts/monthly_data_update.sh

# 5. Restart backend (~1 min)
docker restart cpp-crypto-backend
```

- **Rebalancing frequency**: Indexes use **monthly** rebalancing (industry standard)
- **WEIGHTS frequency**: Generated as **weekly** for flexible backtesting
- **Index methodology**: Equal-weight within top-N, based on ADV ranking
- **Look-ahead bias**: Properly avoided - weights from period N apply to period N+1
- **Data quality**: Symbols need 90% data coverage for monthly, 80% for weekly

---

## Complete Workflow Timeline

**Monthly (e.g., February 5th after January data is available):**
1. Download January data (~30 min)
2. Parse and update klines (~10 min)
3. Aggregate to daily (~5 min)
4. Run monthly update script (~15 min)
5. Restart backend (~1 min)

**Total time: ~1 hour**

---

## File Locations Reference

| Data Type | Location | Format |
|-----------|----------|--------|
| Downloads | `/workspace/data/downloads/` | ZIP files |
| Minute klines | `/workspace/data/klines/` | Parquet |
| Daily klines | `/workspace/data/klines_daily/` | Parquet |
| Indexes | `/workspace/data/klines_index/` | Parquet |
| Aggregates | `/workspace/data/klines_aggregate/` | Parquet |
| Archives | `/workspace/data/archive/` | Parquet |
