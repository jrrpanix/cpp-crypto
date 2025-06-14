# 🚀 C++ Market Data Processor for Binance

This project is a **C++23-based framework** for consuming real-time market data from Binance (`bookTicker` stream). It's designed for **Linux environments via Docker**, with support for local development on macOS or cloud deployment.

---

## 📦 Features

* ✅ Binance Spot and Futures `bookTicker` stream support  
* ⚡ Optional ZeroMQ integration  
* 🐳 Docker-first development and deployment  
* 🧱 Modular CMake + Make build system  

---

## 🧰 Quick Start

```sh
# Build and run the container
make build
make run

# Inside the container
make deps           # Install C++ dependencies
make build_code     # Compile Binance engine
```

---

## 🛠️ Makefile Targets

| Target         | Description                           |
|----------------|---------------------------------------|
| `help`         | Show list of available commands       |
| `build`        | Build Docker container for full stack |
| `run`          | Run the Docker container              |
| `deps`         | Install dependencies inside container |
| `build_code`   | Build the Binance C++ engine          |

---

## ⚙️ Configuration

Edit the following file to control stream selection and symbols:

```
apps/config/binance/config.json
```

Use the `key` field to select the stream configuration (`fut`, `spot`, etc.).

---

## 📚 Dependencies

| Library             | Purpose                                                   | Installation                                                                |
|---------------------|-----------------------------------------------------------|-----------------------------------------------------------------------------|
| **IXWebSocket**     | WebSocket client with TLS                                 | 🔧 Build from source ([GitHub](https://github.com/machinezone/IXWebSocket)) |
| **simdjson**        | Ultra-fast SIMD JSON parsing                              | 🔧 Build from source ([GitHub](https://github.com/simdjson/simdjson))       |
| **fast_float**      | High-performance float parsing                            | 📄 Header-only ([GitHub](https://github.com/fastfloat/fast_float))          |
| **nlohmann::json**  | Friendly JSON API for C++                                 | 📄 Header-only ([GitHub](https://github.com/nlohmann/json))                 |
| **robin_hood**      | High-performance hash map (faster than `unordered_map`)   | 📄 Header-only ([GitHub](https://github.com/martinus/robin-hood-hashing))   |
| **moodycamel**      | Lock-free concurrent queue for low-latency pipelines      | 📄 Header-only ([GitHub](https://github.com/cameron314/concurrentqueue))    |
| **ZeroMQ (libzmq)** | High-performance messaging library for inter-process comm | 📦 Installed in Docker (`apt-get install libzmq3-dev`)                      |
| **cppzmq**          | Header-only C++ bindings for ZeroMQ                       | 📄 Header-only ([GitHub](https://github.com/zeromq/cppzmq))                 |
| **CPR**             | Simple HTTP requests (C++ wrapper over libcurl)           | 🔧 Build from source ([GitHub](https://github.com/libcpr/cpr))              |
| **libcurl**         | HTTP client backend used by CPR                           | 📦 Installed in Docker (`apt-get install libcurl4-openssl-dev`)             |
| **OpenSSL**         | TLS support (`libssl`, `libcrypto`)                       | 📦 Installed in Docker                                                      |
| **zlib**            | Compression library                                       | 📦 Installed in Docker                                                      |
| **CMake**           | Cross-platform build system                               | 📦 Installed in Docker                                                      |
| **g++ 11.4.0**      | C++23-compatible compiler                                 | 📦 Installed in Docker                                                      |

---

## 📁 Project Layout

```plaintext
/workspace
├── apps/
│   ├── bin/                  # Installed binaries (e.g., consumer_main)
│   └── config/binance/       # JSON configs
├── src/
│   ├── binance/              # Binance logic
│   └── common/               # Shared headers/utilities
├── scripts/                  # Build and run scripts
├── test_data/                # (Optional) for benchmarks or fixtures
├── Makefile
└── Dockerfile
```

---

## 🔁 Notes

* Written in **C++23**, compiled with `g++ 11.4+`
* Dockerized for reproducible environments
* Focused on low-latency, high-throughput streaming use cases

---

## ✅ TODO

* [ ] Prometheus metrics support  
* [ ] Auto-reconnect logic  
* [ ] Redis or DuckDB symbol mapping option  
* [ ] YAML or TOML configuration migration  

