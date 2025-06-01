
#include "book_ticker.hpp"
#include "book_ticker_parser.hpp"
#include "book_ticker_parser_nl.hpp"
#include "stream_config.hpp"
#include "time_utils.hpp"
#include <fstream>
#include <iostream>

std::vector<std::string> get_data(const char *fname) {
  std::vector<std::string> data;
  std::ifstream strm(fname);
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
  auto start = std::chrono::high_resolution_clock::now();
  simdjson::ondemand::parser parser;
  BookTicker bt;
  int N = 0;
  int BAD = 0;
  for (auto it : data) {
    bool rv = parse_book_ticker(parser, it, bt, upd_time, symbol_lookup);
    if (rv) {
      ++N;
    } else
      ++BAD;
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
  const char *cfg_file = argc > 2 ? argv[2] : nullptr;
  test_parser(argv[1], cfg_file);
  return 0;
}
