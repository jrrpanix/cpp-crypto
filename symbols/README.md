# 🔍 Benchmark: `unordered_map` vs `gperf` for Symbol Lookup

This directory contains a performance benchmark comparing two methods for mapping cryptocurrency symbol strings (e.g. `"btcusdt"`) to integer IDs:

- `std::unordered_map<std::string, int32_t>`
- A perfect hash function generated using `gperf`

The benchmark performs **1,000,000 randomized lookups** across approximately **1434 Binance trading symbols**.

---

## 🚀 Quick Start

To build and run the benchmark:

```sh
./build_local.sh
./build/bench
```

This will output the average lookup time for both methods.

---

## ⚙️ Benchmark Summary

| Method             | Key Count | Avg Lookup Time | Relative Speed |
|--------------------|-----------|------------------|----------------|
| `unordered_map`     | 1434      | **44.25 ns**      | 1×             |
| `gperf`             | 1434      | **17.61 ns**      | ~**2.5× faster** |

---

## 📂 Files

| File                   | Purpose                                                                 |
|------------------------|-------------------------------------------------------------------------|
| `build_local.sh`       | Compiles the benchmark (`benchmark_symbol_lookup.cpp`)                  |
| `symbols.json`         | Symbol-to-ID map generated from Binance exchange info                   |
| `symbol_keywords.gperf`| Gperf input used to generate `symbol_lookup.hpp`                        |
| `symbol_lookup.hpp`    | Auto-generated header with perfect hash lookup function                 |
| `benchmark_symbol_lookup.cpp` | Benchmark code comparing both methods                         |

---

## 🌐 Binance Exchange Data Source

The symbol list is dynamically sourced from Binance's official **Exchange Information** endpoint:

```
https://api.binance.com/api/v3/exchangeInfo
```

This provides all active trading pairs (e.g. `"btcusdt"`, `"ethusdt"`) for the current day. Only pairs with `"status": "TRADING"` are included.

---

## 📈 Notes

- `gperf` provides **constant-time, collision-free** lookups using precomputed hash tables
- `unordered_map` offers **dynamic flexibility** but incurs runtime hashing and memory overhead
- At this scale (~1400 keys), `gperf` is ~2.5× faster and uses less memory
- 🧠 **Performance improves significantly when the number of symbols is smaller**, especially for `unordered_map`, due to better CPU cache locality and fewer collisions

---

## 🛠️ Dependencies

- `g++` with C++17 support
- [`nlohmann/json`](https://github.com/nlohmann/json) (header-only, for parsing `symbols.json`)
- [`gperf`](https://www.gnu.org/software/gperf/)

Install on Ubuntu:

```sh
sudo apt-get install g++ gperf
```

---

## 🧪 Want to regenerate symbols?

Use the `generate_symbol_files.py` script (Python 3.12+ with `requests`):

```sh
python3 generate_symbol_files.py
```

This will:
- Fetch Binance trading symbols
- Create `symbol_keywords.gperf` and `symbols.json`
- Use those as inputs for benchmarking

---

