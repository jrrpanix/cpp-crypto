#pragma once
#include <cstdint>
#include <limits>

struct OHLCBar {
  double open = std::numeric_limits<double>::quiet_NaN();
  double high = std::numeric_limits<double>::lowest();
  double low = std::numeric_limits<double>::max();
  double close = std::numeric_limits<double>::quiet_NaN();
  int64_t start_time_ms = 0;
  int64_t end_time_ms = 0;
  uint64_t count = 0; // Number of ticks aggregated

  void update(double price, int64_t timestamp_ms) {
    if (count == 0) {
      open = high = low = close = price;
      start_time_ms = timestamp_ms;
    } else {
      if (price > high)
        high = price;
      if (price < low)
        low = price;
      close = price;
    }
    end_time_ms = timestamp_ms;
    ++count;
  }

  void reset() {
    open = close = std::numeric_limits<double>::quiet_NaN();
    high = std::numeric_limits<double>::lowest();
    low = std::numeric_limits<double>::max();
    count = 0;
    start_time_ms = end_time_ms = 0;
  }
};
