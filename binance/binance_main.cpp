#include "setup_websocket.hpp"
#include "stream_config.hpp"
#include <atomic>
#include <chrono>
#include <csignal>
#include <iostream>
#include <ixwebsocket/IXWebSocket.h>
#include <ranges>
#include <string>
#include <system_error>
#include <thread>
#include <vector>

#include "book_ticker_queue.hpp"
#include "symbol_id_map.hpp"

std::atomic<bool> running(true);

void handle_sigint(int) {
  std::cout << "\n🛑 Caught SIGINT. Exiting gracefully...\n";
  running = false;
}
struct Args {
  std::string config_file;
  std::string key;
  std::string symbol_file;
  bool valid;
};

Args parse_args(int argc, char **argv) {
  Args args;
  args.valid = false;
  // Parse command-line arguments
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--config_file" && i + 1 < argc) {
      args.config_file = argv[++i];
    } else if (arg == "--key" && i + 1 < argc) {
      args.key = argv[++i];
    } else if (arg == "--symbol_file" && i + 1 < argc) {
      args.symbol_file = argv[++i];
    } else {
      std::cerr << "❌ Unknown or malformed argument: " << arg << "\n";
      std::cerr << "✅ Usage: " << argv[0]
                << " --config_file <file> --key <key> --symbol_file <file>\n";
      return args;
    }
  }

  // Validate arguments
  if (args.config_file.empty() || args.key.empty() ||
      args.symbol_file.empty()) {
    std::cerr << "❌ Missing required arguments.\n";
    std::cerr << "✅ Usage: " << argv[0]
              << " --config_file <file> --key <key> --symbol_file <file>\n";
    return args;
  }
  args.valid = true;
  return args;
}

void consume_and_monitor(BookTickerQueue &queue, std::atomic<bool> &running) {
  using clock = std::chrono::steady_clock;
  BookTicker msg;

  int count = 0;
  const int batch_size = 1000;
  auto start = clock::now();

  while (running) {
    if (queue.try_dequeue(msg)) {
      ++count;

      if (count >= batch_size) {
        auto end = clock::now();
        std::chrono::duration<double> elapsed = end - start;

        double total = elapsed.count();
        double rate = batch_size / total;
        std::cout << "📈 Rate: " << rate << " msgs/sec: " << total
                  << " total_time sec\n";

        count = 0;
        start = clock::now();
      }
    } else {
      // Sleep briefly to avoid spinning too hot
      std::this_thread::sleep_for(std::chrono::microseconds(100));
    }
  }

  std::cout << "🛑 Consumer thread exiting...\n";
}
/**
 * @brief Entry point for the Binance WebSocket client application.
 *
 * This function sets up and runs a real-time data pipeline using Binance's
 * `bookTicker` WebSocket stream. It parses a configuration file and a symbol
 * reference file, establishes a WebSocket connection, filters the subscribed
 * symbols, and starts a consumer thread that monitors and processes incoming
 * order book updates.
 *
 * The WebSocket callback parses each message using a thread-local simdjson parser
 * and enqueues structured `BookTicker` messages into a lock-free concurrent queue.
 * The consumer thread dequeues these messages and prints the message rate every
 * 1000 updates.
 *
 * The application exits cleanly when interrupted via Ctrl+C.
 *
 * @param argc Command-line argument count.
 * @param argv Command-line argument vector.
 * @return 0 on successful execution, 1 on error (e.g., invalid args or config).
 *
 * @usage
 *   ./program --config_file <config_file.json> --key <section_key> --symbol_file <symbol_map.json>
 *
 * @details
 * - `--config_file`: Path to the JSON config file containing stream configuration.
 * - `--key`: Section key in the config file specifying which stream to subscribe to.
 * - `--symbol_file`: Path to the JSON file mapping Binance symbols to integer IDs.
 *   The file contains a complete reference of all Binance symbols. The program uses this
 *   to construct a smaller `filtered_map` consisting only of the symbols defined in the stream config.
 */
int main(int argc, char **argv) {
  BookTickerQueue q;
  Args args = parse_args(argc, argv);
  if (!args.valid)
    return 1;

  // Parse config file
  StreamConfigMap cfgmap;
  if (!load_stream_config_file(args.config_file, cfgmap)) {
    return 1;
  }

  write_stream_config(std::cout, cfgmap);

  // Validate key
  if (cfgmap.find(args.key) == cfgmap.end()) {
    std::cerr << "❌ Key not found in config: " << args.key << "\n";
    return 1;
  }

  // Setup signal handler for Ctrl+C
  std::signal(SIGINT, handle_sigint);

  // Setup and start WebSocket
  const StreamConfig &stream_config = cfgmap[args.key];

  SymbolIdMap complete_map = load_symbol_map(args.symbol_file);
  SymbolIdMap filtered_map =
      filter_symbol_map(complete_map, stream_config.subs);

  BookTickerQueue queue;
  ix::WebSocket ws;
  setup_websocket(ws, stream_config, filtered_map, &queue);
  std::thread consumer_thread(consume_and_monitor, std::ref(queue),
                              std::ref(running));
  ws.start();

  std::cout << "🟢 WebSocket client running. Press Ctrl+C to exit.\n";

  // Poll until Ctrl+C is pressed
  while (running) {
    std::this_thread::sleep_for(std::chrono::seconds(1));
  }

  std::cout << "🔻 Stopping WebSocket...\n";
  ws.stop();
  consumer_thread.join();
  return 0;
}
