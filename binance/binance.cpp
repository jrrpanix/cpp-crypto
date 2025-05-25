#include "endpoint_config.hpp"
#include "setup_websocket.hpp"
#include <ixwebsocket/IXWebSocket.h>
#include <string>
#include <system_error>
#include <vector>
#include <thread>
#include <chrono>
#include <iostream>

/**
 * @brief Entry point for the WebSocket client.
 *
 * Usage:
 *   ./program --config_file <config_file.json> --key <section_key>
 */
int main(int argc, char** argv) {
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
            std::cerr << "✅ Usage: " << argv[0] << " --config_file <file> --key <key>\n";
            return 1;
        }
    }

    // Validate arguments
    if (config_file.empty() || key.empty()) {
        std::cerr << "❌ Missing required arguments.\n";
        std::cerr << "✅ Usage: " << argv[0] << " --config_file <file> --key <key>\n";
        return 1;
    }

    // Parse config file
    EndpointConfigMap cfgmap;
    if (!parse_config_file(config_file.c_str(), cfgmap)) {
        return 1;
    }

    // Validate key
    if (cfgmap.find(key) == cfgmap.end()) {
        std::cerr << "❌ Key not found in config: " << key << "\n";
        return 1;
    }

    // Setup and start WebSocket
    const EndpointConfig& cfg = cfgmap[key];
    ix::WebSocket ws;
    setup_websocket(ws, cfg.endpoint, cfg.subs);
    ws.start();

    // Run forever
    std::cout << "🟢 WebSocket client running. Press Ctrl+C to exit.\n";
    while (true) {
        std::this_thread::sleep_for(std::chrono::hours(24));
    }

    return 0;
}

