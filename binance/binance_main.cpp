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

#include "symbol_id_map.hpp"
#include "book_ticker_queue.hpp"

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
  if (args.config_file.empty() || args.key.empty() || args.symbol_file.empty()) {
    std::cerr << "❌ Missing required arguments.\n";
    std::cerr << "✅ Usage: " << argv[0]
              << " --config_file <file> --key <key> --symbol_file <file>\n";
    return args;
  }
  args.valid = true;
  return args;
}

/**
 * @brief Entry point for the WebSocket client.
 *
 * Usage:
 *   ./program --config_file <config_file.json> --key <section_key>
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
  SymbolIdMap filtered_map = filter_symbol_map(complete_map, stream_config.subs);

  BookTickerQueue queue;
  //if (true) return 0;
  ix::WebSocket ws;
  setup_websocket(ws, stream_config, filtered_map, &queue);
  //if (1) return 0;
  ws.start();

  std::cout << "🟢 WebSocket client running. Press Ctrl+C to exit.\n";

  // Poll until Ctrl+C is pressed
  while (running) {
    std::this_thread::sleep_for(std::chrono::seconds(1));
  }

  std::cout << "🔻 Stopping WebSocket...\n";
  ws.stop();

  return 0;
}
