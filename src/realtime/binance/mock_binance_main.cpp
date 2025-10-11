#include "book_ticker/book_ticker_parser.hpp" // defines parse_book_ticker
#include "book_ticker/stream_config.hpp"
#include "book_ticker/symbol_id_map.hpp" // defines load_symbol_map
#include <chrono>
#include <fstream>
#include <iostream>
#include <simdjson.h>
#include <string>
#include <thread>
#include <zmq.hpp>

std::string extract_json_from_line(const std::string &line) {
  size_t start = line.find('{');
  size_t end = line.rfind('}');
  if (start != std::string::npos && end != std::string::npos && end > start) {
    return line.substr(start, end - start + 1);
  }
  return {};
}

int main(int argc, char **argv) {
  std::string data_file = "/workspace/test_data/sample.json";
  std::string config_file = "/workspace/apps/config/binance/config.json";
  std::string symbol_file = "/workspace/apps/config/binance/symbols.json";
  std::string key = "fut";

  SymbolIdMap complete_map = load_symbol_map(symbol_file);
  std::ifstream infile(data_file);
  if (!infile) {
    std::cerr << "❌ Failed to open: " << data_file << "\n";
    return 1;
  }

  // Parse config file
  StreamConfigMap cfgmap;
  if (!load_stream_config_file(config_file, cfgmap)) {
    std::cerr << "band file " << std::endl;
    return 1;
  }

  // Validate key
  if (cfgmap.find(key) == cfgmap.end()) {
    std::cerr << "❌ Key not found in config: " << key << "\n";
    return 1;
  }

  const StreamConfig &stream_config = cfgmap[key];

  SymbolIdMap filtered_map =
      filter_symbol_map(complete_map, stream_config.subs);
  std::cout << "subs" << std::endl;
  for (auto x : stream_config.subs) {
    std::cout << x << std::endl;
  }
  std::cout << "mapping" << std::endl;
  for (const auto &[key, value] : filtered_map) {
    std::cout << key << " " << value << std::endl;
  }
  zmq::context_t context(1);
  zmq::socket_t socket(context, zmq::socket_type::pub);
  socket.bind("tcp://0.0.0.0:5555");
  std::cerr << "🧪 ZMQ PUB bound to tcp://0.0.0.0:5555\n";

  std::this_thread::sleep_for(
      std::chrono::seconds(1)); // Allow subscriber time to connect

  thread_local simdjson::ondemand::parser parser;
  thread_local BookTicker ticker;

  std::string line;
  int line_count = 0;
  while (std::getline(infile, line)) {
    std::string json_str = extract_json_from_line(line);
    if (json_str.empty())
      continue;

    try {
      if (parse_book_ticker(parser, json_str, ticker, true, &filtered_map)) {
        ticker.my_receive_time_ns =
            std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::system_clock::now().time_since_epoch())
                .count();

        zmq::message_t zmq_msg(sizeof(BookTicker));
        std::memcpy(zmq_msg.data(), &ticker, sizeof(BookTicker));
        socket.send(zmq_msg, zmq::send_flags::none);

        std::cout << "📤 Sent BookTicker: id=" << ticker.id << "\n";
      } else {
        std::cerr << "⚠️ Failed to parse line " << line_count << "\n";
      }
    } catch (const std::exception &e) {
      std::cerr << "❌ Exception at line " << line_count << ": " << e.what()
                << "\n";
    }

    ++line_count;
    std::this_thread::sleep_for(
        std::chrono::milliseconds(100)); // simulate real-time pacing
  }

  std::cerr << "✅ Finished sending all messages.\n";
  return 0;
}
