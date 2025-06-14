# 🚀 C++ Market Data Processor for Binance

This project is a **C++23-based framework** for consuming real-time market data from Binance (`bookTicker` stream). It's designed for **Linux environments via Docker**, with support for local development on macOS or cloud deployment.

---

## 📦 Features

* ✅ Binance Spot and Futures `bookTicker` stream support
* ⚡ Optional ZeroMQ integration
* 🐳 Docker-first development and deployment
* 🧱 Modular CMake + Make build system
* 📡 FastAPI webserver for receiving consumer metrics

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

| Target       | Description                           |
| ------------ | ------------------------------------- |
| `help`       | Show list of available commands       |
| `build`      | Build Docker container for full stack |
| `run`        | Run the Docker container              |
| `deps`       | Install dependencies inside container |
| `build_code` | Build the Binance C++ engine          |

---

## ⚙️ Configuration

Edit the following file to control stream selection and symbols:

```
apps/config/binance/config.json
```

Use the `key` field to select the stream configuration (`fut`, `spot`, etc.).

---

## 📚 Dependencies

### C++

| Library             | Purpose                                                   | Installation                                                                |
| ------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------- |
| **IXWebSocket**     | WebSocket client with TLS                                 | 🔧 Build from source ([GitHub](https://github.com/machinezone/IXWebSocket)) |
| **simdjson**        | Ultra-fast SIMD JSON parsing                              | 🔧 Build from source ([GitHub](https://github.com/simdjson/simdjson))       |
| **fast\_float**     | High-performance float parsing                            | 📄 Header-only ([GitHub](https://github.com/fastfloat/fast_float))          |
| **nlohmann::json**  | Friendly JSON API for C++                                 | 📄 Header-only ([GitHub](https://github.com/nlohmann/json))                 |
| **robin\_hood**     | High-performance hash map (faster than `unordered_map`)   | 📄 Header-only ([GitHub](https://github.com/martinus/robin-hood-hashing))   |
| **moodycamel**      | Lock-free concurrent queue for low-latency pipelines      | 📄 Header-only ([GitHub](https://github.com/cameron314/concurrentqueue))    |
| **ZeroMQ (libzmq)** | High-performance messaging library for inter-process comm | 📦 Installed in Docker (`apt-get install libzmq3-dev`)                      |
| **cppzmq**          | Header-only C++ bindings for ZeroMQ                       | 📄 Header-only ([GitHub](https://github.com/zeromq/cppzmq))                 |
| **CPR**             | Simple HTTP requests (C++ wrapper over libcurl)           | 🔧 Build from source ([GitHub](https://github.com/libcpr/cpr))              |
| **libcurl**         | HTTP client backend used by CPR                           | 📦 Installed in Docker (`apt-get install libcurl4-openssl-dev`)             |
| **OpenSSL**         | TLS support (`libssl`, `libcrypto`)                       | 📦 Installed in Docker                                                      |
| **zlib**            | Compression library                                       | 📦 Installed in Docker                                                      |
| **CMake**           | Cross-platform build system                               | 📦 Installed in Docker                                                      |
| **g++ 11.4.0**      | C++23-compatible compiler                                 | 📦 Installed in Docker                                                      |

### Python (FastAPI Webserver)

| Package      | Purpose                          | Installation                                |
| ------------ | -------------------------------- | ------------------------------------------- |
| **FastAPI**  | Web framework for REST endpoints | Via `uv` and `pyproject.toml`               |
| **Uvicorn**  | ASGI server for FastAPI          | `uv pip install --system uvicorn[standard]` |
| **pydantic** | Data validation and parsing      | Included with FastAPI                       |

---

## 🧩 Architecture

```text
+------------------+                    
|  binance_main    |                    
|------------------|                    
| - WebSocket      |                    
| - Parses bookTicker                  
| - Push to queue  |                    
+--------+---------+                    
         |                              
         v                              
+--------------------------+     ZMQ PUB
|  ZMQ Publisher Thread     |------------------------+
|--------------------------|                        |
| - Pull from queue        |                        v
| - Send BookTicker structs|              +-------------------+
+--------------------------+              |   Consumer(s)     |
                                          |-------------------|
                                          | - ZMQ SUB         |
                                          | - POST to FastAPI |
                                          +---------+---------+
                                                    |
                                                    v
                                          +--------------------+
                                          |     FastAPI        |
                                          |--------------------|
                                          | - Receives /status |
                                          +--------------------+
```

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
├── server/                   # FastAPI app and pyproject.toml
├── docker/                   # Dockerfiles for each service
│   ├── cpp-dev/
│   ├── full-dev/
│   ├── runtime/
│   └── webserver/
├── test_data/                # (Optional) for benchmarks or fixtures
├── Makefile
└── docker-compose.yml
```

---

## ✅ TODO

* [ ] Prometheus metrics support
* [ ] Auto-reconnect logic
* [ ] Redis or DuckDB symbol mapping option
* [ ] YAML or TOML configuration migration
* [ ] Web dashboard view of consumer status

