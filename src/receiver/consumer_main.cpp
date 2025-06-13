#include "binance/book_ticker/book_ticker.hpp"
#include <cstring>
#include <iostream>
#include <zmq.hpp>


int main() {
  zmq::context_t context(1);
  zmq::socket_t socket(context, zmq::socket_type::sub);  // 🔁 CHANGE: PULL → SUB

  socket.connect("tcp://producer:5555");  // 🔁 CHANGE: bind → connect

  // 🔁 NEW: Subscribe to all messages ("" = no topic filter)
  socket.set(zmq::sockopt::subscribe, "");

  std::cout << "🟢 Consumer ready. Subscribed to tcp://producer:5555\n";

  while (true) {
    zmq::message_t zmq_msg;
    auto result = socket.recv(zmq_msg, zmq::recv_flags::none);

    if (result && *result == sizeof(BookTicker)) {
      BookTicker msg;
      memcpy(&msg, zmq_msg.data(), sizeof(BookTicker));

      std::cout << "Symbol ID: " << msg.id << " | Bid: " << msg.bid_price
                << " | Ask: " << msg.ask_price
                << " | ts_recv: " << msg.my_receive_time_ns << std::endl;
    } else {
      std::cerr << "⚠️ Invalid message size: " << zmq_msg.size()
                << std::endl;
    }
  }
}

