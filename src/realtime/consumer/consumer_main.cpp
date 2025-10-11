#include "binance/book_ticker/book_ticker.hpp"
#include "binance/book_ticker/symbol_id_map.hpp"
#include <cpr/cpr.h> // C++ Requests (https://github.com/libcpr/cpr)
#include <cstring>
#include <iostream>
#include <nlohmann/json.hpp>
#include <zmq.hpp>

struct Args {
  bool sendweb = false;
  std::string endpoint_url = "http://webserver:8000/status";
  std::string symbol_file = "/workspace/apps/config/binance/symbols.json";
};

Args parse_args(int argc, char **argv) {
  Args args;
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--sendweb") {
      args.sendweb = true;
    } else if (arg == "--endpoint" && i + 1 < argc) {
      args.endpoint_url = argv[++i];
    } else if (arg == "--symbol_file" && i + 1 < argc) {
      args.symbol_file = argv[++i];
    }
    else {
      std::cerr << "❌ Unknown or malformed argument: " << arg << "\n";
      std::cerr << "✅ Usage: " << argv[0]
                << " [--sendweb] [--endpoint http://host:port/status] [--symbol_file /workspace/apps/config/binance/symbol_file.json]\n";
      exit(1);
    }
  }
  return args;
}

void push_to_web_server(const BookTicker &msg,
                        const std::string &endpoint_url) {
  nlohmann::json j = {{"id", msg.id},
                      {"bid_price", msg.bid_price},
                      {"ask_price", msg.ask_price},
                      {"timestamp_ns", msg.my_receive_time_ns},
                      {"consumer_id", "c1"}};

  auto response = cpr::Post(cpr::Url{endpoint_url},
                            cpr::Header{{"Content-Type", "application/json"}},
                            cpr::Body{j.dump()});

  if (response.status_code != 200) {
    std::cerr << "❌ Failed to push stats: " << response.status_code << "\n";
  }
}

void run_consumer(Args args) {
  zmq::context_t context(1);
  zmq::socket_t socket(context, zmq::socket_type::sub); // 🔁 CHANGE: PULL → SUB

  socket.connect("tcp://producer:5555"); // 🔁 CHANGE: bind → connect

  // 🔁 NEW: Subscribe to all messages ("" = no topic filter)
  socket.set(zmq::sockopt::subscribe, "");

  std::cout << "🟢 Consumer ready. Subscribed to tcp://producer:5555\n";
  ReverseSymbolIdMap rmap = make_reverse_symbol_map(args.symbol_file);
  while (true) {
    zmq::message_t zmq_msg;
    auto result = socket.recv(zmq_msg, zmq::recv_flags::none);

    if (result && *result == sizeof(BookTicker)) {
      BookTicker msg;
      memcpy(&msg, zmq_msg.data(), sizeof(BookTicker));
      auto symbol = rmap[msg.id];
      std::cout << "Symbol: " << symbol << "Symbol ID: " << msg.id << " | Bid: " << msg.bid_price
                << " | Ask: " << msg.ask_price
                << " | ts_recv: " << msg.my_receive_time_ns << std::endl;
      if (args.sendweb) {
        push_to_web_server(msg, args.endpoint_url);
      }
    } else {
      std::cerr << "⚠️ Invalid message size: " << zmq_msg.size()
                << std::endl;
    }
  }
}

int main(int argc, char **argv) {
  Args args = parse_args(argc, argv);
  run_consumer(args);
}
