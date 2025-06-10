#include <zmq.hpp>
#include <chrono>
#include <thread>
#include <iostream>
#include <cstring>

#pragma pack(push, 1)
struct BookTicker {
    double bid_price;
    double bid_qty;
    double ask_price;
    double ask_qty;
    int64_t update_id;
    int64_t trade_time;
    int32_t event_time_ms_midnight;
    int32_t id;
    int64_t my_receive_time_ns;
};
#pragma pack(pop)

int main() {
    zmq::context_t context(1);
    zmq::socket_t socket(context, zmq::socket_type::push);

    // Connect to consumer
    socket.connect("tcp://consumer:5555");

    std::cout << "🧪 Fake producer started.\n";

    BookTicker msg = {};
    msg.bid_price = 100.0;
    msg.ask_price = 101.0;
    msg.bid_qty = 5.0;
    msg.ask_qty = 6.0;
    msg.update_id = 42;
    msg.trade_time = 123456789;
    msg.event_time_ms_midnight = 999;
    msg.my_receive_time_ns = 0;

    int counter = 0;
    while (true) {
        msg.id = counter++;
        msg.my_receive_time_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count();

        zmq::message_t zmq_msg(sizeof(BookTicker));
        std::memcpy(zmq_msg.data(), &msg, sizeof(BookTicker));

        std::cout << "📤 Sending BookTicker id=" << msg.id << std::endl;
        socket.send(zmq_msg, zmq::send_flags::none);

        std::this_thread::sleep_for(std::chrono::seconds(5));
    }
}

