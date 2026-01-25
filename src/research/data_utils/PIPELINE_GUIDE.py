"""
Quick reference guide for the data pipeline.
Use this to understand the flow and when to use each tool.
"""

# ==============================================================================
# MONTHLY DATA UPDATE WORKFLOW
# ==============================================================================

# 1. DOWNLOAD (first time or to add new month)
#    uv run python src/research/data_utils/bootstrap_klines.py
#    → Downloads SYMBOL-1m-YYYY-MM.zip from Binance to data/downloads/
#    → Takes ~5-10 min depending on # of symbols
#
#    File created: data/downloads/BTCUSDT-1m-2025-01.zip (for each symbol)

# 2. PARSE & APPEND MINUTE BARS (CRITICAL)
#    uv run python src/research/data_utils/update_klines.py \
#      --download-dir data/downloads \
#      --kline-dir data/klines
#    → Reads each .zip file
#    → Appends 1m bars to existing SYMBOL_1m_*.parquet (or creates if new)
#    → Example: BTCUSDT_1m_2024-08_2025-01.parquet (date range in name)
#
#    File updated: data/klines/BTCUSDT_1m_2024-08_2025-01.parquet

# 3. AGGREGATE TO DAILY BARS (fast, no dependencies)
#    uv run python src/research/data_utils/make_daily.py \
#      --input-dir data/klines \
#      --output-dir data/klines_daily
#    → For each 1m file, groups by date and creates OHLCV
#    → Outputs: SYMBOL_daily_2025-01.parquet (per month)
#
#    Files created: data/klines_daily/BTCUSDT_daily_2025-01.parquet

# 4. COMBINE INTO AGGREGATE (optional, for charting/analysis)
#    uv run python src/research/data_utils/make_aggregate.py \
#      --input-dir data/klines_daily \
#      --output-dir data/aggregate
#    → Reads all SYMBOL_daily_*.parquet files
#    → Vertically stacks into one file: aggregate_daily.parquet
#
#    File created: data/aggregate/aggregate_daily.parquet

# 5. BUILD INDEXES (optional, for portfolio-level signals)
#    uv run python src/research/data_utils/build_index.py
#    → Creates synthetic index symbols (e.g., equal-weight portfolio)
#    → Outputs: TOP_10_IX_daily_*.parquet, etc.

# ==============================================================================
# NEW ORCHESTRATED PIPELINE (all steps at once)
# ==============================================================================

#    uv run python src/research/data_utils/pipeline.py \
#      --month 2025-01 \
#      --symbols BTCUSDT,ETHUSDT
#    
#    Logs:
#    - Each step success/failure
#    - Total duration
#    - Tracks run in data/runlog.sqlite (for ranking later)
#
#    Skip steps:
#    --skip-download   (use existing downloads)
#    --skip-index      (skip index building)
#    --dry-run         (see what would run)

# ==============================================================================
# KEY FILE NAMING PATTERNS (from config.py)
# ==============================================================================

# 1m bars:      SYMBOL_1m_YYYY-MM_YYYY-MM.parquet
#               (date range in filename because each month appends)
#
# Daily bars:   SYMBOL_daily_YYYY-MM.parquet
#               (one file per symbol per month, easy to glob)
#
# Aggregate:    aggregate_daily.parquet
#               (all symbols, all dates, stacked)
#
# Indexes:      INDEX_SYMBOL_daily_YYYY-MM.parquet
#               (e.g., TOP_10_IX_daily_2025-01.parquet)

# ==============================================================================
# ROBUST LOADING (use these, not hardcoded filenames)
# ==============================================================================

# Load daily bars for a symbol:
#   from research.data_utils.daily_loader import load_daily_concat
#   df = load_daily_concat("data/klines_daily", symbol="BTCUSDT")
#   
#   No need to know exact filename—loads all matching _daily_*.parquet files

# Load all daily bars:
#   df = load_daily_concat("data/klines_daily")

# Load lazily (for big data):
#   lf = load_daily_lazy("data/klines_daily")
#   result = lf.filter(pl.col("close") > 100).collect()

# ==============================================================================
# COMMON ISSUES & FIXES
# ==============================================================================

# Q: "File not found: BTCUSDT_1m_2024-08_2025-08.parquet"
# A: Filename changes each month. Use daily_loader.py or config.KLINE_PATTERN glob.

# Q: "How do I know which scripts to run?"
# A: Use pipeline.py. It runs all steps in order, or use --skip-* to skip steps.

# Q: "I only have partial data for a month"
# A: Use check_missing.py to find gaps, then download_missing.py to fill them.

# Q: "Can I re-run a step?"
# A: Yes, each step is idempotent (safe to re-run). make_daily.py will overwrite
#    daily files; update_klines.py will append or replace based on logic.

# ==============================================================================
# ANALYTICS & RANKING RUNS
# ==============================================================================

# After running pipeline with backtests:
#   uv run python src/research/data_utils/duckdb_analytics_demo.py
#   → Shows top runs by Sharpe, metric counts, cross-universe stats

# Using runlog:
#   uv run python src/research/data_utils/runlog_stats.py \
#     --db data/runlog.sqlite \
#     --metrics-glob "data/run_metrics/*.parquet" \
#     --top 20
#   → Ranks runs by Sharpe, lists config + results

print(__doc__)
