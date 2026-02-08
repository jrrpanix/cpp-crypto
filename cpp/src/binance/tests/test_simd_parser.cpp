
#include "book_ticker.hpp"
#include "book_ticker_parser.hpp"
#include "book_ticker_parser_nl.hpp"
#include "stream_config.hpp"
#include "common/time_utils.hpp"
#include <fstream>
#include <iostream>

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

void time_loop(const std::vector<std::string> &data, bool upd_time,
               SymbolIdMap *symbol_lookup) {
  if (data.empty()) {
    std::cout << "Total=0;N=0;BAD=0;Avg=0ns"
              << ";UPD_ON=" << (upd_time ? "YES" : "NO") << "\n";
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
      // Silently count parsing errors
    }
  }
  auto end = std::chrono::high_resolution_clock::now();
  auto duration_ns =
      std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();
  int T = N + BAD;
  std::cout << "Total=" << duration_ns << ";N=" << N << ";BAD=" << BAD
            << ";Avg=" << (duration_ns / T) << "ns"
            << ";UPD_ON=" << (upd_time ? "YES" : "NO") << "\n";
}

void test_parser(const char *fname, const char *cfg_file) {
  auto data = get_data(fname);
  if (data.empty()) {
    std::cerr << "ERROR: No data loaded from file: " << fname << std::endl;
    std::cerr << "Test will run with empty data (division by zero prevented)" << std::endl;
  }
  SymbolIdMap *symbol_lookup = nullptr;
  if (cfg_file) {
    StreamConfigMap cfgmap;
    if (!load_stream_config_file(cfg_file, cfgmap)) {
      return;
    }
    const StreamConfig &stream_config = cfgmap["fut"];
    SymbolIdMap *symbol_lookup = new SymbolIdMap();
    *symbol_lookup = json_to_upper_flat_map(stream_config.subs);
  }

  time_loop(data, false, symbol_lookup);
  time_loop(data, false, symbol_lookup);
  time_loop(data, true, symbol_lookup);
  time_loop(data, true, symbol_lookup);
}

int main(int argc, char **argv) {
  std::cout << sizeof(BookTicker) << std::endl;
  
  // Default to test data file if no arguments provided
  const char *input_file = "/workspace/test_data/sample.json";
  const char *cfg_file = nullptr;
  
  if (argc > 1) {
    input_file = argv[1];
  }
  if (argc > 2) {
    cfg_file = argv[2];
  }
  
  std::cout << "Using input file: " << input_file << std::endl;
  if (cfg_file) {
    std::cout << "Using config file: " << cfg_file << std::endl;
  }
  
  test_parser(input_file, cfg_file);
  return 0;
}
