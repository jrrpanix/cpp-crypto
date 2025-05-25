## 🚀 C++ Market Data Processor for Crypto Exchanges

This project provides a **C++23-based framework** for connecting to crypto exchanges. It is designed to run in a **Linux environment via Docker** but is fully developed and tested on a **MacBook** using Docker containers.

The system currently supports the **Binance Spot** and **Binance Perpetual Futures (futures)** `bookTicker` WebSocket channels, which deliver real-time bid/ask updates.

---

### 💡 Why Docker?

Most developers use laptops (e.g., macOS), which aren’t native Linux systems. Docker provides a lightweight, reproducible Linux environment for:

- Running C++17/20/23 toolchains
- Installing build dependencies like OpenSSL, IXWebSocket, etc.
- Mounting your Mac filesystem for seamless development

No need for cloud VMs or full Linux installs — just Docker.

---

## 🧰 Tech Stack

| Library            | Purpose                                               | Installation                                                                 |
|--------------------|-------------------------------------------------------|------------------------------------------------------------------------------|
| **IXWebSocket**     | WebSocket client with TLS                            | 🔧 Build from source ([GitHub](https://github.com/machinezone/IXWebSocket)) |
| **simdjson**        | Ultra-fast SIMD JSON parsing                         | 🔧 Build from source ([GitHub](https://github.com/simdjson/simdjson))       |
| **nlohmann::json**  | Friendly JSON API for C++                            | 📄 Header-only ([GitHub](https://github.com/nlohmann/json))                 |
| **fast_float**      | High-performance float parsing                       | 📄 Header-only ([GitHub](https://github.com/fastfloat/fast_float))          |
| **OpenSSL**         | TLS support (`libssl`, `libcrypto`)                 | 📦 Installed in Docker                                                       |
| **zlib**            | Compression library                                  | 📦 Installed in Docker                                                       |
| **CMake**           | Build system                                         | 📦 Installed in Docker                                                       |
| **g++ 11.4.0**      | C++23-compatible compiler                            | 📦 Installed in Docker                                                       |

---

## 📊 JSON Parser Benchmark (Binance `bookTicker` Messages)

Parsed ~128K Binance messages using both libraries:

| Parser        | Total Time (ms) | Avg Time per Message (ns) | Speedup |
|---------------|------------------|----------------------------|---------|
| **nlohmann**  | ~185–190         | ~1,416–1,475               | 1×      |
| **simdjson**  | ~19.4–19.5       | ~151–152                   | ~10×    |

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
1. Build the Docker container
2. Launch the Linux development environment
3. Install all C++ dependencies
4. Build the Binance app
5. Run the program:
   ```sh
   ./build/binance_main --config_file config.json --key spot
   ```

---

### 🧭 Manual Steps (Alternative)

#### 1. Build the Docker container

```sh
./build_linux_docker.sh
```

#### 2. Start the Linux container shell

```sh
./launch-linux-dev.sh
```

You can optionally mount a directory (default: `$HOME/cpp-crypto`).

#### 3. Install dependencies

```sh
./install_deps.sh
```

#### 4. Build the source code

```sh
cd binance
./build_local.sh
```

#### 5. Run the program

```sh
./build/binance_main --config_file config.json --key spot
```

> To run the perpetual futures feed, use:
> ```sh
> ./build/binance_main --config_file config.json --key fut
> ```

---

### 📝 Notes

- The project is written using **C++23**, compiled with `g++ 11.4.0`
- `g++ 11.4.0` provides **partial** C++23 support; the project plans to upgrade to **`g++ 13+`** for full standard compliance and access to newer language features
- Developed on **macOS**, executed in a **Dockerized Ubuntu Linux** environment
- Designed to easily support multiple exchange backends (e.g., Binance Spot & Futures)

