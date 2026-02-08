#pragma once

#include "bar_aggregator.hpp"
#include <chrono>

inline BarAggregator::BarAggregator(int64_t bar_interval_ms)
    : interval_ms(bar_interval_ms) {
  int64_t now = now_ms();
  current_window_start_ms = get_window_start_ms(now);
  current_window_stop_ms = current_window_start_ms + interval_ms;
}

inline bool BarAggregator::update(int32_t id, double price,
                                  int64_t timestamp_ms) {
  bool rollover_occurred = false;

  if (timestamp_ms >= current_window_stop_ms) {
    completed_bars = std::move(bars_by_id);
    bars_by_id.clear();

    int64_t new_start = get_window_start_ms(timestamp_ms);
    current_window_start_ms = new_start;
    current_window_stop_ms = new_start + interval_ms;

    rollover_occurred = true;
  }

  auto &bar = bars_by_id[id];
  bar.update(price, timestamp_ms);
  bar.start_time_ms = current_window_start_ms;
  bar.end_time_ms = current_window_stop_ms;

  return rollover_occurred;
}

inline const BarAggregator::BarMap &
BarAggregator::consume_completed_bars() const {
  return completed_bars;
}

inline void BarAggregator::clear_completed() { completed_bars.clear(); }

inline bool BarAggregator::has_completed_bars() const {
  return !completed_bars.empty();
}

inline int64_t BarAggregator::now_ms() const {
  using namespace std::chrono;
  return duration_cast<milliseconds>(system_clock::now().time_since_epoch())
      .count();
}

inline int64_t BarAggregator::get_window_start_ms(int64_t timestamp_ms) const {
  return (timestamp_ms / interval_ms) * interval_ms;
}
