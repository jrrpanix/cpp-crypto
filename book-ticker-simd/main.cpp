#include <cstdint>
#include <iostream>
#include <ixwebsocket/IXWebSocket.h>
#include <simdjson.h>
#include <string>
#include <system_error>
#include <vector>
#include "BookTicker.hpp"
#include "BookTickerParser.hpp"
#include "time_utils.hpp"


int main(int argc, char **argv) {
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
