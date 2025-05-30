# 🚀 C++ Market Data Processor for Crypto Exchanges

This project provides a **C++23-based framework** for connecting to crypto exchanges. It is designed to run in a **Linux environment via Docker** but is fully developed and tested on a **MacBook** using Docker containers.

The system currently supports the **Binance Spot** and **Binance Perpetual Futures (futures)** `bookTicker` WebSocket channels, which deliver real-time bid/ask updates.

---

## 💡 Why Docker?

Most developers use laptops (e.g., macOS), which aren’t native Linux systems. Docker provides a lightweight, reproducible Linux environment for:

- Running C++17/20/23 toolchains
- Installing build dependencies like OpenSSL, IXWebSocket, etc.
- Mounting your Mac filesystem for seamless development

---
## 🧰 Tech Stack


| Library               | Purpose                                                   | Installation                                                                 |
|-----------------------|-----------------------------------------------------------|------------------------------------------------------------------------------|
| **IXWebSocket**       | WebSocket client with TLS                                 | 🔧 Build from source ([GitHub](https://github.com/machinezone/IXWebSocket)) |
| **simdjson**          | Ultra-fast SIMD JSON parsing                              | 🔧 Build from source ([GitHub](https://github.com/simdjson/simdjson))       |
| **nlohmann::json**    | Friendly JSON API for C++                                 | 📄 Header-only ([GitHub](https://github.com/nlohmann/json))                 |
| **fast_float**        | High-performance float parsing                            | 📄 Header-only ([GitHub](https://github.com/fastfloat/fast_float))          |
| **robin_hood**        | High-performance hash map (faster than `unordered_map`)   | 📄 Header-only ([GitHub](https://github.com/martinus/robin-hood-hashing))  |
| **moodycamel**        | Lock-free concurrent queue for low-latency pipelines      | 📄 Header-only ([GitHub](https://github.com/cameron314/concurrentqueue))    |
| **ZeroMQ (libzmq)**   | High-performance messaging library for inter-process comm | 📦 Installed in Docker (`apt-get install libzmq3-dev`)                      |
| **cppzmq**            | Header-only C++ bindings for ZeroMQ                       | 📄 Header-only ([GitHub](https://github.com/zeromq/cppzmq))                 |
| **OpenSSL**           | TLS support (`libssl`, `libcrypto`)                       | 📦 Installed in Docker                                                       |
| **zlib**              | Compression library                                       | 📦 Installed in Docker                                                       |
| **CMake**             | Cross-platform build system                               | 📦 Installed in Docker                                                       |
| **g++ 11.4.0**        | C++23-compatible compiler                                 | 📦 Installed in Docker                                                       |

---
# Development Environment Makefile

This repository provides a Makefile to streamline the setup, build, and execution of development environments using Docker. It supports both a C++-only and a combined C++ + Python setup.

## Usage

**For fast start: `make setup`**

To use any of the predefined targets, run:

`make <target>`

## Available Targets

| Target       | Description                                      |
|--------------|--------------------------------------------------|
| `build_cpp`  | Build the C++-only Docker image                  |
| `build_full` | Build the full (C++ + Python) Docker image       |
| `run_cpp`    | Launch the C++ dev Docker container              |
| `run_full`   | Launch the full (C++ + Python) dev container     |
| `setup`      | Run full setup (build + launch + install deps)   |
| `deps`       | Install dependencies inside the container        |
| `help`       | Display this help message                        |

---
# 📊 JSON Parsing Benchmark: Binance `bookTicker` Messages

This benchmark compares the performance of several JSON parsers using real-time market data from Binance's perpetual futures `bookTicker` stream.

---

## 🧪 Dataset

- **File**: `test_data/binance_perp_btc.json`
- **Format**: One JSON object per line
- **Source**: [Binance Exchange WebSocket](https://binance-docs.github.io/apidocs/futures/en/#individual-symbol-book-ticker-streams)
- **Total messages**: 128,398

---

## 📈 Benchmark Results

| Parser              | Total Time (ms) | Avg Time per Message (ns) | Language |
|---------------------|------------------|----------------------------|----------|
| `simdjson`          | 18.50 ms         | 144 ns                     | C++      |
| `nlohmann::json`    | 180.90 ms        | 1408 ns                    | C++      |
| Python `json`       | 139.11 ms        | 1083 ns                    | Python   |

---

## ✅ Summary

s- `simdjson` is the fastest, offering ~10× better performance than `nlohmann::json`.
- Python’s built-in `json` parser is surprisingly efficient and competitive.
- `nlohmann::json` is a strong middle-ground for developer ergonomics in C++.

---

## 🔁 Reproducing the Benchmark

### 🔧 C++ Timing

```sh
./binance/build/test_json_times ./test_data/binance_perp_btc.json
```

- Benchmarks both `simdjson` and `nlohmann::json`
- Reports total and average time per message

---

### 🐍 Python Timing

```sh
python ./binance/tests/test_python_parser.py ./test_data/binance_perp_btc.json
```

- Uses Python's built-in `json` module
- Measures total parsing time only (no I/O)

---

## 📝 Notes

- All benchmarks use the same input file
- Each line must be a valid JSON object (cleaned if needed)
- No printing or validation performed during timed runs

---

Use this to evaluate trade-offs between performance and ease of use when choosing a JSON library for real-time parsing workloads.


---


## 📝 Notes

- Written in **C++23**, compiled with `g++ 11.4.0`
- Partial C++23 support — project will upgrade to `g++ 13+`
- Optimized for macOS-based development via Dockerized Linux
- Uses `robin_hood::unordered_flat_map` and `gperf` for efficient symbol lookups


