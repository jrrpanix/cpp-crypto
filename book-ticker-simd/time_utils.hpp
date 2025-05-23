#pragma once

#include <chrono>
#include <cstdint>

inline int32_t get_time_since_midnight_us() {
    using namespace std::chrono;

    auto now = high_resolution_clock::now();
    auto since_epoch = now.time_since_epoch();
    auto midnight = duration_cast<microseconds>(since_epoch % hours(24));
    return static_cast<int32_t>(midnight.count());
}
