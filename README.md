# 🚀 Crypto Trading & Research Platform

High-performance C++/Python platform for real-time crypto data processing and quantitative research. Clean separation between low-latency C++ engine and flexible Python research environment, all managed with Docker.

---

## 🏗️ Architecture

- **C++ Engine (`cpp/`)**: Real-time data processing with lock-free, multi-threaded design for Binance WebSocket feeds
- **Python Research (`python/`)**: Data pipeline, signal generation, and analysis using Polars/Pandas
- **Backtest Webapp**: Web interface for testing trading strategies with performance analytics
- **Docker Dev Environment**: Consistent Ubuntu 22.04 container with all dependencies

---

## 🚀 Quick Start

### Development Container
```bash
# Build image, start container, and get shell (all-in-one)
make dev

# Inside container, compile C++ code
cd cpp/src/binance && make

# Run Python scripts
uv run python python/research/data_utils/script.py
```

### Services

```bash
# Backtest webapp (port 8084)
make backtest
# Access: http://localhost:8084

# WebSocket server (port 8082)  
make websocket
# Access: http://localhost:8082

# View logs
make logs

# Stop all services
make stop
```

See [Backtest Quick Start](docs/BACKTEST_QUICKSTART.md) for detailed usage.

---

## 📈 Monthly Data Update Workflow

**Quick update (inside dev container):**
```bash
bash /workspace/scripts/monthly_data_update.sh
```

This automated script:
1. Downloads latest monthly ZIP files from Binance
2. Processes ZIPs into minute-level parquet files
3. Aggregates to daily data
4. Calculates ADV (Average Daily Volume)
5. Generates 5 indexes with monthly rebalancing:
   - **IX10**: Top 10 by ADV (mega-cap)
   - **IX10EXBTC**: Top 10 excluding BTC (alt mega-cap)
   - **IX60**: Mid 60 (ranks 11-70)
   - **IX100**: Small 100 (ranks 71-170)
   - **IX130**: Tiny 130 (ranks 171-300)
6. Creates `AGG_WITH_INDEXES.pq` combining all data

**Manual steps:**

```bash
# 1. Download latest month (example: Feb 2026)
python python/research/data_utils/get_latest_klines.py \
  --year 2026 --month 2 \
  --symbol-file ~/github/data/symbols.csv \
  --dest-dir ~/github/data/downloads

# 2. Process ZIPs to minute parquet
python python/research/data_utils/update_klines.py \
  --kline-dir ~/github/data/klines \
  --download-dir ~/github/data/downloads

# 3. Aggregate to daily
python python/research/data_utils/make_daily_klines.py

# 4. Build indexes (monthly rebalancing only - weekly is broken)
python python/research/data_utils/build_index.py \
  --interval 1 --units months

# 5. Combine everything
python python/research/data_utils/make_aggregate_with_indexes.py
```

> **Note**: Weekly rebalancing produces incorrect results due to ISO week grouping bug causing -98% drops. Use monthly only.

---

## 📁 Project Structure

```plaintext
cpp-crypto/
├── Makefile                      # Simple commands: dev, backtest, websocket, stop, logs
├── docker/
│   ├── Dockerfile.dev            # Ubuntu dev container
│   ├── Dockerfile.backtest       # Backtest webapp image  
│   └── compose/                  # Service configurations
│       ├── backtest.yml
│       └── websocket.yml
├── cpp/                          # C++ realtime engine
│   ├── src/                      # Source code
│   │   ├── binance/              # Binance client
│   │   ├── consumer/             # Data consumer
│   │   ├── bars/                 # Bar aggregation
│   │   └── common/               # Utilities
│   ├── third_party/              # Dependencies (simdjson, ixwebsocket, etc.)
│   └── apps/                     # Compiled binaries (gitignored)
├── python/                       # Python research & webapps
│   ├── research/
│   │   ├── data_utils/           # Data pipeline scripts
│   │   │   ├── core/             # Bootstrap, update klines
│   │   │   ├── utils/            # Daily agg, index building
│   │   │   ├── experimental/     # calc_adv, analysis
│   │   │   └── debug/            # Inspection tools
│   │   ├── signal_utils/         # Strategy implementations
│   │   ├── notebooks/            # Jupyter analysis
│   │   └── ml/                   # Machine learning (local only)
│   ├── backtest/
│   │   ├── api/                  # Flask backend (backtest_api.py)
│   │   └── frontend/             # HTML/JS webapp
│   ├── pyproject.toml            # Python dependencies (uv)
│   └── .venv/                    # Virtual environment (gitignored)
├── config/                       # Configuration files
│   └── binance/
├── scripts/                      # Helper scripts
│   └── monthly_data_update.sh
├── data/                         # Data directory (external, mounted)
│   ├── downloads/                # Monthly ZIP files
│   ├── klines/                   # Minute parquet files
│   ├── klines_daily/             # Daily aggregated data
│   ├── klines_index/             # Index files (IX10, IX60, etc.)
│   └── klines_aggregate/         # Combined AGG_WITH_INDEXES.pq
└── docs/                         # Documentation

