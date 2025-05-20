#include <cstdint>
#include <fast_float/fast_float.h>
#include <fstream>
#include <iostream>
#include <ixwebsocket/IXWebSocket.h>
#include <simdjson.h>
#include <string>
#include <system_error>
#include <vector>
#include "BookTicker.hpp"
#include "BookTickerParser.hpp"
#include "time_utils.hpp"

//#include <immintrin.h>  // For _alignas128 or _alignas64 if needed

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


int main(int argc, char **argv) {
  std::cout << sizeof(BookTicker) << std::endl;
  bool p = 1;
  if (p) {
    auto data = get_data(argv[1]);
    simdjson::ondemand::parser parser;
    BookTicker bt;
    int i = 0;
    for (auto it : data) {
      bool rv = parse_book_ticker(parser, it, bt);
      if (rv)
        ++i;
    }
    std::cout << i << std::endl;
    return 0;
  }
  ix::WebSocket ws;
  ws.setUrl("wss://fstream.binance.com/ws/btcusdt@bookTicker");

  // Persistent simdjson objects
  simdjson::ondemand::parser parser;

  ws.setPingInterval(30);

  ws.setOnMessageCallback([&parser](const ix::WebSocketMessagePtr &msg) {
    if (msg->type == ix::WebSocketMessageType::Message) {
      try {
        std::cout << msg->str << std::endl;
        simdjson::padded_string padded(msg->str);
        auto doc = parser.iterate(padded);
        std::string symbol = std::string(doc["s"].get_string().value());
        std::string bid = std::string(doc["b"].get_string().value());
        std::string ask = std::string(doc["a"].get_string().value());

        std::cout << "Symbol: " << symbol << " | Bid: " << bid
                  << " | Ask: " << ask << "\n";
      } catch (const simdjson::simdjson_error &e) {
        std::cerr << "JSON parse error: " << e.what() << "\n";
        throw std::runtime_error(e.what());
      }
    }
  });

  ws.start();
  std::this_thread::sleep_for(std::chrono::minutes(10));
  ws.stop();
  return 0;
}
