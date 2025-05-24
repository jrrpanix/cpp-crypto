## C++ Market Data Processor for Crypto Ecxhanges

This repository in written in C++ to connect to crypto exchanges.

It runs in a linux enviornment via Docker.

The first exchange is Binance bookTicker Channel.

All development has been done on a **MacBook** by running a **Docker** containter which contains the Linux env.  The choice was made to develop in a Docker Container because most people just carry around laptops and its cheaper to Develop locally on a Laptop inside of a Docker Linux Container than to run Linux on a cloud computing machine.  All that is required is a Docker subscripton to get going.  if you already have a Linux enviornment and don't want to use Docker that works too.

The code is compiled and run in Linux with the Linux shell running locally on a Mac by:

- Creating a Linux-based Docker image (e.g., Ubuntu)
- Running the container on macOS using Docker
- Mounting your macOS file system into the container using volumes

This setup enables fully containerized C++ development that integrates seamlessly with local file editing.

---
## Tech Stack

| Library           | Purpose                                                                 | How to Get It                                                                                  |
| ----------------- | ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| **IXWebSocket**   | WebSocket client for C++ with TLS support                               | 🔧 **Build from source**: [IXWebSocket GitHub](https://github.com/machinezone/IXWebSocket)    |
| **simdjson**      | SIMD-accelerated real-time JSON parsing from the exchange               | 🔧 **Build from source**: [simdjson GitHub](https://github.com/simdjson/simdjson)             |
| **nlohmann::json**| Used for constructing outbound JSON (e.g., subscription messages)       | 🔧 **Header-only**: [nlohmann/json GitHub](https://github.com/nlohmann/json)                  |
| **fast_float**    | Fastest string-to-float/double conversion                               | 🔧 **Header-only**: [fast_float GitHub](https://github.com/fastfloat/fast_float)              |
| **OpenSSL**       | TLS/SSL support (`libssl`, `libcrypto`)                                 | 📦 Installed in Docker via `libssl-dev`                                                        |
| **zlib**          | Compression and decompression support                                   | 📦 Installed in Docker via `zlib1g-dev`                                                        |
| **CMake**         | Cross-platform build system                                              | 📦 Installed in Docker                                                                         |
| **g++**           | C++23-compatible compiler                                                | 📦 Installed in Docker (e.g., `g++-13` for full C++23 support)                                 |

### Notes

- The project is written in **C++23**.
- `nlohmann::json` is used primarily to construct outgoing messages (e.g., subscriptions during `on_open`).
- `simdjson` is used to parse incoming high-frequency JSON messages from the exchange with maximum performance.

## JSON Parser Benchmark (Binance `bookTicker` Messages)

Parsed 128,398 JSON messages from Binance using two libraries:

| Parser        | Total Time (ms) | Avg Time per Message (ns) | Speedup vs. nlohmann |
|---------------|------------------|----------------------------|------------------------|
| **nlohmann**  | ~185–190 ms      | ~1,416–1,475 ns            | 1×                     |
| **simdjson**  | ~19.4–19.5 ms    | ~151–152 ns                | **~9–10× faster**      |

### Summary

- `simdjson` demonstrates ~10× faster parsing performance compared to `nlohmann::json` on compact Binance `bookTicker` messages.
- Ideal for high-throughput, low-latency applications (e.g. WebSocket feeds, trading systems).
- `nlohmann::json` still offers excellent usability and STL-style APIs for general-purpose usage.

### Test Details

- Messages loaded from a file: `test_data.json` (128,398 lines)
- Benchmarked using two functions:
  - `parse_book_ticker_nlohmann(const std::string& s, BookTicker& bt)`
  - `parse_book_ticker(const std::string& s, BookTicker& bt)`



## 🚀 Development Workflow

### 1. Build the Docker container

***Run on Mac (should also work on Linux or Windows)***

Docker is cross platform so building the Docker image should work on most OS.  It was only tested on ***MacBook***

This builds an Ubuntu-based image with all dependencies (e.g., CMake, OpenSSL, IXWebSocket):

```sh
./build_linux_docker.sh
```

### 2. Start the Linux Shell

Run the Docker Image, creates a shell to do development in

***start this on your MacBook***

```sh
# run the docker image
# specify the mount point : optional defaults to $HOME/cpp-crypto
# this will be where r/w access between mac/docker will be

./launch-linux-dev.sh
```

### 3. Run Dependency Installation Script

This script automates the download, build, and installation of the following C++ libraries:

- **[IXWebSocket](https://github.com/machinezone/IXWebSocket)**: WebSocket client with TLS support
- **[fast_float](https://github.com/fastfloat/fast_float)**: Fast string-to-float conversion library
- **[nlohmann/json](https://github.com/nlohmann/json)**: Modern C++ JSON library (header-only)
- **[simdjson](https://github.com/simdjson/simdjson)**: High-performance SIMD-accelerated JSON parser

### Usage

```sh
sh install_deps.sh
```