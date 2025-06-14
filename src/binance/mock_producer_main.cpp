#include <zmq.hpp>
#include <chrono>
#include <thread>
#include <iostream>
#include <cstring>
#include "book_ticker/book_ticker.hpp"  // ✅ canonical struct

int main() {
    zmq::context_t context(1);
    zmq::socket_t socket(context, zmq::socket_type::pub);  // ✅ PUB not PUSH

    // Bind to same port as real producer
    socket.bind("tcp://0.0.0.0:5555");
    std::cerr << "🧪 Mock producer ZMQ PUB bound to tcp://0.0.0.0:5555\n";

    // Allow time for consumers to connect
    std::this_thread::sleep_for(std::chrono::seconds(1));

    BookTicker msg = {};
    msg.bid_price = 100.0;
    msg.ask_price = 101.0;
    msg.bid_qty = 5.0;
    msg.ask_qty = 6.0;
    msg.update_id = 42;
    msg.trade_time = 123456789;
    msg.event_time_ms_midnight = 999;

    int counter = 0;

    while (true) {
        msg.id = counter++;
        msg.my_receive_time_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();

        zmq::message_t zmq_msg(sizeof(BookTicker));
        std::memcpy(zmq_msg.data(), &msg, sizeof(BookTicker));

        std::cout << "📤 Sending BookTicker id=" << msg.id << std::endl;
        socket.send(zmq_msg, zmq::send_flags::none);

        std::this_thread::sleep_for(std::chrono::seconds(1));
    }
}

