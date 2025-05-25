# 🚀 C++ Market Data Processor for Crypto Exchanges

This project provides a **C++23-based framework** for connecting to crypto exchanges. It is designed to run in a **Linux environment via Docker** but is fully developed and tested on a **MacBook** using Docker containers.

The system currently supports the **Binance Spot** and **Binance Perpetual Futures (futures)** `bookTicker` WebSocket channels, which deliver real-time bid/ask updates.

---

## 💡 Why Docker?

Most developers use laptops (e.g., macOS), which aren’t native Linux systems. Docker provides a lightweight, reproducible Linux environment for:

- Running C++17/20/23 toolchains
- Installing build dependencies like OpenSSL, IXWebSocket, etc.
- Mounting your Mac filesystem for seamless development

No need for cloud VMs or full Linux installs — just Docker.

---

## 🧰 Tech Stack

| Library               | Purpose                                                   | Installation                                                                 |
|-----------------------|-----------------------------------------------------------|------------------------------------------------------------------------------|
| **IXWebSocket**       | WebSocket client with TLS                                 | 🔧 Build from source ([GitHub](https://github.com/machinezone/IXWebSocket)) |
| **simdjson**          | Ultra-fast SIMD JSON parsing                              | 🔧 Build from source ([GitHub](https://github.com/simdjson/simdjson))       |
| **nlohmann::json**    | Friendly JSON API for C++                                 | 📄 Header-only ([GitHub](https://github.com/nlohmann/json))                 |
| **fast_float**        | High-performance float parsing                            | 📄 Header-only ([GitHub](https://github.com/fastfloat/fast_float))          |
| **robin_hood**        | High-performance hash map (faster than `unordered_map`)   | 📄 Header-only ([GitHub](https://github.com/martinus/robin-hood-hashing))  |
| **OpenSSL**           | TLS support (`libssl`, `libcrypto`)                       | 📦 Installed in Docker                                                       |
| **zlib**              | Compression library                                       | 📦 Installed in Docker                                                       |
| **CMake**             | Cross-platform build system                               | 📦 Installed in Docker                                                       |
| **g++ 11.4.0**        | C++23-compatible compiler                                 | 📦 Installed in Docker                                                       |

---

## 📊 JSON Parser Benchmark (Binance `bookTicker` Messages)

Parsed ~128K Binance messages using two libraries:

| Parser         | Total Time (ms) | Avg Time per Message (ns) | Speedup |
|----------------|------------------|----------------------------|---------|
| **nlohmann**   | ~185–190         | ~1,416–1,475               | 1×      |
| **simdjson**   | ~19.4–19.5       | ~151–152                   | ~10×    |

- `simdjson` is ideal for high-throughput applications.
- `nlohmann::json` is excellent for readability and outbound message composition.

---

## ⚙️ Development Workflow

All scripts are now in the `scripts/` subdirectory. You can either run them directly or use the `Makefile` for convenience.

### ✅ Option 1: One-Shot Setup (Recommended)

If you're on a Mac with Docker installed:

```sh
./scripts/setup_and_run.sh
```

This will:

1. Build the Docker container (`cpp-dev` or `full-dev`)
2. Launch the Linux development environment
3. Install C++ dependencies
4. Build and run the Binance app:

```sh
./build/binance_main --config_file config.json --key spot
```

---

### 🛠 Option 2: Manual Steps (or via `make`)

#### Build Docker image:

```sh
./scripts/build_docker.sh cpp    # or full
```

Or using `make`:

```sh
make build-cpp
make build-full
```

#### Launch Docker container:

```sh
./scripts/launch-dev.sh cpp    # or full
```

Or using `make`:

```sh
make run-cpp
make run-full
```

#### Install dependencies (inside container):

```sh
./scripts/install_deps.sh
```

Or:

```sh
make deps
```

#### Build the app:

```sh
cd binance
./build_local.sh
```

#### Run the app:

```sh
./build/binance_main --config_file config.json --key spot
```

To run the **futures feed**:

```sh
./build/binance_main --config_file config.json --key fut
```

---

## 🧾 Makefile Targets

Once in the project root, you can also use:

```sh
make help        # list commands
make build-cpp   # build C++ Docker image
make run-cpp     # launch cpp-dev environment
make setup       # full setup (build, launch, install)
```

---

## 📝 Notes

- Written in **C++23**, compiled with `g++ 11.4.0`
- Partial C++23 support — project will upgrade to `g++ 13+`
- Optimized for macOS-based development via Dockerized Linux
- Uses `robin_hood::unordered_flat_map` and `gperf` for efficient symbol lookups


