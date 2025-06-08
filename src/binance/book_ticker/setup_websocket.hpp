#include "book_ticker_parser.hpp"
#include "book_ticker_queue.hpp"
#include "stream_config.hpp"
#include "symbol_id_map.hpp"
#include <iostream>
#include <ixwebsocket/IXWebSocket.h>
#include <nlohmann/json.hpp>
#include <string>
#include <vector>

/**
 * @brief Sets up a WebSocket connection to Binance and subscribes to bookTicker
 * streams. Handles incoming messages, parses them using simdjson, and enqueues
 * structured BookTicker messages into a concurrent queue for downstream
 * consumption.
 *
 * Also manages ping/pong frames and logs connection events or message drops.
 *
 * @param ws           Reference to the ix::WebSocket instance to configure and
 * start.
 * @param cfg          Stream configuration including the WebSocket endpoint and
 * symbol subscriptions.
 * @param filtered_map Map of symbol strings to integer IDs used for efficient
 * symbol lookup.
 * @param queue        Optional pointer to a BookTickerQueue. If provided,
 * parsed BookTicker messages will be enqueued; otherwise, messages are parsed
 * but discarded.
 *
 * Notes:
 * - Uses thread-local simdjson parser for high-throughput, thread-safe JSON
 * parsing.
 * - Drops are counted and logged if the queue is full or memory allocation
 * fails.
 * - Throws an exception if more than 500 messages are dropped.
 * - Assumes messages are in Binance Perpetual Futures bookTicker format.
 */

inline void setup_websocket(ix::WebSocket &ws, const StreamConfig &cfg,
                            const SymbolIdMap &filtered_map,
                            BookTickerQueue *queue) {
  ws.setUrl(cfg.endpoint);

  ws.setOnMessageCallback([&ws, cfg, &filtered_map,
                           queue](const ix::WebSocketMessagePtr &msg) {
    thread_local simdjson::ondemand::parser parser;
    thread_local BookTicker ticker;
    using ix::WebSocketMessageType;

    switch (msg->type) {
    case WebSocketMessageType::Message:
      // std::cerr << "Received: " << msg->str << std::endl;
      try {
        parse_book_ticker(parser, msg->str, ticker, true, &filtered_map);
        if (queue && !queue->try_enqueue(ticker)) {
          static std::atomic<int> drop_count = 0;
          drop_count++;
          std::cerr << "⚠️ Queue full or memory error. Drop count: "
                    << drop_count.load() << "\n";
          if (drop_count.load() > 500) {
            throw std::runtime_error("drop count exceeded");
          }
        }

      } catch (simdjson::simdjson_error &err) {
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
