
#include "BookTicker.hpp"
#include "BookTickerParser.hpp"
#include "BookTickerParserNL.hpp"
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

void time_loop(const std::vector<std::string> &data, bool upd_time) {
  auto start = std::chrono::high_resolution_clock::now();
  simdjson::ondemand::parser parser;
  BookTicker bt;
  int N = 0;
  int BAD = 0;
  for (auto it : data) {
    bool rv = parse_book_ticker(parser, it, bt);
    if (rv) {
      ++N;
      if (upd_time)
        bt.my_receive_time_ns = now_ns_since_epoch();
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

void test_parser(const char *fname) {
  auto data = get_data(fname);
  time_loop(data, false);
  time_loop(data, false);
  time_loop(data, true);
  time_loop(data, true);
}

int main(int argc, char **argv) {
  std::cout << sizeof(BookTicker) << std::endl;
  test_parser(argv[1]);
  return 0;
}
