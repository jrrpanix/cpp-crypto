# 🚀 C++ Market Data Processor for Binance

This project is a **C++23-based framework** for consuming real-time market data from Binance (`bookTicker` stream). It's designed for **Linux environments via Docker**, with support for local development on macOS or cloud deployment.

---

## 📦 Features

* ✅ Binance Spot and Futures `bookTicker` stream support
* ⚡ Optional ZeroMQ integration
* 🐳 Docker-first development and deployment
* 🧱 Modular CMake + Make build system
* 📈 JSON parsing benchmarks with real data

---

## 🧰 Quick Start

```sh
# Build and run the container
make build
make run

# Inside the container
make deps           # Install C++ dependencies
make build_code     # Compile Binance engine
make run_fut        # Run with Futures config
# OR
make run_spot       # Run with Spot config
```

---

## 🛠️ Makefile Targets

| Target          | Description                           |
| --------------- | ------------------------------------- |
| `build`         | Build Docker container for full stack |
| `run`           | Run the Docker container              |
| `deps`          | Install dependencies inside container |
| `build_code`    | Build the Binance C++ engine          |
| `run_fut`       | Run Futures stream                    |
| `run_spot`      | Run Spot stream                       |
| `benchmark_cpp` | Run C++ JSON benchmark                |
| `benchmark_py`  | Run Python JSON benchmark             |

---

## ⚙️ Configuration

Edit:

```
apps/config/binance/config.json
```

Use the `key` field as `fut` or `spot` in run commands.

---

## 🧪 Benchmarks: JSON Parsing

**Dataset**: 128,398 Binance `bookTicker` messages
**File**: `test_data/binance_perp_btc.json`

| Parser           | Avg Time (ns/msg) | Language |
| ---------------- | ----------------- | -------- |
| `simdjson`       | 144 ns            | C++      |
| `nlohmann::json` | 1408 ns           | C++      |
| Python `json`    | 1083 ns           | Python   |

```sh
make benchmark_cpp
make benchmark_py
```

---

## 📚 Dependencies

<details>
<summary>📦 Click to view third-party libraries used</summary>

| Library             | Purpose                                                   | Installation                                                                |
| ------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------- |
| **IXWebSocket**     | WebSocket client with TLS                                 | 🔧 Build from source ([GitHub](https://github.com/machinezone/IXWebSocket)) |
| **simdjson**        | Ultra-fast SIMD JSON parsing                              | 🔧 Build from source ([GitHub](https://github.com/simdjson/simdjson))       |
| **nlohmann::json**  | Friendly JSON API for C++                                 | 📄 Header-only ([GitHub](https://github.com/nlohmann/json))                 |
| **fast\_float**     | High-performance float parsing                            | 📄 Header-only ([GitHub](https://github.com/fastfloat/fast_float))          |
| **robin\_hood**     | High-performance hash map (faster than `unordered_map`)   | 📄 Header-only ([GitHub](https://github.com/martinus/robin-hood-hashing))   |
| **moodycamel**      | Lock-free concurrent queue for low-latency pipelines      | 📄 Header-only ([GitHub](https://github.com/cameron314/concurrentqueue))    |
| **ZeroMQ (libzmq)** | High-performance messaging library for inter-process comm | 📦 Installed in Docker (`apt-get install libzmq3-dev`)                      |
| **cppzmq**          | Header-only C++ bindings for ZeroMQ                       | 📄 Header-only ([GitHub](https://github.com/zeromq/cppzmq))                 |
| **OpenSSL**         | TLS support (`libssl`, `libcrypto`)                       | 📦 Installed in Docker                                                      |
| **zlib**            | Compression library                                       | 📦 Installed in Docker                                                      |
| **CMake**           | Cross-platform build system                               | 📦 Installed in Docker                                                      |
| **g++ 11.4.0**      | C++23-compatible compiler                                 | 📦 Installed in Docker                                                      |

</details>

---

## 📁 Project Layout

```
/workspace
├── apps/config/binance/    # JSON configs
├── src/binance/            # Binance logic
├── src/common/             # Shared headers
├── scripts/                # Build/run scripts
├── test_data/              # Benchmark data
├── Makefile
└── Dockerfile
```

---

## 🔁 Notes

* C++23 features enabled (via `g++ 11.4+`)
* Designed for Dockerized development
* Focused on low-latency and clean modularity

---

## ✅ TODO

* [ ] Prometheus metrics support
* [ ] Auto-reconnect logic
* [ ] Redis or DuckDB symbol mapping option
* [ ] YAML or TOML configuration migration

