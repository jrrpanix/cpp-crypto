#include <iostream>
#include <ixwebsocket/IXWebSocket.h>
#include <nlohmann/json.hpp>
#include <vector>

int main() {
  ix::WebSocket ws;

  ws.setUrl("wss://stream.binance.com:9443/ws");

  ws.setOnMessageCallback([&ws](const ix::WebSocketMessagePtr &msg) {
    if (msg->type == ix::WebSocketMessageType::Message) {
      std::cout << "Received: " << msg->str << std::endl;
    } else if (msg->type == ix::WebSocketMessageType::Open) {
      std::cout << "Connection established, sending subscribe message..."
                << std::endl;

      // Prepare JSON subscription message
      std::vector<std::string> symbols = {"btcusdt", "ethusdt", "adausdt"};
      std::vector<std::string> streams;
      for (const auto &sym : symbols) {
        streams.push_back(sym + "@bookTicker");
      }

      nlohmann::json sub_msg = {
          {"method", "SUBSCRIBE"}, {"params", streams}, {"id", 1}};

      ws.send(sub_msg.dump());
    } else if (msg->type == ix::WebSocketMessageType::Error) {
      std::cerr << "Error: " << msg->errorInfo.reason << std::endl;
    } else if (msg->type == ix::WebSocketMessageType::Close) {
      std::cout << "Connection closed." << std::endl;
    }
  });

  ws.start();

  // Wait for user input to quit
  std::cout << "Press Enter to quit..." << std::endl;
  std::cin.get();

  ws.stop();
  return 0;
}
