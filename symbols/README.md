# 🔎 Symbol Lookup Benchmark

This subdirectory benchmarks various symbol lookup methods for use in high-performance market data applications.

It compares the average lookup speed of:

- ✅ `std::unordered_map`
- ✅ `robin_hood::unordered_flat_map`
- ✅ `gperf` (perfect hash)
- ✅ Python `dict`

These tests are designed to simulate high-frequency symbol-to-ID mapping — such as translating Binance `bookTicker` symbols to internal numeric IDs.

---

## 🧪 Benchmark Results

Each method was tested over 1,000,000 randomized lookups on ~1400 Binance symbols:

| Method                     | Avg Lookup Time (ns) |
|----------------------------|----------------------|
| `std::unordered_map`       | 44.44 ns             |
| `robin_hood::flat_map`     | 35.47 ns             |
| `gperf` (perfect hash)     | 24.92 ns             |
| Python `dict` (CPython 3.12)| 45.94 ns            |

---

## ⚙️ Build and Run

### 🔨 Build the benchmark

```sh
./build_local.sh
```

This compiles the C++ benchmarks for `unordered_map`, `robin_hood`, and `gperf`.

### 🚀 Run the benchmark

```sh
./run.sh
```

This executes the compiled C++ benchmarks and the Python timing code. Results are printed to stdout.

---

## 📦 Dependencies

- C++17+ compiler (e.g., g++ 11 or higher)
- `robin_hood.h` (included or installed via `install_deps.sh`)
- `gperf` (precompiled static perfect hash lookup table)
- Python 3.12+ (for Python dict timing)
- `nlohmann/json` and `Polars` for loading `symbols.json`

---

## 📁 Files

| File             | Purpose                                     |
|------------------|---------------------------------------------|
| `build_local.sh` | Builds all benchmark binaries               |
| `run.sh`         | Runs all benchmark tests (C++ and Python)   |
| `symbols.json`   | Symbol-to-ID mapping input file             |
| `symbol_lookup.hpp` | Generated gperf header from `symbols.json` |
| `benchmark_all_maps.cpp` | Main C++ benchmark source            |
| `dict_benchmark.py` | Python benchmark script                  |

---

## 📝 Notes

- `gperf` is the fastest, but requires a static key set.
- `robin_hood::flat_map` is a great drop-in replacement for `unordered_map` with no dependencies.
- Python’s built-in `dict` is competitive for small to mid-size keysets.

```sh
Use this benchmark to guide your choice of lookup strategy depending on latency, key mutability, and codebase simplicity.
```

