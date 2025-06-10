#include "bars/bar_aggregator_impl.hpp"
#include "bars/bar_report_printer.hpp"
#include "bars/ohlc_bar.hpp"
#include "common/price_calc.hpp"
#include "setup_websocket.hpp"
#include "stream_config.hpp"
#include <atomic>
#include <chrono>
#include <csignal>
#include <iomanip> // for std::setprecision
#include <iostream>
#include <ixwebsocket/IXWebSocket.h>
#include <ranges>
#include <string>
#include <system_error>
#include <thread>
#include <unordered_map>
#include <vector>
#include <zmq.hpp>

#include "book_ticker_queue.hpp"
#include "symbol_id_map.hpp"

std::atomic<bool> running(true);

void handle_sigint(int) {
  std::cout << "\n🛑 Caught SIGINT. Exiting gracefully...\n";
  running = false;
}
/**
 * @struct Args
 * @brief Holds parsed command-line arguments for the WebSocket client.
 *
 * This struct stores:
 * - The path to the stream configuration file (`config_file`)
 * - The section key in the config to select a specific stream (`key`)
 * - The path to the symbol map file (`symbol_file`)
 * - A flag indicating whether all required arguments were successfully parsed
 * (`valid`)
 */
struct Args {
  std::string config_file;
  std::string key;
  std::string symbol_file;
  bool zmqon = false;
  bool debug = false;
  bool valid = false;
};

/**
 * @brief Parses command-line arguments for the WebSocket client.
 *
 * Expects three named arguments:
 * - `--config_file <file>`: Path to the stream configuration JSON file.
 * - `--key <key>`: Identifier within the config to select the desired stream
 * configuration.
 * - `--symbol_file <file>`: Path to the symbol-to-ID mapping JSON file.
 *
 * If any arguments are missing or malformed, the function prints usage help
 * and returns an `Args` object with `valid = false`.
 *
 * @param argc Number of arguments passed to the program.
 * @param argv Array of C-style strings representing arguments.
 * @return An `Args` struct with parsed values and a `valid` flag.
 */
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
    } else if (arg == "--zmqon") {
      args.zmqon = true;
    } else if (arg == "--debug") {
      args.debug = true;
    } else {
      std::cerr << "❌ Unknown or malformed argument: " << arg << "\n";
      std::cerr << "✅ Usage: " << argv[0]
                << " --config_file <file> --key <key> --symbol_file <file> "
                   "[--debug]\n";
      return args;
    }
  }

  // Validate arguments
  if (args.config_file.empty() || args.key.empty() ||
      args.symbol_file.empty()) {
    std::cerr << "❌ Missing required arguments.\n";
    std::cerr << "✅ Usage: " << argv[0]
              << " --config_file <file> --key <key> --symbol_file <file> "
                 "[--debug] [--zmqon]\n";
    return args;
  }
  args.valid = true;
  return args;
}

robin_hood::unordered_flat_map<int32_t, std::string>
make_reverse_map(const SymbolIdMap &symbol_to_id) {
  robin_hood::unordered_flat_map<int32_t, std::string> id_to_symbol;
  for (const auto &[symbol, id] : symbol_to_id) {
    id_to_symbol[id] = symbol;
  }
  return id_to_symbol;
}

void consume_and_monitor(BookTickerQueue &queue, std::atomic<bool> &running,
                         const SymbolIdMap &filtered_map, zmq::socket_t *zmq_socket) {
  using clock = std::chrono::steady_clock;
  using namespace std::chrono;

  struct Stats {
    int64_t count = 0;
    double bid_price_sum = 0;
    double bid_qty_sum = 0;
    double ask_price_sum = 0;
    double ask_qty_sum = 0;
    double latency_sum_ms = 0;
  };

  std::unordered_map<int32_t, Stats> stats_by_id;
  BookTicker msg;

  auto last_report = clock::now();
  auto id_to_symbol = make_reverse_map(filtered_map);
  while (running) {
    if (queue.try_dequeue(msg)) {
      auto &stats = stats_by_id[msg.id];

      if (zmq_socket) {
	static long cnt = 0;
	if (++cnt < 20) {
	  std::cerr << "sening message " << msg.id << " " << msg.bid_price << " " << msg.ask_price << std::endl;
	}
	zmq::message_t zmq_msg(sizeof(msg));
	memcpy(zmq_msg.data(), &msg, sizeof(msg));
	zmq_socket->send(zmq_msg, zmq::send_flags::none);
      }
      stats.count++;
      stats.bid_price_sum += msg.bid_price;
      stats.bid_qty_sum += msg.bid_qty;
      stats.ask_price_sum += msg.ask_price;
      stats.ask_qty_sum += msg.ask_qty;

      int64_t event_time_ns =
          static_cast<int64_t>(msg.event_time_ms_midnight) * 1'000'000;
      int64_t recv_time_ns =
          epoch_ns_to_midnight_ns_utc(msg.my_receive_time_ns);
      double latency_ms =
          static_cast<double>(recv_time_ns - event_time_ns) / 1'000'000.0;
      stats.latency_sum_ms += latency_ms;
    } else {
      std::this_thread::sleep_for(std::chrono::microseconds(100));
    }

    // Print every 30 seconds
    auto now = clock::now();
    if (duration_cast<seconds>(now - last_report).count() >= 30) {
      std::vector<std::pair<std::string, Stats>> ordered_stats;

      for (const auto &[id, stats] : stats_by_id) {
        auto it = id_to_symbol.find(id);
        std::string symbol =
            (it != id_to_symbol.end()) ? it->second : "<unknown>";
        ordered_stats.emplace_back(symbol, stats);
      }

      std::sort(ordered_stats.begin(), ordered_stats.end(),
                [](const auto &a, const auto &b) { return a.first < b.first; });

      // Print as dataframe
      std::cout << "\n📊 ---- 30-Second Summary ----\n";
      std::cout << std::left << std::setw(12) << "Symbol" << std::right
                << std::setw(10) << "Count" << std::setw(15) << "Avg Bid"
                << std::setw(15) << "Bid Qty" << std::setw(15) << "Avg Ask"
                << std::setw(15) << "Ask Qty" << std::setw(15) << "Latency (ms)"
                << "\n";

      for (const auto &[symbol, stats] : ordered_stats) {
        if (stats.count == 0)
          continue;

        double avg_bid_price = stats.bid_price_sum / stats.count;
        double avg_bid_qty = stats.bid_qty_sum / stats.count;
        double avg_ask_price = stats.ask_price_sum / stats.count;
        double avg_ask_qty = stats.ask_qty_sum / stats.count;
        double avg_latency = stats.latency_sum_ms / stats.count;

        std::cout << std::left << std::setw(12) << symbol << std::right
                  << std::setw(10) << stats.count << std::setw(15) << std::fixed
                  << std::setprecision(3) << avg_bid_price << std::setw(15)
                  << avg_bid_qty << std::setw(15) << avg_ask_price
                  << std::setw(15) << avg_ask_qty << std::setw(15)
                  << avg_latency << "\n";
      }

      std::cout << "------------------------------\n";

      stats_by_id.clear();
      last_report = now;
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
 * The WebSocket callback parses each message using a thread-local simdjson
 * parser and enqueues structured `BookTicker` messages into a lock-free
 * concurrent queue. The consumer thread dequeues these messages and prints the
 * message rate every 1000 updates.
 *
 * The application exits cleanly when interrupted via Ctrl+C.
 *
 * @param argc Command-line argument count.
 * @param argv Command-line argument vector.
 * @return 0 on successful execution, 1 on error (e.g., invalid args or config).
 *
 * @usage
 *   ./program --config_file <config_file.json> --key <section_key>
 * --symbol_file <symbol_map.json>
 *
 * @details
 * - `--config_file`: Path to the JSON config file containing stream
 * configuration.
 * - `--key`: Section key in the config file specifying which stream to
 * subscribe to.
 * - `--symbol_file`: Path to the JSON file mapping Binance symbols to integer
 * IDs. The file contains a complete reference of all Binance symbols. The
 * program uses this to construct a smaller `filtered_map` consisting only of
 * the symbols defined in the stream config.
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
  zmq::socket_t *zmq_socket = nullptr;
  if (args.zmqon) {
    std::cerr << "building zmq_socket" << std::endl;
    zmq::context_t context(1);
    zmq_socket = new zmq::socket_t(context, zmq::socket_type::push);
    zmq_socket->connect("tcp://consumer:5555");  // Docker network address
  }
  
  // Setup and start WebSocket
  const StreamConfig &stream_config = cfgmap[args.key];

  SymbolIdMap complete_map = load_symbol_map(args.symbol_file);
  SymbolIdMap filtered_map =
      filter_symbol_map(complete_map, stream_config.subs);

  BookTickerQueue queue;
  ix::WebSocket ws;
  setup_websocket(ws, stream_config, filtered_map, &queue, args.debug);
  std::thread consumer_thread(consume_and_monitor, std::ref(queue),
                              std::ref(running), filtered_map, zmq_socket);
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
