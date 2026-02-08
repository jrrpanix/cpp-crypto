#include "book_ticker.hpp"
#include "book_ticker_parser.hpp"
#include "book_ticker_parser_baseline.hpp"
#include "symbol_id_map.hpp"
#include "common/time_utils.hpp"
#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp>

std::vector<std::string> get_data(const char *fname) {
  std::vector<std::string> data;
  std::ifstream strm(fname);
  if (!strm) {
    std::cerr << "ERROR: Failed to open input file: " << fname << std::endl;
    return data;
  }
  std::cout << "Reading input file: " << fname << std::endl;
  std::string line;
  while (strm) {
    std::getline(strm, line);
    size_t start = line.find('{');
    if (start == std::string::npos)
      continue;
    data.push_back(line.substr(start));
  }
  return data;
}

void time_baseline(const std::vector<std::string> &data, bool upd_time,
               SymbolIdMap *symbol_lookup) {
  if (data.empty()) {
    std::cout << "[BASELINE] Total=0;N=0;BAD=0;Avg=0ns"
              << ";TIME=" << (upd_time ? "YES" : "NO")
              << ";LOOKUP=" << (symbol_lookup ? "YES" : "NO") << "\n";
    return;
  }
  auto start = std::chrono::high_resolution_clock::now();
  simdjson::ondemand::parser parser;
  BookTicker bt;
  int N = 0;
  int BAD = 0;
  for (auto it : data) {
    try {
      bool rv = parse_book_ticker_baseline(parser, it, bt, upd_time, symbol_lookup);
      if (rv) {
        ++N;
      } else
        ++BAD;
    } catch (const std::exception& e) {
      ++BAD;
    }
  }
  auto end = std::chrono::high_resolution_clock::now();
  auto duration_ns =
      std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
  int T = N + BAD;
  std::cout << "[BASELINE] Total=" << duration_ns << ";N=" << N << ";BAD=" << BAD
            << ";Avg=" << (duration_ns / T) << "ns"
            << ";TIME=" << (upd_time ? "YES" : "NO")
            << ";LOOKUP=" << (symbol_lookup ? "YES" : "NO") << "\n";
}

void time_optimized(const std::vector<std::string> &data, bool upd_time,
               SymbolIdMap *symbol_lookup) {
  if (data.empty()) {
    std::cout << "[OPTIMIZED] Total=0;N=0;BAD=0;Avg=0ns"
              << ";TIME=" << (upd_time ? "YES" : "NO")
              << ";LOOKUP=" << (symbol_lookup ? "YES" : "NO") << "\n";
    return;
  }
  auto start = std::chrono::high_resolution_clock::now();
  simdjson::ondemand::parser parser;
  BookTicker bt;
  int N = 0;
  int BAD = 0;
  for (auto it : data) {
    try {
      bool rv = parse_book_ticker(parser, it, bt, upd_time, symbol_lookup);
      if (rv) {
        ++N;
      } else
        ++BAD;
    } catch (const std::exception& e) {
      ++BAD;
    }
  }
  auto end = std::chrono::high_resolution_clock::now();
  auto duration_ns =
      std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
  int T = N + BAD;
  std::cout << "[OPTIMIZED] Total=" << duration_ns << ";N=" << N << ";BAD=" << BAD
            << ";Avg=" << (duration_ns / T) << "ns"
            << ";TIME=" << (upd_time ? "YES" : "NO")
            << ";LOOKUP=" << (symbol_lookup ? "YES" : "NO") << "\n";
}

void test_compare(const char *fname, const char *symbol_file) {
  auto data = get_data(fname);
  if (data.empty()) {
    std::cerr << "ERROR: No data loaded from file: " << fname << std::endl;
    return;
  }
  
  SymbolIdMap *symbol_lookup = nullptr;
  if (symbol_file) {
    std::ifstream f(symbol_file);
    if (!f) {
      std::cerr << "ERROR: Cannot open symbol file: " << symbol_file << std::endl;
      return;
    }
    nlohmann::json symbol_json;
    f >> symbol_json;
    
    symbol_lookup = new SymbolIdMap();
    *symbol_lookup = json_to_upper_flat_map(symbol_json);
    std::cout << "Loaded " << symbol_lookup->size() << " symbols from " << symbol_file << "\n";
  }

  std::cout << "\n=== COMPARISON: BASELINE vs OPTIMIZED ===\n";
  std::cout << "Legend: TIME=local timestamp, LOOKUP=symbol map lookup\n\n";
  
  std::cout << "--- Scenario 1: No time, No lookup ---\n";
  time_baseline(data, false, nullptr);
  time_optimized(data, false, nullptr);
  
  std::cout << "\n--- Scenario 2: No time, With lookup ---\n";
  time_baseline(data, false, symbol_lookup);
  time_optimized(data, false, symbol_lookup);
  
  std::cout << "\n--- Scenario 3: With time, No lookup ---\n";
  time_baseline(data, true, nullptr);
  time_optimized(data, true, nullptr);
  
  std::cout << "\n--- Scenario 4: With time, With lookup ---\n";
  time_baseline(data, true, symbol_lookup);
  time_optimized(data, true, symbol_lookup);

  if (symbol_lookup) delete symbol_lookup;
}

int main(int argc, char **argv) {
  std::cout << "BookTicker size: " << sizeof(BookTicker) << " bytes\n\n";
  
  const char *input_file = "/workspace/test_data/sample.json";
  const char *symbol_file = "/workspace/config/binance/symbols.json";
  
  std::cout << "Using input file: " << input_file << std::endl;
  std::cout << "Using symbol map: " << symbol_file << std::endl;
  std::cout << "NOTE: Full symbol map used - larger than production subset\n";
  
  test_compare(input_file, symbol_file);
  return 0;
}
