#include "book_ticker.hpp"
#include "book_ticker_parser.hpp"
#include "endpoint_config.hpp"
#include "setup_websocket.hpp"
#include "time_utils.hpp"
#include <cstdint>
#include <fstream>
#include <iostream>
#include <ixwebsocket/IXWebSocket.h>
#include <simdjson.h>
#include <string>
#include <system_error>
#include <vector>

int main(int argc, char **argv) {
  EndpointConfigMap cfgmap;
  const char *cfg_file = argv[1];
  std::string key = argv[2];
  if (!parse_config_file(cfg_file, cfgmap)) {
    return 1;
  }
  EndpointConfig cfg = cfgmap[key];
  ix::WebSocket ws;
  std::string endpoint;
  setup_websocket(ws, cfg.endpoint, cfg.subs);
  //// Prevent main thread from exiting
  std::this_thread::sleep_for(std::chrono::minutes(10));
  return 0;
}
