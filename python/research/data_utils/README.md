# Data Utils: Binance Kline Pipeline & Analytics

A comprehensive toolkit for downloading, processing, analyzing, and backtesting with Binance perpetual futures kline data at 1-minute resolution.

## 🎯 Quick Start

```bash
# Monthly data update (recommended workflow)
# See: docs/MONTHLY_UPDATE_WORKFLOW.md
bash scripts/monthly_data_update.sh

# Or individual steps
uv run python src/research/data_utils/core/make_daily.py       # 1m → daily bars
uv run python src/research/data_utils/core/make_aggregate.py   # Combine symbols
uv run python src/research/data_utils/core/build_index.py      # Build indexes with ADV weights

# Track runs & rank by Sharpe
uv run python src/research/data_utils/utils/runlog_stats.py
```

---

## 📁 File Organization

### Core Pipeline (4 files)
Essential files for the data workflow. Use these for monthly updates.

| File | Purpose | How to Use |
|------|---------|-----------|
| **config.py** | Centralized paths & settings | Imported by all scripts |
| **core/update_klines.py** | Parse Binance ZIPs → parquet | `core/update_klines.py --input-dir data/downloads` |
| **core/make_daily.py** | Aggregate 1m bars → daily OHLCV | `core/make_daily.py --input-dir data/klines` |
| **core/make_aggregate.py** | Combine daily files (all symbols) | `core/make_aggregate.py --output-file AGG_*.pq` |

**Monthly Workflow:**
```bash
# Automated script handles all steps:
bash scripts/monthly_data_update.sh

# Or manually:
#  1. Download data from Binance (get_latest_klines.py)
#  2. Parse ZIPs (update_klines.py --mode replace)
#  3. Create daily files (make_daily.py)
#  4. Aggregate all symbols (make_aggregate.py)
#  5. Build indexes (build_index.py)

# See complete instructions: docs/MONTHLY_UPDATE_WORKFLOW.md
```

---

### CLI Infrastructure (1 file)
Shared command-line utilities to eliminate argparse duplication.

| File | Purpose | How to Use |
|------|---------|------------|
| **cli_utils.py** | Common CLI argument builders & preset parsers | Imported by pipeline scripts |

**Example Usage:**
```python
from cli_utils import add_io_args, add_dry_run_arg, create_transform_parser

# Method 1: Build parser with helper functions
parser = argparse.ArgumentParser(description="My script")
add_io_args(parser, 
    input_default="/workspace/data/klines",
    output_default="/workspace/data/klines_daily")
add_dry_run_arg(parser)
args = parser.parse_args()

# Method 2: Use preset parser
parser = create_transform_parser(
    description="Transform data",
    input_default="/workspace/data/klines"
)
args = parser.parse_args()
```

**Available Functions:**
- `add_io_args()` - input-dir, output-dir with defaults
- `add_dry_run_arg()` - --dry-run flag
- `add_symbol_filter_arg()` - --symbol filter
- `add_date_range_args()` - --start-date, --end-date
- `add_file_pattern_arg()` - --pattern with default *.parquet
- `add_dir_arg()` - Flexible directory argument
- `create_transform_parser()` - Preset for data transformation
- `create_analysis_parser()` - Preset for analysis scripts

**Refactored Scripts:**
8 scripts now use cli_utils.py to reduce CLI code by 50-70%:
- make_daily.py (34 lines → 15 lines)
- make_aggregate.py (24 lines → 12 lines)
- update_klines.py (18 lines → 10 lines)
- plot_daily.py (12 lines → 8 lines)
- check_missing.py, repair_missing.py, debug_daily.py, debug_gaps.py

---

### Run Logging & Analytics (5 files)
Track backtest runs, rank by Sharpe ratio, analyze cross-run metrics.

| File | Purpose | When to Use |
|------|---------|-------------|
| **utils/runlog.py** | SQLite registry for run metadata | Imported by pipeline & backtests |
| **experimental/runlog_demo.py** | Example: log a run & query results | `python experimental/runlog_demo.py` |
| **utils/runlog_stats.py** | Query runs, rank by Sharpe | `utils/runlog_stats.py --top 20` |
| **experimental/duckdb_analytics.py** | Optional SQL-based analytics | Advanced queries; requires duckdb |
| **experimental/duckdb_analytics_demo.py** | Example DuckDB queries | `python experimental/duckdb_analytics_demo.py` |

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
| **utils/daily_loader.py** | Load daily parquet files by symbol/glob; handles monthly file rotation |

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
| **experimental/detection_filters.py** | Apply 5 detection variants side-by-side for A/B testing |

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
| **experimental/calc_adv.py** | 840 | Calculate ADV, portfolio weights, generate plots | Ad-hoc analysis |
| **core/build_index.py** | 570 | Build market indexes with ADV weighting | Monthly (automated) |

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
Find gaps, repair missing data, visualize, and validate. All use cli_utils.py for consistent CLI.

| File | Purpose | When to Use |
|------|---------|-------------|
| **debug/check_missing.py** | Identify gaps in minute-level data | After downloading; before backtest |
| **debug/repair_missing.py** | Merge gap-fill data into existing files | After downloading missing data |
| **debug/debug_daily.py** | Inspect daily file structure/content | Ad-hoc troubleshooting |
| **debug/debug_gaps.py** | Find time series gaps | Ad-hoc gap detection |
| **debug/plot_daily.py** | Visualize daily price charts | Ad-hoc visualization |
| **debug/viewp.py** | Quick parquet file viewer | Ad-hoc inspection |

**Gap Detection & Repair Workflow:**
```bash
# 1. Find gaps
uv run python src/research/data_utils/debug/check_missing.py \
  --input-dir data/klines --output-dir data/check

# 2. Download gap-fill data (manual or script)
# ... download ZIPs from Binance to data/missing/ ...

# 3. Repair gaps
uv run python src/research/data_utils/debug/repair_missing.py \
  --missing-dir data/missing --klines-dir data/klines

# 4. Regenerate downstream files
uv run python src/research/data_utils/core/make_daily.py --input-dir data/klines --output-dir data/klines_daily
uv run python src/research/data_utils/core/make_aggregate.py ...
```

---

### Documentation & Reference (2 files)

| File | Purpose |
|------|---------|
| **README.md** (this file) | Full documentation |
| **../../docs/MONTHLY_UPDATE_WORKFLOW.md** | Complete monthly data update instructions |

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
# 1. Download latest data from Binance
uv run python src/research/data_utils/core/get_latest_klines.py \
  --output-dir /workspace/data/downloads \
  --symbols-file apps/config/binance/perp_usdt_symbols.txt

# 2. Run complete monthly update
bash scripts/monthly_data_update.sh

# This automatically:
#   - Parses ZIPs to minute-level parquet
#   - Aggregates to daily bars
#   - Combines all symbols into aggregate file
#   - Builds 5 market indexes (IX10, IX10EXBTC, IX60, IX100, IX130)
#   - Generates AGG_WITH_INDEXES file for frontend
#   - Creates WEIGHTS files for each index

# See: docs/MONTHLY_UPDATE_WORKFLOW.md for complete instructions
```

---

### Monthly Update

```bash
# Complete monthly workflow (recommended)
bash scripts/monthly_data_update.sh

# Or step-by-step:

# 1. Download latest data
uv run python src/research/data_utils/core/get_latest_klines.py \
  --output-dir /workspace/data/downloads \
  --symbols-file apps/config/binance/perp_usdt_symbols.txt

# 2. Parse new ZIPs (replaces all existing minute data)
uv run python src/research/data_utils/core/update_klines.py \
  --input-dir /workspace/data/downloads \
  --output-dir /workspace/data/klines \
  --mode replace

# 3. Regenerate daily aggregates
uv run python src/research/data_utils/core/make_daily.py \
  --input-dir /workspace/data/klines \
  --output-dir /workspace/data/klines_daily

# 4. Rebuild main aggregate file
uv run python src/research/data_utils/core/make_aggregate.py \
  --input-dir /workspace/data/klines_daily \
  --output-file /workspace/data/klines_aggregate/AGG_2024-07-01_2025-01-31.pq \
  --start-date 2024-07-01 --end-date 2025-01-31

# 5. Build all indexes (generates AGG_WITH_INDEXES and WEIGHTS files)
bash scripts/monthly_data_update.sh  # Or run build_index.py for each index

# See: docs/MONTHLY_UPDATE_WORKFLOW.md for complete instructions
```

---

### Running a Backtest with Run Logging

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'research'))

from data_utils.utils.runlog import log_run, write_metrics
from data_utils.utils.daily_loader import load_daily_concat
from data_utils.experimental.detection_filters import apply_detection_filters

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
uv run python src/research/data_utils/utils/runlog_stats.py --top 10
```

---

### Gap Detection & Repair

```bash
# 1. Check for gaps in minute-level data
uv run python src/research/data_utils/debug/check_missing.py \
  --input-dir data/klines \
  --output-dir data/check \
  --start-date 2024-07-01 \
  --end-date 2025-02-28

# 2. Review results
cat data/check/missing_*.csv

# 3. Manually download missing ZIPs from Binance to data/missing/
# (Or use debug/download_missing.py if compatible with your setup)

# 4. Repair gaps
uv run python src/research/data_utils/debug/repair_missing.py \
  --missing-dir data/missing \
  --klines-dir data/klines

# 5. Regenerate daily & aggregate
uv run python src/research/data_utils/core/make_daily.py \
  --input-dir data/klines --output-dir data/klines_daily

uv run python src/research/data_utils/core/make_aggregate.py \
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

### cli_utils.py
```python
"""Shared CLI argument builders to eliminate argparse duplication."""
# Provides:
#   - add_io_args() - standardized input/output directory args
#   - add_dry_run_arg() - consistent --dry-run flag
#   - add_symbol_filter_arg() - symbol filtering
#   - add_dir_arg() - flexible directory arguments
#   - create_transform_parser() - preset for data transformation scripts
#   - create_analysis_parser() - preset for analysis scripts
# Impact: Reduces CLI code by 50-70% across 8 scripts
```

### core/update_klines.py
```python
"""Parse downloaded Binance ZIP files into minute-level parquet."""
# Handles:
#   - CSV extraction from ZIPs
#   - Timestamp conversion (string ms → datetime)
#   - Schema matching & type casting
#   - Duplicate removal & sorting
#   - Append vs replace logic
```

### core/make_daily.py
```python
"""Aggregate minute-level parquet to daily OHLCV."""
# Processes:
#   - Groups by calendar day (UTC)
#   - Calculates: open, high, low, close, volume
# Output: One daily parquet file per symbol
# New: process_directory() wrapper for batch processing
# Uses cli_utils.py for CLI (reduced from 34 lines to 15)
```

### core/make_aggregate.py
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
# Uses cli_utils.py for CLI (reduced from 24 lines to 12)
```

### utils/runlog.py
```python
"""SQLite-backed run registry for backtest tracking."""
# Key functions:
#   - log_run(command, config, tags) → run_id
#   - update_run(run_id, status, result_path)
#   - write_metrics(run_id, metrics_list)
#   - list_runs()
# Schema: runs table with id, created_at, command, config_json, status, etc.
```

### utils/daily_loader.py
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

### experimental/detection_filters.py
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

### experimental/calc_adv.py
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
1. Download latest Binance data
2. Run monthly_data_update.sh script
3. Check for gaps (optional)
4. Frontend will automatically use new AGG_WITH_INDEXES file

```bash
# Entire monthly update in one command
bash scripts/monthly_data_update.sh

# This generates:
#   - AGG_WITH_INDEXES_{dates}.pq (for frontend)
#   - WEIGHTS files for each index
#   - All market indexes (IX10, IX10EXBTC, IX60, IX100, IX130)

# See complete instructions:
# docs/MONTHLY_UPDATE_WORKFLOW.md
```

---

## ✅ Best Practices

1. **Use monthly_data_update.sh**: Automates entire workflow with correct sequence
2. **Regenerate after repairs**: If you fix data gaps, always regenerate daily/aggregate
3. **Version aggregates**: Include date range in filename (e.g., AGG_2024-07-01_2025-02-28.pq)
4. **Check config.py**: All paths & symbols defined there; edit once, not in every script
5. **Log your runs**: Use runlog to track backtest experiments; enables Sharpe ranking
6. **Use daily_loader**: Don't hardcode filenames; use glob-based loader
7. **Use cli_utils.py**: When writing new scripts, import CLI helpers instead of duplicating argparse
8. **Monthly rebalancing only**: Weekly rebalancing has known issues; use monthly (--units months)

---

## 🐛 Troubleshooting

**Schema Mismatch After Update**
```
Error: Cannot cast column from Int64 to Float64
```
→ Use `update_klines.py` which handles auto-casting. If manual fix: regenerate daily/aggregate.

**Missing Data After Repair**
→ Did you regenerate daily & aggregate files? Required after any klines/ changes:
```bash
uv run python src/research/data_utils/core/make_daily.py --input-dir data/klines --output-dir data/klines_daily
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
2. Read: `docs/MONTHLY_UPDATE_WORKFLOW.md`
3. Run: `bash scripts/monthly_data_update.sh`

**Intermediate:**
1. Load daily data: `from data_utils.utils.daily_loader import load_daily_concat`
2. Apply filters: `from data_utils.experimental.detection_filters import apply_detection_filters`
3. Log runs: `from data_utils.utils.runlog import log_run, write_metrics`

**Advanced:**
1. Query with DuckDB: `from data_utils.experimental.duckdb_analytics import top_runs_by_sharpe`
2. Build custom indexes: `from data_utils.experimental.calc_adv import calculate_adv`
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

