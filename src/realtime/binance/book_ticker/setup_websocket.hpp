#pragma once
#include "book_ticker_parser.hpp"
#include "book_ticker_queue.hpp"
#include "stream_config.hpp"
#include "symbol_id_map.hpp"
#include <chrono>
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
                            BookTickerQueue *queue, bool debug) {
  ws.setUrl(cfg.endpoint);

  // Per-connection drop counter (not shared across multiple websocket instances)
  auto drop_count = std::make_shared<std::atomic<int>>(0);

  // Message rate tracking (messages processed per second)
  auto msg_count = std::make_shared<std::atomic<int64_t>>(0);
  auto last_rate_log = std::make_shared<std::chrono::steady_clock::time_point>(
      std::chrono::steady_clock::now());

  ws.setOnMessageCallback([&ws, cfg, &filtered_map, queue, debug, drop_count,
                           msg_count,
                           last_rate_log](const ix::WebSocketMessagePtr &msg) {
    thread_local simdjson::ondemand::parser parser;
    thread_local BookTicker ticker;
    using ix::WebSocketMessageType;

    switch (msg->type) {
    case WebSocketMessageType::Message:
      if (debug)
        std::cerr << "Received: " << msg->str << std::endl;
      
      // Skip subscription response messages (e.g., {"result":null,"id":1})
      // These don't have the "u" field that bookTicker has
      if (msg->str.find("\"result\"") != std::string::npos || 
          msg->str.find("\"u\"") == std::string::npos) {
        if (debug || msg->str.find("\"result\"") != std::string::npos) {
          std::cout << "⏭️  Skipping non-bookTicker message: " << msg->str << "\n";
        }
        break;
      }
      
      try {
        parse_book_ticker(parser, msg->str, ticker, true, &filtered_map);
        if (queue && !queue->try_enqueue(ticker)) {
          (*drop_count)++;
          std::cerr << "⚠️ Queue full or memory error. Drop count: "
                    << drop_count->load() << "\n";
          if (drop_count->load() > 500) {
            throw std::runtime_error("drop count exceeded");
          }
        } else {
          // Track successful message rate
          (*msg_count)++;
          auto now = std::chrono::steady_clock::now();
          auto elapsed =
              std::chrono::duration_cast<std::chrono::seconds>(
                  now - *last_rate_log)
                  .count();
          if (elapsed >= 5) {  // Log every 5 seconds
            int64_t count = msg_count->exchange(0);
            double rate = static_cast<double>(count) / elapsed;
            std::cout << "📊 Message rate: " << rate
                      << " msg/sec (" << count << " in " << elapsed
                      << "s)\n";
            *last_rate_log = now;
          }
        }

      } catch (simdjson::simdjson_error &err) {
        std::cerr << "Parse error: " << err.what() << std::endl;
      } catch (const std::exception &err) {
        std::cerr << "Exception: " << err.what() << std::endl;
      }
      break;

    case WebSocketMessageType::Open:
      std::cout << "Connection established, sending subscribe message..."
                << std::endl;
      {
        std::vector<std::string> streams;
        std::cout << "📝 Building subscription streams for " << cfg.subs.size()
                  << " symbol(s):\n";
        for (const auto &sym : cfg.subs) {
          std::string stream_name = sym + "@bookTicker";
          streams.push_back(stream_name);
          std::cout << "   - " << stream_name << "\n";
        }

        nlohmann::json sub_msg = {
            {"method", "SUBSCRIBE"}, {"params", streams}, {"id", 1}};

        std::string payload = sub_msg.dump();
        std::cout << "\n🔗 Sending subscription payload:\n" << payload
                  << "\n\n";

        ws.send(payload);
      }
      break;

    case WebSocketMessageType::Ping:
      std::cout << "[Ping] Received from server, sending Pong..." << std::endl;
      // Binance sends ping approximately every 180 seconds with a time integer
      // payload. The IXWebSocket library automatically responds with pong, so
      // manual pong handling (ws.pong(msg->str)) is not required.
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
