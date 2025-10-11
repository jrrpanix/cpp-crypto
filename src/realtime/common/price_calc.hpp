#include <cmath>
#include <limits>

struct Prices {
  double mid_price;
  double micro_price;
  double wgt_price;
};

/**
 * @brief Compute mid-price, micro-price, and weighted price from order book
 * snapshot.
 *
 * @param bid_price Best bid price
 * @param ask_price Best ask price
 * @param bid_qty   Best bid quantity
 * @param ask_qty   Best ask quantity
 * @return Prices struct with computed values
 */
inline Prices compute_prices(double bid_price, double ask_price, double bid_qty,
                             double ask_qty) {
  Prices result;

  // Basic mid price
  result.mid_price = 0.5 * (bid_price + ask_price);

  // To avoid divide-by-zero, check sum of prices
  double denom = bid_qty + ask_qty;
  if (denom > 0) {
    result.micro_price = (bid_qty * ask_price + ask_qty * bid_price) / denom;
    result.wgt_price = (bid_qty * bid_price + ask_qty * ask_price) / denom;
  } else {
    result.micro_price = std::numeric_limits<double>::quiet_NaN();
    result.wgt_price = std::numeric_limits<double>::quiet_NaN();
  }

  return result;
}
