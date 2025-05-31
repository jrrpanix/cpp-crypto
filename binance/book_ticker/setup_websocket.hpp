#include "stream_config.hpp"
#include "book_ticker_queue.hpp"
#include "book_ticker_parser.hpp"
#include "symbol_id_map.hpp"
#include <iostream>
#include <ixwebsocket/IXWebSocket.h>
#include <nlohmann/json.hpp>
#include <string>
#include <vector>

/**
 * @brief Sets up a WebSocket connection to Binance and subscribes to bookTicker
 * streams. Also handles Ping/Pong and logs errors or connection closure.
 *
 * @param ws        Reference to an ix::WebSocket object.
 * @param endpoint  WebSocket URL to connect to (e.g.
 * "wss://stream.binance.com:9443/ws").
 * @param subs nlohmann::json object
 * Expected input JSON format:
 * {
 *   "btcusdt": 0,
 *   "ethusdt": 1
 * }
 *
 */
inline void setup_websocket(ix::WebSocket &ws, const StreamConfig &cfg, const SymbolIdMap &filtered_map, BookTickerQueue *queue) {
  ws.setUrl(cfg.endpoint);

  ws.setOnMessageCallback([&ws, cfg, &filtered_map, queue](const ix::WebSocketMessagePtr &msg) {
    thread_local simdjson::ondemand::parser parser;
    thread_local BookTicker ticker;
    using ix::WebSocketMessageType;

    switch (msg->type) {
    case WebSocketMessageType::Message:
      std::cerr << "Received: " << msg->str << std::endl;
      try {
	parse_book_ticker(parser, msg->str, ticker, &filtered_map);
      } catch(simdjson::simdjson_error &err) {
	std::cerr << err.what() << std::endl;
      }
      break;

    case WebSocketMessageType::Open:
      std::cout << "Connection established, sending subscribe message..."
                << std::endl;
      {
        std::vector<std::string> streams;
        for (const auto &sym : cfg.subs) {
          streams.push_back(sym + "@bookTicker");
        }

        nlohmann::json sub_msg = {
            {"method", "SUBSCRIBE"}, {"params", streams}, {"id", 1}};

        ws.send(sub_msg.dump());
      }
      break;

    case WebSocketMessageType::Ping:
      std::cout << "[Ping] Received from server, sending Pong..." << std::endl;
      // ws.pong(msg->str);
      break;

    case WebSocketMessageType::Pong:
      std::cout << "[Pong] Received from server." << std::endl;
      break;

    case WebSocketMessageType::Error:
      std::cerr << "Error: " << msg->errorInfo.reason << std::endl;
      break;

    case WebSocketMessageType::Close:
      std::cout << "Connection closed." << std::endl;
      break;

    default:
      std::cerr << "Unhandled WebSocket message type." << std::endl;
      break;
    }
  });
}
