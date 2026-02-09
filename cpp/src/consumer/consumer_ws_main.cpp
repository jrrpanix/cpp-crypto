#include "binance/book_ticker/book_ticker.hpp"
#include "binance/book_ticker/symbol_id_map.hpp"
#include <cstring>
#include <iostream>
#include <nlohmann/json.hpp>
#include <zmq.hpp>
#include <ixwebsocket/IXNetSystem.h>
#include <ixwebsocket/IXWebSocket.h>
#include <ixwebsocket/IXWebSocketServer.h>
#include <thread>
#include <atomic>
#include <set>
#include <mutex>

struct Args {
  bool websocket = false;
  int ws_port = 9001;
  std::string symbol_file = "/workspace/cpp/apps/config/binance/symbols.json";
  int throttle_ms = 0;  // Throttle in milliseconds (0 = no throttle)
  int max_rate = 0;     // Maximum messages per second (0 = unlimited)
};

Args parse_args(int argc, char **argv) {
  Args args;
  for (int i = 1; i < argc; ++i) {
    std::string arg = argv[i];
    if (arg == "--websocket") {
      args.websocket = true;
    } else if (arg == "--port" && i + 1 < argc) {
      args.ws_port = std::stoi(argv[++i]);
    } else if (arg == "--symbols" && i + 1 < argc) {
      args.symbol_file = argv[++i];
    } else if (arg == "--throttle" && i + 1 < argc) {
      args.throttle_ms = std::stoi(argv[++i]);
    } else if (arg == "--max-rate" && i + 1 < argc) {
      args.max_rate = std::stoi(argv[++i]);
    }
  }
  return args;
}

class WebSocketBroadcaster {
private:
  ix::WebSocketServer server;
  std::set<std::shared_ptr<ix::WebSocket>> connections;
  mutable std::mutex connectionsMutex;
  std::atomic<bool> running{false};
  
public:
  WebSocketBroadcaster(int port) : server(port, "0.0.0.0") {
    setupServer();
  }
  
  void setupServer() {
    server.setOnClientMessageCallback([this](std::shared_ptr<ix::ConnectionState> connectionState,
                                            ix::WebSocket& webSocket,
                                            const ix::WebSocketMessagePtr& msg) {
      if (msg->type == ix::WebSocketMessageType::Open) {
        std::lock_guard<std::mutex> lock(connectionsMutex);
        auto wsPtr = std::shared_ptr<ix::WebSocket>(&webSocket, [](ix::WebSocket*){});
        connections.insert(wsPtr);
        std::cout << "🔗 WebSocket client connected. Total: " << connections.size() << std::endl;
        
        // Send welcome message
        nlohmann::json welcome = {
          {"type", "welcome"},
          {"message", "Connected to crypto consumer WebSocket"},
          {"timestamp", std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count()}
        };
        webSocket.send(welcome.dump());
        
      } else if (msg->type == ix::WebSocketMessageType::Close) {
        std::lock_guard<std::mutex> lock(connectionsMutex);
        auto wsPtr = std::shared_ptr<ix::WebSocket>(&webSocket, [](ix::WebSocket*){});
        connections.erase(wsPtr);
        std::cout << "❌ WebSocket client disconnected. Total: " << connections.size() << std::endl;
        
      } else if (msg->type == ix::WebSocketMessageType::Error) {
        std::cout << "⚠️ WebSocket error: " << msg->errorInfo.reason << std::endl;
      }
    });
  }
  
  void start() {
    running = true;
    auto result = server.listen();
    if (!result.first) {
      std::cerr << "❌ Failed to start WebSocket server: " << result.second << std::endl;
      return;
    }
    
    std::cout << "🚀 WebSocket server started on port " << server.getPort() << std::endl;
    server.start();
  }
  
  void stop() {
    running = false;
    server.stop();
  }
  
  void broadcast(const nlohmann::json& data) {
    std::lock_guard<std::mutex> lock(connectionsMutex);
    if (connections.empty()) return;
    
    std::string message = data.dump();
    auto it = connections.begin();
    while (it != connections.end()) {
      auto ws = *it;
      if (ws) {
        auto result = ws->send(message);
        if (result.success) {
          ++it;
        } else {
          std::cout << "⚠️ Failed to send to client, removing connection" << std::endl;
          it = connections.erase(it);
        }
      } else {
        it = connections.erase(it);
      }
    }
  }
  
  size_t getConnectionCount() const {
    std::lock_guard<std::mutex> lock(connectionsMutex);
    return connections.size();
  }
  
  bool isRunning() const {
    return running;
  }
};

// Convert BookTicker to JSON
nlohmann::json bookTickerToJson(const BookTicker& ticker, const std::string& symbol) {
  return nlohmann::json{
    {"e", "bookTicker"},
    {"s", symbol},
    {"id", ticker.id},
    {"b", std::to_string(ticker.bid_price)},
    {"a", std::to_string(ticker.ask_price)},
    {"B", std::to_string(ticker.bid_qty)},
    {"A", std::to_string(ticker.ask_qty)},
    {"T", ticker.trade_time},
    {"E", ticker.event_time_ms_midnight},
    {"u", ticker.update_id}
  };
}

int main(int argc, char **argv) {
  Args args = parse_args(argc, argv);
  
  if (!args.websocket) {
    std::cerr << "❌ Use --websocket flag to enable WebSocket server mode\n";
    std::cerr << "Usage: " << argv[0] << " --websocket [--port 9001] [--symbols path] [--throttle ms] [--max-rate rate]\n";
    std::cerr << "  --throttle ms   : Throttle between messages (milliseconds)\n";
    std::cerr << "  --max-rate rate : Maximum messages per second\n";
    return 1;
  }

  // Initialize networking
  ix::initNetSystem();
  
  // Load symbol map
  SymbolIdMap symbol_map = load_symbol_map(args.symbol_file);
  std::cout << "📊 Loaded " << symbol_map.size() << " symbols\n";

  // Create WebSocket server
  std::unique_ptr<WebSocketBroadcaster> broadcaster;
  
  try {
    broadcaster = std::make_unique<WebSocketBroadcaster>(args.ws_port);
    
    // Start WebSocket server in background thread
    std::thread wsThread([&broadcaster]() {
      broadcaster->start();
    });
    
    // Give server time to start
    std::this_thread::sleep_for(std::chrono::milliseconds(500));
    
    if (!broadcaster->isRunning()) {
      std::cerr << "❌ Failed to start WebSocket server" << std::endl;
      return 1;
    }

    // Setup ZMQ consumer
    zmq::context_t context(1);
    zmq::socket_t socket(context, zmq::socket_type::sub);
    socket.connect("tcp://producer:5555");
    socket.set(zmq::sockopt::subscribe, ""); // Subscribe to all messages
    
    std::cout << "🔗 Connected to ZMQ producer tcp://producer:5555" << std::endl;
    std::cout << "🚀 WebSocket server ready on port " << args.ws_port << std::endl;
    std::cout << "📡 Broadcasting BookTicker data to connected clients..." << std::endl;

    // Throttling variables
    auto last_send_time = std::chrono::steady_clock::now();
    auto rate_window_start = std::chrono::steady_clock::now();
    int messages_in_window = 0;

    // Main consumer loop
    int message_count = 0;
    while (true) {
      zmq::message_t zmq_msg;
      auto recv_result = socket.recv(zmq_msg, zmq::recv_flags::none);
      
      if (!recv_result) continue;

      if (zmq_msg.size() == sizeof(BookTicker)) {
        BookTicker ticker;
        std::memcpy(&ticker, zmq_msg.data(), sizeof(BookTicker));
        
        // Find symbol name
        auto symbol_it = std::find_if(symbol_map.begin(), symbol_map.end(),
          [&ticker](const auto& pair) { return pair.second == ticker.id; });
        
        if (symbol_it != symbol_map.end()) {
          std::string symbol = symbol_it->first;
          
          // Convert to uppercase for consistency
          std::transform(symbol.begin(), symbol.end(), symbol.begin(), ::toupper);
          
          std::cout << "📤 " << symbol << " | ID: " << ticker.id 
                    << " | Bid: " << ticker.bid_price 
                    << " | Ask: " << ticker.ask_price << std::endl;
          
          // Rate limiting check
          auto now = std::chrono::steady_clock::now();
          bool should_send = true;
          
          if (args.max_rate > 0) {
            // Check if we're in a new second window
            auto time_since_window_start = std::chrono::duration_cast<std::chrono::seconds>(now - rate_window_start).count();
            if (time_since_window_start >= 1) {
              // Reset for new window
              rate_window_start = now;
              messages_in_window = 0;
            }
            
            // Check if we've exceeded the rate limit
            if (messages_in_window >= args.max_rate) {
              should_send = false;
            }
          }
          
          if (args.throttle_ms > 0) {
            // Check throttle timing
            auto time_since_last = std::chrono::duration_cast<std::chrono::milliseconds>(now - last_send_time).count();
            if (time_since_last < args.throttle_ms) {
              should_send = false;
            }
          }
          
          if (should_send) {
            // Broadcast to WebSocket clients
            nlohmann::json json_data = bookTickerToJson(ticker, symbol);
            broadcaster->broadcast(json_data);
            
            last_send_time = now;
            messages_in_window++;
            message_count++;
            
            // Log statistics every 50 messages
            if (message_count % 50 == 0) {
              std::cout << "📊 Sent " << message_count << " messages to " 
                        << broadcaster->getConnectionCount() << " WebSocket clients" << std::endl;
            }
          }
        }
      }
    }
    
    // Cleanup
    if (wsThread.joinable()) {
      wsThread.join();
    }
    
  } catch (const std::exception& e) {
    std::cerr << "❌ Error: " << e.what() << std::endl;
    return 1;
  }

  ix::uninitNetSystem();
  return 0;
}