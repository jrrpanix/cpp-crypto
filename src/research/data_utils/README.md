# Data Utils: Binance Kline Pipeline & Analytics

A comprehensive toolkit for downloading, processing, analyzing, and backtesting with Binance perpetual futures kline data at 1-minute resolution.

## 🎯 Quick Start

```bash
# Full pipeline: download → parse → daily → aggregate → index
uv run python src/research/data_utils/pipeline.py --month 2025-01 --all-symbols

# Or individual steps
uv run python src/research/data_utils/make_daily.py       # 1m → daily bars
uv run python src/research/data_utils/make_aggregate.py   # Combine symbols
uv run python src/research/data_utils/calc_adv.py         # Calculate weights

# Track runs & rank by Sharpe
uv run python src/research/data_utils/runlog_stats.py
```

---

## 📁 File Organization

### Core Pipeline (5 files)
Essential files for the data workflow. Use these for monthly updates.

| File | Purpose | How to Use |
|------|---------|-----------|
| **config.py** | Centralized paths & settings | Imported by all scripts |
| **pipeline.py** | Orchestrates all 5 steps | `pipeline.py --month 2025-01 --all-symbols` |
| **update_klines.py** | Parse Binance ZIPs → parquet | Called by pipeline |
| **make_daily.py** | Aggregate 1m bars → daily OHLCV | Called by pipeline or standalone |
| **make_aggregate.py** | Combine daily files (all symbols) | Called by pipeline or standalone |

**Monthly Workflow:**
```bash
# Pipeline automates all these steps:
uv run python src/research/data_utils/pipeline.py --month 2025-02 --skip-download
# Equivalent to:
#  1. update_klines() - parse ZIPs
#  2. make_daily() - create daily files
#  3. make_aggregate() - combine symbols
#  4. (optional) build indexes
```

---

### Run Logging & Analytics (5 files)
Track backtest runs, rank by Sharpe ratio, analyze cross-run metrics.

| File | Purpose | When to Use |
|------|---------|-------------|
| **runlog.py** | SQLite registry for run metadata | Imported by pipeline & backtests |
| **runlog_demo.py** | Example: log a run & query results | `python runlog_demo.py` |
| **runlog_stats.py** | Query runs, rank by Sharpe | `runlog_stats.py --top 20` |
| **duckdb_analytics.py** | Optional SQL-based analytics | Advanced queries; requires duckdb |
| **duckdb_analytics_demo.py** | Example DuckDB queries | `python duckdb_analytics_demo.py` |

**Typical Usage:**
```python
# In your backtest script
from data_utils.runlog import log_run, write_metrics

run_id = log_run(
    command="backtest --symbols BTCUSDT --window 5",
    config={"window": 5, "symbols": "BTCUSDT"},
    tags="daily,hw5"
)

# ... run backtest ...

write_metrics(run_id, [
    {"metric": "sharpe", "value": 1.82},
    {"metric": "max_dd", "value": -0.12}
])
```

---

### Data Loading (1 file)
Robust utilities for loading daily data without brittle filenames.

| File | Purpose |
|------|---------|
| **daily_loader.py** | Load daily parquet files by symbol/glob; handles monthly file rotation |

**Example:**
```python
from data_utils.daily_loader import load_daily_lazy, load_daily_concat

# Lazy load (efficient for large datasets)
df = load_daily_lazy("data/klines_daily", symbol="BTCUSDT")

# Eager load (for small datasets)
df = load_daily_concat("data/klines_daily", symbol="BTCUSDT")
```

---

### Signal Detection (1 file)
5 variants of signal detection filters to prevent overfitting.

| File | Purpose |
|------|---------|
| **detection_filters.py** | Apply 5 detection variants side-by-side for A/B testing |

**Example:**
```python
from data_utils.detection_filters import apply_detection_filters

df = apply_detection_filters(
    df, 
    window=5,          # 5-day detection window
    target=0.05,       # 5% target move
    max_single=0.03,   # max single-day move
    up_days_required=2 # min consecutive up days
)

# Result columns: spread_pass, cap_pass, updays_pass, smooth_pass, hybrid_pass
print(df[["date", "ret", "spread_pass", "hybrid_pass"]])
```

---

### Utilities (2 files)
Specialized calculations for ADV, weights, and indexes.

| File | Lines | Purpose | Frequency |
|------|-------|---------|-----------|
| **calc_adv.py** | 840 | Calculate ADV, portfolio weights, generate plots | Monthly+ |
| **build_index.py** | 570 | Build market indexes from daily data | Occasionally |

**ADV Example:**
```bash
# Calculate weekly ADV for top 25 symbols
uv run python src/research/data_utils/calc_adv.py \
  --input-file data/klines_aggregate/AGG_2024-07-01_2025-09-30.pq \
  --interval 1 --units weeks --nsymbols 25 \
  --output-dir data/klines_aggregate --plot
```

---

### Validation & Debug Utilities (6 files)
Find gaps, repair missing data, visualize, and validate.

| File | Purpose | When to Use |
|------|---------|-------------|
| **check_missing.py** | Identify gaps in minute-level data | After downloading; before backtest |
| **repair_missing.py** | Merge gap-fill data into existing files | After downloading missing data |
| **debug_daily.py** | Inspect daily file structure/content | Ad-hoc troubleshooting |
| **debug_gaps.py** | Find time series gaps | Ad-hoc gap detection |
| **plot_daily.py** | Visualize daily price charts | Ad-hoc visualization |
| **viewp.py** | Quick parquet file viewer | Ad-hoc inspection |

**Gap Detection & Repair Workflow:**
```bash
# 1. Find gaps
uv run python src/research/data_utils/check_missing.py \
  --input-dir data/klines --output-dir data/check

# 2. Download gap-fill data (manual or script)
# ... download ZIPs from Binance to data/missing/ ...

# 3. Repair gaps
uv run python src/research/data_utils/repair_missing.py \
  --missing-dir data/missing --klines-dir data/klines

# 4. Regenerate downstream files
uv run python src/research/data_utils/make_daily.py --input-dir data/klines --output-dir data/klines_daily
uv run python src/research/data_utils/make_aggregate.py ...
```

---

### Documentation & Reference (2 files)

| File | Purpose |
|------|---------|
| **PIPELINE_GUIDE.py** | Quick reference for CLI commands & file patterns (`python PIPELINE_GUIDE.py` to print) |
| **CLEANUP_ANALYSIS.md** | Detailed analysis of code organization & redundancies |
| **README.md** (this file) | Full documentation |

---

## 📊 Data Flow Diagram

```
Binance Data
    ↓
[download] → data/downloads/ (ZIPs)
    ↓
[update_klines] → data/klines/ (1m parquet)
    ↓
[make_daily] → data/klines_daily/ (daily parquet)
    ↓
[make_aggregate] → data/klines_aggregate/ (combined daily)
    ↓
[calc_adv] → ADV + WEIGHTS parquet files
    ↓
[backtest] + [runlog] → run_metrics/ (parquet) + runlog.sqlite
    ↓
[duckdb_analytics / runlog_stats] → Cross-run analysis & ranking
```

---

## 🚀 Complete Workflows

### Initial Setup (First Time)

```bash
# 1. Orchestrate entire pipeline for a month
uv run python src/research/data_utils/pipeline.py \
  --month 2025-01 \
  --all-symbols

# This automatically:
#   - Downloads Binance data
#   - Parses ZIPs to minute-level parquet
#   - Aggregates to daily bars
#   - Combines all symbols into aggregate file
#   - Logs run to runlog.sqlite
```

---

### Monthly Update

```bash
# 1. Run pipeline for latest month (skips download if you prefer)
uv run python src/research/data_utils/pipeline.py \
  --month 2025-02 \
  --skip-download

# 2. Calculate fresh ADV weights
uv run python src/research/data_utils/calc_adv.py \
  --input-file data/klines_aggregate/AGG_2024-07-01_2025-02-28.pq \
  --interval 1 --units weeks --index-start-day monday \
  --nsymbols 25 --output-dir data/klines_aggregate --plot
```

---

### Running a Backtest with Run Logging

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'research'))

from data_utils.runlog import log_run, write_metrics
from data_utils.daily_loader import load_daily_concat
from data_utils.detection_filters import apply_detection_filters

# Load daily data
df = load_daily_concat("data/klines_daily", symbol="BTCUSDT")

# Apply detection filters
df = apply_detection_filters(df, window=5, target=0.05)

# Run backtest (your logic here)
# ... compute returns, Sharpe, drawdown, etc ...
sharpe = 1.85
max_dd = -0.12

# Log to runlog
run_id = log_run(
    command="backtest.py --symbol BTCUSDT --window 5",
    config={"symbol": "BTCUSDT", "window": 5},
    tags="daily,v2"
)

# Write metrics
write_metrics(run_id, [
    {"metric": "sharpe", "value": sharpe},
    {"metric": "max_dd", "value": max_dd}
])

print(f"✅ Run logged: {run_id}")
```

Then query results:
```bash
uv run python src/research/data_utils/runlog_stats.py --top 10
```

---

### Gap Detection & Repair

```bash
# 1. Check for gaps in minute-level data
uv run python src/research/data_utils/check_missing.py \
  --input-dir data/klines \
  --output-dir data/check \
  --start-date 2024-07-01 \
  --end-date 2025-02-28

# 2. Review results
cat data/check/missing_*.csv

# 3. Manually download missing ZIPs from Binance to data/missing/
# (Or use download_missing.py if compatible with your setup)

# 4. Repair gaps
uv run python src/research/data_utils/repair_missing.py \
  --missing-dir data/missing \
  --klines-dir data/klines

# 5. Regenerate daily & aggregate
uv run python src/research/data_utils/make_daily.py \
  --input-dir data/klines --output-dir data/klines_daily

uv run python src/research/data_utils/make_aggregate.py \
  --input-dir data/klines_daily \
  --output-file data/klines_aggregate/AGG_2024-07-01_2025-02-28.pq \
  --start-date 2024-07-01 --end-date 2025-02-28
```

---

## 📋 File Descriptions (Detailed)

### config.py
```python
"""Centralized configuration for all data utils scripts."""
# Defines:
#   - DATA_DIR = /workspace/data
#   - KLINES_DIR, KLINES_DAILY_DIR, AGGREGATE_DIR, etc.
#   - File naming patterns (KLINE_PATTERN, DAILY_PATTERN)
#   - DEFAULT_SYMBOLS = [BTCUSDT, ETHUSDT, ...]
#   - Feature flags (SKIP_DOWNLOAD, DRY_RUN, VERBOSE)
```

### pipeline.py
```python
"""5-step data pipeline orchestrator with logging & runlog integration."""
# Usage: python pipeline.py --month 2025-01 --symbols BTCUSDT,ETHUSDT
# Steps:
#   1. Download from Binance
#   2. Parse ZIPs → parquet
#   3. Aggregate to daily
#   4. Combine symbols
#   5. Build indexes (optional)
# All steps are logged with timestamps and run_id
```

### update_klines.py
```python
"""Parse downloaded Binance ZIP files into minute-level parquet."""
# Handles:
#   - CSV extraction from ZIPs
#   - Timestamp conversion (string ms → datetime)
#   - Schema matching & type casting
#   - Duplicate removal & sorting
#   - Append vs replace logic
```

### make_daily.py
```python
"""Aggregate minute-level parquet to daily OHLCV."""
# Processes:
#   - Groups by calendar day (UTC)
#   - Calculates: open, high, low, close, volume
# Output: One daily parquet file per symbol
# New: process_directory() wrapper for batch processing
```

### make_aggregate.py
```python
"""Combine all daily parquet files into single aggregate."""
# Inputs:
#   - data/klines_daily/{SYMBOL}_daily_*.parquet
# Output:
#   - data/klines_aggregate/AGG_YYYY-MM-DD_YYYY-MM-DD.pq
# Handles:
#   - Symbol stacking
#   - Date range filtering
#   - Optimized for cross-symbol analysis
```

### runlog.py
```python
"""SQLite-backed run registry for backtest tracking."""
# Key functions:
#   - log_run(command, config, tags) → run_id
#   - update_run(run_id, status, result_path)
#   - write_metrics(run_id, metrics_list)
#   - list_runs()
# Schema: runs table with id, created_at, command, config_json, status, etc.
```

### daily_loader.py
```python
"""Robust loading of daily parquet files without brittle filenames."""
# Key functions:
#   - load_daily_lazy(dir, symbol=None) → Lazy DataFrame
#   - load_daily_concat(dir, symbol=None) → Eager DataFrame
# Handles:
#   - Symbol filtering
#   - Latest-per-symbol selection (for monthly file rotation)
#   - Glob-based discovery (no hardcoded names)
```

### detection_filters.py
```python
"""5 signal detection variants for overfitting analysis."""
# Filters:
#   1. spread_pass: Detect multi-day trends (spread the move)
#   2. cap_pass: Cap single-day moves
#   3. updays_pass: Require consecutive up days
#   4. smooth_pass: Smooth mean > threshold
#   5. hybrid_pass: AND of all filters (most restrictive)
# Output: DataFrame with 5 boolean columns
```

### calc_adv.py
```python
"""Calculate Average Daily Volume, portfolio weights, and plots."""
# Options:
#   - Interval: 1-N weeks/months
#   - Alignment: rolling, start-of-month, index-start-day
#   - Filtering: by suffix (USDT/USDC), symbol prefix
#   - Ranking: top N symbols by ADV
# Output: ADV parquet + optional WEIGHTS + plots
```

---

## 🔄 Monthly Maintenance

**Every Month:**
1. Run pipeline for latest month
2. Recalculate ADV & weights
3. Check for gaps (optional)
4. Log any infrastructure changes

```bash
# Entire monthly update in one command
uv run python src/research/data_utils/pipeline.py --month 2025-02 --all-symbols

# Then calculate new weights
uv run python src/research/data_utils/calc_adv.py \
  --input-file data/klines_aggregate/AGG_2024-07-01_2025-02-28.pq \
  --interval 1 --units weeks --nsymbols 25 --output-dir data/klines_aggregate
```

---

## ✅ Best Practices

1. **Use pipeline.py**: Automates 5 steps with logging & error handling
2. **Regenerate after repairs**: If you fix data gaps, always regenerate daily/aggregate
3. **Version aggregates**: Include date range in filename (e.g., AGG_2024-07-01_2025-02-28.pq)
4. **Check config.py**: All paths & symbols defined there; edit once, not in every script
5. **Log your runs**: Use runlog to track backtest experiments; enables Sharpe ranking
6. **Use daily_loader**: Don't hardcode filenames; use glob-based loader

---

## 🐛 Troubleshooting

**Schema Mismatch After Update**
```
Error: Cannot cast column from Int64 to Float64
```
→ Use `update_klines.py` which handles auto-casting. If manual fix: regenerate daily/aggregate.

**Pipeline Fails: "not implemented"**
→ Ensure all imports work: `python -c "from research.data_utils.make_daily import process_directory"`

**Missing Data After Repair**
→ Did you regenerate daily & aggregate files? Required after any klines/ changes:
```bash
uv run python src/research/data_utils/make_daily.py --input-dir data/klines --output-dir data/klines_daily
```

**DuckDB Import Error**
→ Optional dependency. Install with: `pip install duckdb` or `uv add duckdb`

---

## 📚 Dependencies

- Python 3.10+
- Polars (DataFrame operations)
- Requests (HTTP downloads)
- Matplotlib (plotting, optional)
- DuckDB (analytics, optional)

Install:
```bash
uv sync
```

---

## 🎓 Learning Path

**Beginner:**
1. Read this README's "Quick Start" section
2. Run: `python pipeline.py --month 2025-01 --dry-run`
3. Run actual: `python pipeline.py --month 2025-01 --skip-download`

**Intermediate:**
1. Load daily data: `from data_utils.daily_loader import load_daily_concat`
2. Apply filters: `from data_utils.detection_filters import apply_detection_filters`
3. Log runs: `from data_utils.runlog import log_run, write_metrics`

**Advanced:**
1. Query with DuckDB: `from data_utils.duckdb_analytics import top_runs_by_sharpe`
2. Build custom indexes: `from data_utils.calc_adv import calculate_adv`
3. Parallel processing: (future enhancement)

---

## 📞 Support

For issues:
1. Check error message and traceback
2. Review troubleshooting section
3. Verify paths & date ranges are correct
4. Check that dependencies are installed: `uv sync`
5. Review detailed CLEANUP_ANALYSIS.md for file organization

---

## 📝 Notes

- **Data Source**: Binance perpetual futures (1-minute bars)
- **Update Frequency**: Monthly files available ~1 week after month-end
- **Symbol Coverage**: All perpetual contract types (500+)
- **Timezone**: UTC (all timestamps)
- **Compression**: Parquet files use zstd (faster than gzip, better than snappy)

