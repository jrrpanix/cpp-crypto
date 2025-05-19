#include <cstdint>
#include <fast_float/fast_float.h>
#include <fstream>
#include <iostream>
#include <ixwebsocket/IXWebSocket.h>
#include <simdjson.h>
#include <string>
#include <system_error>
#include <vector>
//#include <immintrin.h>  // For _alignas128 or _alignas64 if needed
#include <cassert>
#include <cstdint>

struct alignas(64) BookTicker {
  double bid_price; // "b"
  double bid_qty;   // "B"
  double ask_price; // "a"
  double ask_qty;   // "A"

  int64_t update_id;  // "u"
  int64_t trade_time; // "T"
  int64_t event_time; // "E"

  int32_t id;      // internal symbol ID (e.g. 0 = BTCUSDT)
  int32_t padding; // pad to keep struct 64-byte aligned
};

static_assert(sizeof(BookTicker) == 64, "BookTicker must be 64 bytes");

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

bool parse_data(simdjson::ondemand::parser &parser, const std::string &s) {
  simdjson::padded_string padded(s);
  auto doc = parser.iterate(padded);
  /*
  std::string symbol = std::string(doc["s"].get_string().value());
  std::string bid    = std::string(doc["b"].get_string().value());
  std::string ask    = std::string(doc["a"].get_string().value());
  if (false)
    std::cout << "Symbol: " << symbol
              << " | Bid: " << bid
              << " | Ask: " << ask << "\n";
  */

  // Extract the string views
  std::string_view bid_price_str = doc["b"].get_string().value();
  std::string_view bid_qty_str = doc["B"].get_string().value();
  std::string_view ask_price_str = doc["a"].get_string().value();
  std::string_view ask_qty_str = doc["A"].get_string().value();

  // Convert to double using fast_float
  double bid_price, bid_qty, ask_price, ask_qty;
  auto err1 = fast_float::from_chars(
      bid_price_str.data(), bid_price_str.data() + bid_price_str.size(),
      bid_price);
  auto err2 = fast_float::from_chars(
      bid_qty_str.data(), bid_qty_str.data() + bid_qty_str.size(), bid_qty);
  auto err3 = fast_float::from_chars(
      ask_price_str.data(), ask_price_str.data() + ask_price_str.size(),
      ask_price);
  auto err4 = fast_float::from_chars(
      ask_qty_str.data(), ask_qty_str.data() + ask_qty_str.size(), ask_qty);

  if ((err1.ec != std::errc()) || (err2.ec != std::errc()) ||
      (err3.ec != std::errc()) || (err4.ec != std::errc())) {
    return false;
  }
  // std::cout << bid_price  << " " << bid_qty << " " << ask_price << " " <<
  // ask_qty << std::endl;
  int64_t update_id = doc["u"].get_int64().value();
  std::string_view symbol = std::string(doc["s"].get_string().value());

  int64_t trade_time = doc["T"].get_int64().value();
  int64_t event_time = doc["E"].get_int64().value();
  return true;
}

int main(int argc, char **argv) {
  std::cout << sizeof(BookTicker) << std::endl;
  bool p = 1;
  if (p) {
    auto data = get_data(argv[1]);
    simdjson::ondemand::parser parser;
    int i = 0;
    for (auto it : data) {
      bool rv = parse_data(parser, it);
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
