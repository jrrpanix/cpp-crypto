# 🚀 Crypto Trading & Research Platform

A high-performance C++/Python platform for real-time crypto data processing and quantitative research. This project is architected for a clean separation between a low-latency C++ core and a flexible Python research environment, all managed with Docker.

---

## Core Components

- **Real-time Engine (C++):** A C++17-based application for consuming and processing high-frequency data from Binance. It uses a lock-free, multi-threaded design to minimize latency.
- **Research & Data Utilities (Python):** A suite of Python scripts using libraries like Polars and Pandas for data acquisition, analysis, and signal generation.
- **Backtest Webapp:** A web-based interface for testing window-based trading strategies on historical data with comprehensive performance analytics.

---

## 🚀 Quick Start

### Live Data WebSocket
```bash
# Test mode with mock data
make run-websocket
# Access: http://localhost:8082

# Live Binance data
make run-live-websocket
# Access: http://localhost:8083
```

### Backtest Analysis Webapp
```bash
# Start backtest webapp
make run-backtest
# Access: http://localhost:8084
```
See [Backtest Quick Start Guide](docs/BACKTEST_QUICKSTART.md) for detailed usage.

---

## 🛠️ Development Workflow

**First Time Setup:**
```sh
# 1. Configure your data directory location
cp .env.example .env
# Edit .env to set DATA_DIR to your data location
# See docs/DATA_DIRECTORY_SETUP.md for details

# 2. Build the development image
make build-dev
```

All development is done inside a Docker container. The `Makefile` provides a simple interface for managing the environment.

1.  **Build the development image:**
    ```sh
    make build-dev
    ```

2.  **Start the container in the background:**
    ```sh
    make run-dev
    ```

3.  **Get a shell inside the running container:**
    ```sh
    make shell-dev
    ```

4.  **Compile all C++ applications (inside the container):**
    ```sh
    make build-code
    ```

5.  **Stop the development container when finished:**
    ```sh
    make stop-dev
    ```

> **Note**: If you haven't set up your data directory, see [Data Directory Setup Guide](docs/DATA_DIRECTORY_SETUP.md)

---

## 📈 Data Workflow: Bootstrapping and Updating Kline Data

This workflow details the process for building and maintaining a local dataset of **Binance Perpetual Futures** kline data in the efficient Parquet format. It does not handle spot data.

### Step 1 (Option A): Initial Data Bootstrap

If you are starting with an empty database, use the `bootstrap_klines.py` script to perform a large-scale historical data download.

1.  **Run the bootstrap script:**
    ```sh
    # This will download the last 13 months of 1-minute kline data.
    python src/research/data_utils/bootstrap_klines.py
    ```
2.  **What it does:** The script downloads monthly kline data as `.zip` files into the `data/downloads/` directory.
    - If a `symbols.csv` file exists in the root directory, it will download data for the symbols listed in that file.
    - If `symbols.csv` does **not** exist, the script will automatically create it by querying the Binance API for a list of all currently tradeable perpetual futures contracts.
    - This initial download can take a very long time and consume significant disk space.

### Step 1 (Option B): Incremental Monthly Update

If you already have a historical dataset, use `get_latest_klines.py` to download only the most recent monthly data.

1.  **Run the download script:**
    ```sh
    # Example: Download October 2025 data for all symbols in symbols.csv
    python src/research/data_utils/get_latest_klines.py \
        --symbol-file symbols.csv \
        --dest-dir data/downloads \
        --year 2025 \
        --month 10
    ```
2.  **What it does:** The script reads the specified symbol file and downloads the `.zip` archive for the given year and month into the destination directory, organized by symbol.

### Step 2: Process ZIPs and Update Parquet Files

After downloading the raw `.zip` files (either via bootstrapping or incremental update), you must process them into the final Parquet format. This script intelligently scans the download directory and updates any corresponding kline files with new monthly data.

1.  **Run the update script:**
    ```sh
    # Example: Process all downloaded ZIPs and append to their respective Parquet files
    python src/research/data_utils/update_klines.py \
        --kline-dir data/klines \
        --download-dir data/downloads
    ```
2.  **What it does:** The script scans the `download-dir` for any `.zip` files, extracts the kline data, and efficiently appends it to the corresponding consolidated Parquet file in the `kline-dir`. It automatically handles file renaming to reflect the new date range.

---

## 📁 Project Layout

The project is organized into distinct `realtime` and `research` components.

```plaintext
/
├── Makefile                  # Main entrypoint for all build/run commands
├── docker/                   # Dockerfiles and docker-compose configurations
│   ├── Dockerfile.dev
│   ├── Dockerfile.runtime
│   └── docker-compose.yml
├── src/
│   ├── realtime/             # C++ source for low-latency applications
│   │   ├── binance/
│   │   └── consumer/
│   └── research/             # Python source for data analysis and utilities
│       ├── data_utils/
│       └── signal_utils/
├── data/                     # (Git-ignored) Kline data, downloads, etc.
├── apps/                     # (Git-ignored) Compiled C++ binaries
└── pyproject.toml            # Python dependencies
```

---

## ✅ TODO

* [ ] Prometheus metrics support
* [ ] Auto-reconnect logic
* [ ] Redis or DuckDB symbol mapping option
* [ ] YAML or TOML configuration migration
* [ ] Web dashboard view of consumer status

