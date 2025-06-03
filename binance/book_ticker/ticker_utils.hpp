#pragma once
#include "book_ticker.hpp"

namespace ticker_utils {

inline double compute_mid_price(const BookTicker &bt) {
  return 0.5 * (bt.bid_price + bt.ask_price);
}

inline double compute_micro_price(const BookTicker &bt) {
  double denom = bt.bid_qty + bt.ask_qty;
  return (denom > 0)
             ? (bt.bid_qty * bt.ask_price + bt.ask_qty * bt.bid_price) / denom
             : std::numeric_limits<double>::quiet_NaN();
}

inline double compute_weighted_price(const BookTicker &bt) {
  double denom = bt.bid_qty + bt.ask_qty;
  return (denom > 0)
             ? (bt.bid_qty * bt.bid_price + bt.ask_qty * bt.ask_price) / denom
             : std::numeric_limits<double>::quiet_NaN();
}

} // namespace ticker_utils
