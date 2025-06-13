// =========================
// C++ Consumer Push Example
// =========================

#include <iostream>
#include <nlohmann/json.hpp>
#include <cpr/cpr.h>  // C++ Requests (https://github.com/libcpr/cpr)

// Assume BookTicker is defined as:
struct BookTicker {
    int id;
    double bid_price;
    double ask_price;
    int64_t my_receive_time_ns;
};

void push_to_web_server(const BookTicker &msg) {
    nlohmann::json j = {
        {"id", msg.id},
        {"bid_price", msg.bid_price},
        {"ask_price", msg.ask_price},
        {"timestamp_ns", msg.my_receive_time_ns}
    };

    auto response = cpr::Post(
        cpr::Url{"http://web:80/update_stats"},
        cpr::Header{{"Content-Type", "application/json"}},
        cpr::Body{j.dump()});

    if (response.status_code != 200) {
        std::cerr << "❌ Failed to push stats: " << response.status_code << "\n";
    }
}

// Call this in your consumer loop:
// push_to_web_server(msg);

