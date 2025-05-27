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

std::atomic<bool> running(true);

void handle_sigint(int) {
  std::cout << "\n🛑 Caught SIGINT. Exiting gracefully...\n";
  running = false;
}

/**
 * @brief Entry point for the WebSocket client.
 *
 * Usage:
 *   ./program --config_file <config_file.json> --key <section_key>
 */
int main(int argc, char **argv) {
  std::string config_file;
  std::string key;

  // Parse command-line arguments
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--config_file" && i + 1 < argc) {
      config_file = argv[++i];
    } else if (arg == "--key" && i + 1 < argc) {
      key = argv[++i];
    } else {
      std::cerr << "❌ Unknown or malformed argument: " << arg << "\n";
      std::cerr << "✅ Usage: " << argv[0]
                << " --config_file <file> --key <key>\n";
      return 1;
    }
  }

  // Validate arguments
  if (config_file.empty() || key.empty()) {
    std::cerr << "❌ Missing required arguments.\n";
    std::cerr << "✅ Usage: " << argv[0]
              << " --config_file <file> --key <key>\n";
    return 1;
  }

  // Parse config file
  StreamConfigMap cfgmap;
  if (!load_stream_config_file(config_file, cfgmap)) {
    return 1;
  }
  write_stream_config(std::cout, cfgmap);

  // Validate key
  if (cfgmap.find(key) == cfgmap.end()) {
    std::cerr << "❌ Key not found in config: " << key << "\n";
    return 1;
  }

  // Setup signal handler for Ctrl+C
  std::signal(SIGINT, handle_sigint);

  // Setup and start WebSocket
  const StreamConfig &stream_config = cfgmap[key];
  SymbolIdMap symbol_lookup = json_to_upper_flat_map(stream_config.subs);

  for (const auto &[symbol, id] : symbol_lookup) {
    std::cout << symbol << " → " << id << '\n';
  }
  ix::WebSocket ws;
  setup_websocket(ws, stream_config.endpoint, stream_config.subs);
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
