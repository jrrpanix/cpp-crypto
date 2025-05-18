#include <ixwebsocket/IXWebSocket.h>
#include <simdjson.h>
#include <iostream>
#include <fstream>

int main(int argc, char **argv) {

  if (false) {
    std::ifstream strm(argv[1]);
    std::string data;
    std::getline(strm, data);
    std::cout << data << std::endl;
    simdjson::dom::parser parser_;
    auto obj = parser_.parse(data);
    const std::string &symbol = std::string(obj["s"].get_string().value());
    std::cout << symbol << std::endl;
    int64_t u = obj["u"].get_int64().value();
    std::cout << u << std::endl;
    const std::string &bs = std::string(obj["b"].get_string().value());
    double b = std::stod(bs);
    std::cout << std::fixed << std::setprecision(8) << b << std::endl;
    std::cout << b << std::endl;
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

