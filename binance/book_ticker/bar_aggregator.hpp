#pragma once

#include "ohlc_bar.hpp"
#include "robin_hood.h"
#include <cstdint>

/**
 * @brief Aggregates OHLC bars by symbol ID on synchronized time intervals.
 */
class BarAggregator {
public:
  using BarMap =
      robin_hood::unordered_flat_map<int32_t, OHLCBar>; // ✅ alias for map type

  explicit BarAggregator(int64_t bar_interval_ms = 60'000);

  /**
   * @brief Update bar data for a given ID and timestamped price.
   * @return true if a new time window started (bars ready to consume)
   */
  bool update(int32_t id, double price, int64_t timestamp_ms);

  /**
   * @brief Access the completed bars (from the previous interval).
   */
  const BarMap &consume_completed_bars() const;

  /**
   * @brief Clears the completed bars after consumption.
   */
  void clear_completed();

  /**
   * @brief Returns true if bars from the last interval are available.
   */
  bool has_completed_bars() const;

private:
  int64_t interval_ms;
  int64_t current_window_start_ms;
  int64_t current_window_stop_ms;

  BarMap bars_by_id;
  BarMap completed_bars;

  int64_t now_ms() const;
  int64_t get_window_start_ms(int64_t timestamp_ms) const;
};
