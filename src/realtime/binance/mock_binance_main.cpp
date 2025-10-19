#include "book_ticker/book_ticker_parser.hpp" // defines parse_book_ticker
#include "book_ticker/stream_config.hpp"
#include "book_ticker/symbol_id_map.hpp" // defines load_symbol_map
#include <chrono>
#include <fstream>
#include <iostream>
#include <random>
#include <simdjson.h>
#include <string>
#include <thread>
#include <vector>
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
  // Default values
  std::string data_file = "/workspace/test_data/sample.json";
  std::string config_file = "/workspace/apps/config/binance/config.json";
  std::string symbol_file = "/workspace/apps/config/binance/symbols.json";
  std::string key = "fut";
  int throttle_ms = 20; // Default 20ms = 50 messages/second max
  double price_variation = 0.001; // Default 0.1% price variation
  double shock_probability = 0.05; // 5% chance of price shock per message
  double shock_magnitude = 0.02; // 2% price shock when it occurs
  
  // Parse command line arguments
  for (int i = 1; i < argc; i++) {
    if (std::string(argv[i]) == "--throttle" && i + 1 < argc) {
      throttle_ms = std::stoi(argv[++i]);
    } else if (std::string(argv[i]) == "--variation" && i + 1 < argc) {
      price_variation = std::stod(argv[++i]);
    } else if (std::string(argv[i]) == "--shock-prob" && i + 1 < argc) {
      shock_probability = std::stod(argv[++i]);
    } else if (std::string(argv[i]) == "--shock-mag" && i + 1 < argc) {
      shock_magnitude = std::stod(argv[++i]);
    } else if (std::string(argv[i]) == "--data-file" && i + 1 < argc) {
      data_file = argv[++i];
    }
  }
  
  // Ensure minimum throttle to prevent firehose (max 50 msg/sec)
  if (throttle_ms < 20) {
    std::cout << "⚠️  Throttle too low, enforcing minimum 20ms (50 msg/sec max)\n";
    throttle_ms = 20;
  }
  
  std::cout << "🚀 Mock Producer Configuration:\n";
  std::cout << "   📁 Data file: " << data_file << "\n";
  std::cout << "   ⏱️  Throttle: " << throttle_ms << "ms (" << (1000.0/throttle_ms) << " msg/sec max)\n";
  std::cout << "   📈 Price variation: " << (price_variation * 100) << "%\n";
  std::cout << "   💥 Shock probability: " << (shock_probability * 100) << "%\n";
  std::cout << "   🔥 Shock magnitude: " << (shock_magnitude * 100) << "%\n";

  SymbolIdMap complete_map = load_symbol_map(symbol_file);
  
  // Load all data into memory first
  std::vector<std::string> data_lines;
  std::ifstream infile(data_file);
  if (!infile) {
    std::cerr << "❌ Failed to open: " << data_file << "\n";
    return 1;
  }
  
  std::string line;
  while (std::getline(infile, line)) {
    std::string json_str = extract_json_from_line(line);
    if (!json_str.empty()) {
      data_lines.push_back(json_str);
    }
  }
  infile.close();
  
  std::cout << "📊 Loaded " << data_lines.size() << " data lines\n";
  if (data_lines.empty()) {
    std::cerr << "❌ No valid data found in file\n";
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
  
  // Setup random number generation
  std::random_device rd;
  std::mt19937 gen(rd());
  std::uniform_real_distribution<> variation_dist(-price_variation, price_variation);
  std::uniform_real_distribution<> shock_dist(-shock_magnitude, shock_magnitude);
  std::uniform_real_distribution<> shock_prob_dist(0.0, 1.0);

  size_t current_index = 0;
  int total_sent = 0;
  int loop_count = 0;
  
  // Base timestamp - we'll increment this to simulate time progression
  uint64_t base_timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(
      std::chrono::system_clock::now().time_since_epoch()).count();
  
  std::cout << "🔄 Starting infinite data loop with timestamp progression...\n";
  
  while (true) {
    const std::string &json_str = data_lines[current_index];
    
    try {
      if (parse_book_ticker(parser, json_str, ticker, true, &filtered_map)) {
        // Calculate progressive timestamp
        uint64_t time_offset = (total_sent * throttle_ms); // ms since start
        uint64_t new_timestamp = base_timestamp + time_offset;
        
        // Update timestamps to show progression
        ticker.trade_time = new_timestamp;
        ticker.event_time_ms_midnight = new_timestamp;
        
        // Apply normal price variations
        double bid_variation = 1.0 + variation_dist(gen);
        double ask_variation = 1.0 + variation_dist(gen);
        
        // Check for price shock
        if (shock_prob_dist(gen) < shock_probability) {
          double shock = 1.0 + shock_dist(gen);
          bid_variation *= shock;
          ask_variation *= shock;
          if (total_sent % 10 == 0) { // Only log some shocks to avoid spam
            std::cout << "💥 Price shock applied: " << ((shock - 1.0) * 100) << "% for symbol " << ticker.id << "\n";
          }
        }
        
        ticker.bid_price *= bid_variation;
        ticker.ask_price *= ask_variation;
        
        // Ensure ask > bid
        if (ticker.ask_price <= ticker.bid_price) {
          ticker.ask_price = ticker.bid_price * (1.0 + std::abs(price_variation));
        }
        
        ticker.my_receive_time_ns =
            std::chrono::duration_cast<std::chrono::nanoseconds>(
                std::chrono::system_clock::now().time_since_epoch())
                .count();

        zmq::message_t zmq_msg(sizeof(BookTicker));
        std::memcpy(zmq_msg.data(), &ticker, sizeof(BookTicker));
        socket.send(zmq_msg, zmq::send_flags::none);

        total_sent++;
        if (total_sent % 100 == 0) {
          std::cout << "📤 Sent " << total_sent << " messages (loop " << (loop_count + 1) 
                    << ", index " << current_index << ", timestamp " << new_timestamp << ")\n";
        }
      }
    } catch (const std::exception &e) {
      std::cerr << "❌ Exception at index " << current_index << ": " << e.what() << "\n";
    }

    // Move to next line, loop back to beginning when done
    current_index = (current_index + 1) % data_lines.size();
    if (current_index == 0) {
      loop_count++;
      std::cout << "🔁 Completed loop " << loop_count << ", restarting with progressing timestamps\n";
    }
    
    std::this_thread::sleep_for(std::chrono::milliseconds(throttle_ms));
  }
  return 0;
}
