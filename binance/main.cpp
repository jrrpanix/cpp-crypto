#include "book_ticker.hpp"
#include "book_ticker_parser.hpp"
#include "time_utils.hpp"
#include "setup_websocket.hpp"
#include "parse_config.hpp"
#include <cstdint>
#include <iostream>
#include <fstream>
#include <ixwebsocket/IXWebSocket.h>
#include <simdjson.h>
#include <string>
#include <system_error>
#include <vector>

bool get_config(const char *file_name, std::string &endpoint, std::vector<std::string> &subs) {
  std::ifstream infile(file_name);
  if (!infile.is_open()) {
    std::cerr << "❌ Failed to open file.\n";
    return false;
  }
  return parse_config(infile, endpoint, subs);

}

int main(int argc, char **argv) {
    ix::WebSocket ws;
    std::string endpoint;
    std::vector<std::string> subs;
    if (!get_config(argv[1], endpoint, subs)) {
      return 1;
    }
    std::cout << "endpoint=" << endpoint << std::endl;
    setup_websocket(ws, endpoint, subs);
    //// Prevent main thread from exiting
    std::this_thread::sleep_for(std::chrono::minutes(10));
    return 0;
}
