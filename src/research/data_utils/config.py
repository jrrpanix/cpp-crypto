"""
Centralized configuration for data pipeline.
Single source of truth for paths, symbols, and settings.
"""

import os
from pathlib import Path

# Directories
DATA_DIR = Path("/workspace/data")
DOWNLOADS_DIR = DATA_DIR / "downloads"
KLINES_DIR = DATA_DIR / "klines"           # 1-minute bars
KLINES_DAILY_DIR = DATA_DIR / "klines_daily"  # daily bars
AGGREGATE_DIR = DATA_DIR / "aggregate"     # aggregated cross-symbol
INDEXES_DIR = DATA_DIR / "indexes"         # index data
LOGS_DIR = Path("data") / "logs"           # local logs for run tracking

# Ensure dirs exist
for d in [KLINES_DIR, KLINES_DAILY_DIR, AGGREGATE_DIR, INDEXES_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# File naming patterns (used by daily_loader and pipeline)
KLINE_PATTERN = "*_1m_*.parquet"           # 1-minute bars (e.g., BTCUSDT_1m_2024-08_2025-09.parquet)
DAILY_PATTERN = "*_daily_*.parquet"        # daily bars (e.g., BTCUSDT_daily_2024-01.parquet)
AGGREGATE_FILE = "aggregate_daily.parquet" # all symbols, all dates, concatenated

# Symbols (TODO: load from API or config file)
# For now, kept as placeholder; in practice, fetch from Binance perpetuals or a curated list
DEFAULT_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "DOGEUSDT", "MATICUSDT", "SOLUSDT", "AVAXUSDT", "LINKUSDT",
]

# Download settings
DOWNLOAD_INTERVAL = "1m"  # Only 1m supported for now
BINANCE_BASE_URL = "https://data.binance.vision/data/futures/um/monthly/klines"

# Pipeline run log database
RUNLOG_DB = "data/runlog.sqlite"
RUNLOG_METRICS = "data/run_metrics"

# Feature flags
SKIP_DOWNLOAD = False       # Set to True to skip downloads, use existing files
SKIP_INDEX_BUILD = False    # Set to True to skip index building
DRY_RUN = False             # Set to True to see what would happen without running
VERBOSE = True              # Print detailed logs

__all__ = [
    "DATA_DIR", "DOWNLOADS_DIR", "KLINES_DIR", "KLINES_DAILY_DIR", "AGGREGATE_DIR",
    "INDEXES_DIR", "LOGS_DIR", "KLINE_PATTERN", "DAILY_PATTERN", "AGGREGATE_FILE",
    "DEFAULT_SYMBOLS", "DOWNLOAD_INTERVAL", "BINANCE_BASE_URL", "RUNLOG_DB",
    "RUNLOG_METRICS", "SKIP_DOWNLOAD", "SKIP_INDEX_BUILD", "DRY_RUN", "VERBOSE"
]
