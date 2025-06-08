# 🔎 Symbol Lookup Benchmark

This subdirectory benchmarks various symbol lookup methods for use in high-performance market data applications.

It compares the average lookup speed of:

- ✅ `std::unordered_map`
- ✅ `robin_hood::unordered_flat_map`
- ✅ `gperf` (perfect hash)
- ✅ Python `dict`

These tests simulate real-time symbol-to-ID translation — such as mapping Binance `bookTicker` symbols to internal numeric IDs during market data processing.

---

## 🌐 Data Source

Symbol data is retrieved from the **Binance Exchange Information API**:

```
https://api.binance.com/api/v3/exchangeInfo
```

This provides all active trading pairs (e.g., `BTCUSDT`, `ETHUSDT`) used to generate the lookup tables.

The script `generate_symbol_files.py`:
- Downloads the exchange info from Binance
- Writes the symbol list with numeric IDs to `symbols.json`
- Generates `symbol_lookup.hpp`, a perfect hash table used by gperf-based lookups

---

## 🧪 Benchmark Results

Each method was tested over 1,000,000 randomized lookups on ~1400 Binance symbols:

| Method                     | Avg Lookup Time (ns) |
|----------------------------|----------------------|
| `std::unordered_map`       | 44.44 ns             |
| `robin_hood::flat_map`     | 35.47 ns             |
| `gperf` (perfect hash)     | 24.92 ns             |
| Python `dict` (CPython 3.12) | 45.94 ns           |

---

## ⚙️ Build and Run

### 🔄 Generate Symbol Files

If not already generated:

```sh
uv run python generate_symbol_files.py
```

This produces:
- `symbols.json` for dynamic C++/Python maps
- `symbol_lookup.hpp` for static gperf-based lookup

### 🔨 Build the benchmark

```sh
./build_local.sh
```

This compiles the C++ benchmarks for `unordered_map`, `robin_hood`, and `gperf`.

### 🚀 Run the benchmark

```sh
./run.sh
```

This runs the compiled C++ benchmarks and the Python dict timing. Results are printed to stdout.

---

## 📦 Dependencies

- C++17+ compiler (e.g., `g++ 11+`)
- `robin_hood.h` (included or installed via `install_deps.sh`)
- `gperf` (used to generate perfect hash header)
- Python 3.12+ with:
  - `requests`
  - `polars`
- `nlohmann/json.hpp` for C++ JSON parsing

---

## 📁 Files

| File                  | Purpose                                         |
|-----------------------|-------------------------------------------------|
| `generate_symbol_files.py` | Downloads Binance symbols and generates `symbols.json` and `symbol_lookup.hpp` |
| `symbols.json`        | Symbol-to-ID mapping (used by Python and C++)   |
| `symbol_lookup.hpp`   | Generated perfect hash lookup header for gperf  |
| `benchmark_all_maps.cpp` | C++ benchmark source                         |
| `dict_benchmark.py`   | Python dictionary benchmark                     |
| `build_local.sh`      | Builds all C++ benchmark binaries               |
| `run.sh`              | Runs all benchmarks (C++ and Python)            |

---

## 📝 Notes

- `gperf` is the fastest but only supports static key sets.
- `robin_hood::flat_map` is a high-performance drop-in replacement for `unordered_map`.
- Python `dict` is competitive but limited to Python-side workloads.
- Use this benchmark suite to decide the best trade-off for latency-sensitive symbol lookup.

```sh
Use ./generate_symbol_files.py to stay up to date with Binance's active symbols.
```

