#pragma once

#include <cassert>
#include <cstdint>
#include <type_traits>

/**
 * @struct BookTicker
 * @brief Represents the best bid/ask level from Binance `bookTicker` stream.
 *
 * This struct captures Binance order book snapshot data for both Spot and
 * Perpetual (Futures) trading symbols. The structure is cache-line aligned
 * (64 bytes) for optimal performance in high-throughput scenarios.
 *
 * **Binance Data Format Differences:**
 *
 * **Perpetual Futures (bookTicker):**
 *   - Includes all timestamp fields: "E" (event time), "T" (trade time)
 *   - Example: {"e":"bookTicker","u":123,"s":"BTCUSDT","b":"79043.04","B":"3.04",
 *              "a":"79043.05","A":"0.66","T":1769921127516,"E":1769921127517}
 *   - T (trade_time): Server-side milliseconds since epoch when order was placed
 *   - E (event_time): Server-side milliseconds since epoch when update occurred
 *
 * **Spot Trading (bookTicker):**
 *   - Minimal fields, NO timestamp data from Binance
 *   - Example: {"u":86197067407,"s":"BTCUSDT","b":"79043.04","B":"3.04",
 *              "a":"79043.05","A":"0.66"}
 *   - trade_time: Not provided; set to 0
 *   - event_time_ms_midnight: Falls back to current system time
 *
 * **Timestamp Source Summary:**
 * - Futures: Uses Binance exchange timestamps (E and T fields)
 * - Spot: Uses local system timestamps (my_receive_time_ns) due to lack of
 *         exchange timestamps in Binance Spot bookTicker stream
 * - Both: my_receive_time_ns always captures local receipt time in nanoseconds
 *
 * **Field Mapping:**
 * - "b", "B": Bid price and quantity
 * - "a", "A": Ask price and quantity
 * - "u": Update ID (unique per symbol, monotonically increasing)
 * - "T": Trade time (Futures only) - milliseconds since epoch
 * - "E": Event time (Futures only) - milliseconds since epoch
 *
 * Note: Due to 64-byte cache alignment constraint, only one event timestamp
 * can be stored. For Futures, "E" is converted to milliseconds from midnight UTC.
 * For Spot, system time at receive is used since Binance does not provide
 * exchange timestamps in the Spot bookTicker stream.
 */
struct alignas(64) BookTicker {
  /// Best bid price ("b" from Binance)
  double bid_price;

  /// Best bid quantity ("B" from Binance)
  double bid_qty;

  /// Best ask price ("a" from Binance)
  double ask_price;

  /// Best ask quantity ("A" from Binance)
  double ask_qty;

  /// Binance update ID ("u" from Binance) - unique per symbol, monotonic
  int64_t update_id;

  /// Trade time from Binance ("T" from Binance Futures only)
  /// Futures: Milliseconds since Unix epoch from Binance exchange
  /// Spot: Set to 0 (Binance Spot bookTicker does not provide this field)
  int64_t trade_time;

  /// Event time converted to milliseconds from midnight UTC
  /// Futures: Derived from Binance "E" field (exchange timestamp)
  /// Spot: Derived from local system time (Binance provides no timestamps)
  /// Note: For accurate Spot timing analysis, use my_receive_time_ns instead
  int32_t event_time_ms_midnight;

  /// Internal integer symbol ID for lookup (e.g., 0 = BTCUSDT)
  int32_t id;

  /// Receive time in nanoseconds since Unix epoch
  /// Always captured locally when message arrives (both Spot and Futures)
  /// Critical for Spot: This is the ONLY reliable timestamp for Spot data
  /// as Binance Spot bookTicker provides no exchange timestamps
  int64_t my_receive_time_ns;
};

static_assert(sizeof(BookTicker) == 64, "BookTicker must be 64 bytes");
static_assert(std::is_trivially_copyable<BookTicker>::value,
              "BookTicker must be trivially copyable");
