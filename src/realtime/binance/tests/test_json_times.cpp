#include "book_ticker.hpp"
#include "book_ticker_parser.hpp"
#include "book_ticker_parser_nl.hpp"
#include "common/time_utils.hpp"
#include <fstream>
#include <iostream>

std::vector<std::string> get_data(const char *fname) {
  std::vector<std::string> data;
  std::ifstream strm(fname);
  if (!strm.is_open()) {
    std::cerr << "Failed to open " << fname << std::endl;
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

void time_nl(const std::vector<std::string> &lines) {
  if (lines.empty()) {
    std::cout << "[nlohmann] Total time: 0 ms\n";
    std::cout << "[nlohmann] Avg per message: 0 ns\n\n";
    return;
  }
  // Benchmark nlohmann
  {
    BookTicker bt;
    int success = 0;
    auto start = std::chrono::high_resolution_clock::now();
    for (const auto &l : lines) {
      try {
        if (parse_book_ticker_nlohmann(l, bt)) {
          ++success;
        }
      } catch (const std::exception& e) {
        // Silently skip parsing errors
      }
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_ns =
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start)
            .count();
    std::cout << "[nlohmann] Total time: " << duration_ns / 1e6 << " ms\n";
    std::cout << "[nlohmann] Avg per message: " << duration_ns / lines.size()
              << " ns (parsed " << success << "/" << lines.size() << ")\n\n";
  }
}

void time_simd(const std::vector<std::string> &lines) {
  if (lines.empty()) {
    std::cout << "[simdjson] Total time: 0 ms\n";
    std::cout << "[simdjson] Avg per message: 0 ns\n";
    return;
  }
  // Benchmark simdjson
  {
    BookTicker bt;
    simdjson::ondemand::parser parser;
    int success = 0;
    auto start = std::chrono::high_resolution_clock::now();
    for (const auto &l : lines) {
      try {
        if (parse_book_ticker(parser, l, bt, false, nullptr)) {
          ++success;
        }
      } catch (const std::exception& e) {
        // Silently skip parsing errors
      }
    }
    auto end = std::chrono::high_resolution_clock::now();
    auto duration_ns =
        std::chrono::duration_cast<std::chrono::nanoseconds>(end - start)
            .count();
    std::cout << "[simdjson] Total time: " << duration_ns / 1e6 << " ms\n";
    std::cout << "[simdjson] Avg per message: " << duration_ns / lines.size()
              << " ns (parsed " << success << "/" << lines.size() << ")\n";
  }
}

int main(int argc, char **argv) {
  // Default to test data file if no arguments provided
  const char *input_file = "/workspace/test_data/sample.json";
  
  if (argc > 1) {
    input_file = argv[1];
  }
  
  std::cout << "Using input file: " << input_file << std::endl;
  auto lines = get_data(input_file);
  std::cout << "Loaded " << lines.size() << " JSON lines.\n\n";
  
  time_nl(lines);
  time_simd(lines);
  time_nl(lines);
  time_simd(lines);

  return 0;
}
