#pragma once

#include <cassert>
#include <cstdint>
#include <type_traits>

/**
 * @struct BookTicker
 * @brief Represents a single level of the order book (best bid/ask) for a
 * Binance Perpetual trading symbol.
 *
 * This struct is used to capture the Binance `bookTicker` stream data
 * specifically for perpetual contracts. It includes bid/ask prices and
 * quantities, update ID, event and trade timestamps, and an internal symbol ID.
 *
 * Note: Binance Spot `bookTicker` messages do not include all of these fields
 * (e.g., `trade_time` and `update_id` may be missing).
 *
 * The struct is aligned to 64 bytes for cache-line optimization and sized
 * exactly 64 bytes.
 */

struct alignas(64) BookTicker {
  /// Best bid price ("b")
  double bid_price;

  /// Best bid quantity ("B")
  double bid_qty;

  /// Best ask price ("a")
  double ask_price;

  /// Best ask quantity ("A")
  double ask_qty;

  /// Binance update ID ("u")
  int64_t update_id;

  /// Trade time as reported by Binance ("T")
  int64_t trade_time;

  /// Event time as milliseconds from midnight (local representation)
  /// reported by Binance ("E") converted to ms from midnight
  int32_t event_time_ms_midnight;

  /// Internal integer symbol ID (e.g., 0 = BTCUSDT)
  int32_t id;

  /// Receive time in nanoseconds from epoch
  int64_t my_receive_time_ns;
};

static_assert(sizeof(BookTicker) == 64, "BookTicker must be 64 bytes");
static_assert(std::is_trivially_copyable<BookTicker>::value,
              "BookTicker must be trivially copyable");
