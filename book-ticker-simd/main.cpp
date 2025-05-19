#include <ixwebsocket/IXWebSocket.h>
#include <simdjson.h>
#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <fast_float/fast_float.h>
#include <system_error> 

std::vector<std::string> get_data(const char *fname) {
  std::vector<std::string> data;
  std::ifstream strm(fname);
  std::string line;
  while(strm) {
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
        std::string_view bid_qty_str   = doc["B"].get_string().value();
        std::string_view ask_price_str = doc["a"].get_string().value();
        std::string_view ask_qty_str   = doc["A"].get_string().value();

       // Convert to double using fast_float
        double bid_price, bid_qty, ask_price, ask_qty;
        auto err1 = fast_float::from_chars(bid_price_str.data(), bid_price_str.data() + bid_price_str.size(), bid_price);
        auto err2 = fast_float::from_chars(bid_qty_str.data(),   bid_qty_str.data()   + bid_qty_str.size(),   bid_qty);
        auto err3 = fast_float::from_chars(ask_price_str.data(), ask_price_str.data() + ask_price_str.size(), ask_price);
        auto err4 = fast_float::from_chars(ask_qty_str.data(),   ask_qty_str.data()   + ask_qty_str.size(),   ask_qty);

	if (  (err1.ec != std::errc()) ||
	      (err2.ec != std::errc()) ||
	      (err3.ec != std::errc()) ||
	      (err4.ec != std::errc())) {
	  return false;
	}
	//std::cout << bid_price  << " " << bid_qty << " " << ask_price << " " << ask_qty << std::endl;
	
	return true;
}


int main(int argc, char **argv) {
  bool p = 1;
  if (p) {
    auto data = get_data(argv[1]);
    simdjson::ondemand::parser parser;
    int i = 0;
    for(auto it : data) {
      bool rv = parse_data(parser, it);
      if (rv) ++i;
    }
    std::cout << i << std::endl;
    return 0;
  
  }
    ix::WebSocket ws;
    ws.setUrl("wss://fstream.binance.com/ws/btcusdt@bookTicker");

    // Persistent simdjson objects
    simdjson::ondemand::parser parser;

    ws.setPingInterval(30);

    ws.setOnMessageCallback([&parser](const ix::WebSocketMessagePtr& msg) {
        if (msg->type == ix::WebSocketMessageType::Message) {
            try {
	      std::cout << msg->str << std::endl;
	      simdjson::padded_string padded(msg->str);
                auto doc = parser.iterate(padded);
                std::string symbol = std::string(doc["s"].get_string().value());
                std::string bid    = std::string(doc["b"].get_string().value());
                std::string ask    = std::string(doc["a"].get_string().value());

                std::cout << "Symbol: " << symbol
                          << " | Bid: " << bid
                          << " | Ask: " << ask << "\n";
            } catch (const simdjson::simdjson_error& e) {
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

