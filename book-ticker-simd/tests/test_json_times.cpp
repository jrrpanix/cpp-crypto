#include "BookTicker.hpp"
#include "BookTickerParser.hpp"
#include "BookTickerParserNL.hpp"
#include "time_utils.hpp"
#include <fstream>
#include <iostream>

std::vector<std::string> get_data(const char *fname) {
  std::vector<std::string> data;
  std::ifstream strm(fname);
  if (!strm.is_open()) {
    std::cerr << "Failed to open " << fname << "\n";
    return data;
  }
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

void time_nl(const std::vector<std::string> &lines) {
  // Benchmark nlohmann
  {
    BookTicker bt;
    auto start = std::chrono::high_resolution_clock::now();
    for (const auto &l : lines) {
      parse_book_ticker_nlohmann(l, bt);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_ns =
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start)
            .count();
    std::cout << "[nlohmann] Total time: " << duration_ns / 1e6 << " ms\n";
    std::cout << "[nlohmann] Avg per message: " << duration_ns / lines.size()
              << " ns\n\n";
  }
}

void time_simd(const std::vector<std::string> &lines) {
  // Benchmark simdjson
  {
    BookTicker bt;
    simdjson::ondemand::parser parser;
    auto start = std::chrono::high_resolution_clock::now();
    for (const auto &l : lines) {
      parse_book_ticker(parser, l, bt);
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_ns =
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start)
            .count();
    std::cout << "[simdjson] Total time: " << duration_ns / 1e6 << " ms\n";
    std::cout << "[simdjson] Avg per message: " << duration_ns / lines.size()
              << " ns\n";
  }
}

int main(int argc, char **argv) {
  auto lines = get_data(argv[1]);
  std::cout << "Loaded " << lines.size() << " JSON lines.\n\n";
  time_nl(lines);
  time_simd(lines);
  time_nl(lines);
  time_simd(lines);

  return 0;
}
