#pragma once

#include <cassert>
#include <cstdint>

struct alignas(64) BookTicker {
  double bid_price; // "b"
  double bid_qty;   // "B"
  double ask_price; // "a"
  double ask_qty;   // "A"

  int64_t update_id;  // "u"
  int64_t trade_time; // "T"
  int64_t event_time; // "E"

  int32_t id;      // internal symbol ID (e.g. 0 = BTCUSDT)
  int32_t my_receive_time_us;  // compressed receive time us from midnight
};



static_assert(sizeof(BookTicker) == 64, "BookTicker must be 64 bytes");
