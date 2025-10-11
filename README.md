# 🚀 Crypto Trading & Research Platform

A high-performance C++/Python platform for real-time crypto data processing and quantitative research. This project is architected for a clean separation between a low-latency C++ core and a flexible Python research environment, all managed with Docker.

---

## Core Components

- **Real-time Engine (C++):** A C++23-based application for consuming and processing high-frequency data from Binance. It uses a lock-free, multi-threaded design to minimize latency.
- **Research & Data Utilities (Python):** A suite of Python scripts using libraries like Polars and Pandas for data acquisition, analysis, and signal generation.

---

## 🛠️ Development Workflow

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

---

## 📈 Data Workflow: Updating Monthly Klines

The primary data workflow involves downloading monthly futures kline data from Binance and converting it into an efficient Parquet format.

### Step 1: Download Monthly ZIP Files

Use the `update_klines.py` script to download new data. Run this command from inside the development container.

```sh
# Example: Download BTC-USDT 1-minute data for August & September 2025
python src/research/data_utils/update_klines.py --symbol BTCUSDT --year 2025 --months 8 9
```

- The script downloads ZIP archives into the `data/downloads/` directory.
- It automatically skips files that already exist.

### Step 2: Update Parquet Files

After downloading the raw data, run the same script **without the `--months` argument** to process all downloaded ZIPs into consolidated Parquet files.

```sh
# Example: Process all downloaded files for BTC-USDT
python src/research/data_utils/update_klines.py --symbol BTCUSDT --year 2025
```

- The script reads the ZIP files from `data/downloads/`, extracts the CSVs, and appends the data to the corresponding Parquet file in `data/klines/`.

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

