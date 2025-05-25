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

### ✅ One-Shot Setup (Recommended)

If you're on a Mac with Docker installed, just run:

```sh
./setup_and_run.sh
```

This script will:

1. Build the Docker container (`cpp-dev` or `full-dev`)
2. Launch the Linux dev container
3. Install dependencies via `install_deps.sh`
4. Build the Binance C++ project
5. Run the program:

```sh
./build/binance_main --config_file config.json --key spot
```

To run the **futures feed**:

```sh
./build/binance_main --config_file config.json --key fut
```

---

### 🛠 Manual Setup (If Needed)

**Build Docker container**:

```sh
./build_docker.sh cpp     # Lightweight C++-only
./build_docker.sh full    # Full C++ + Python stack
```

**Launch the container**:

```sh
./launch-dev.sh cpp       # Use current dir
./launch-dev.sh full $HOME/cpp-dev  # Optional path
```

**Inside the container**:

```sh
./install_deps.sh
cd binance
./build_local.sh
./build/binance_main --config_file config.json --key spot
```

---

## 📝 Notes

- Written in **C++23**, compiled with `g++ 11.4.0`
- Partial C++23 support — upgrade to `g++ 13+` recommended
- Designed for macOS-based development using Dockerized Ubuntu Linux
- Uses `robin_hood::unordered_flat_map` for performant symbol lookup

