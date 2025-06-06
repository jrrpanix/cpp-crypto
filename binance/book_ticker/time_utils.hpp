#pragma once

#include <chrono>
#include <cstdint>

/**
 * @brief Get current time in nanoseconds since Unix epoch (UTC).
 * @return int64_t Nanoseconds since 1970-01-01 00:00:00 UTC
 */
inline int64_t now_ns_since_epoch() {
  using namespace std::chrono;

  auto now = system_clock::now();
  return duration_cast<nanoseconds>(now.time_since_epoch()).count();
}

/**
 * @brief Convert milliseconds since epoch (UTC) to milliseconds since midnight
 * (UTC).
 *
 * @param epoch_ms Milliseconds since Unix epoch (UTC)
 * @return int32_t Milliseconds since UTC midnight
 */
inline int32_t epoch_ms_to_midnight_ms_utc(int64_t epoch_ms) {
  using namespace std::chrono;

  // Convert to system_clock::time_point
  system_clock::time_point tp =
      time_point<system_clock, milliseconds>(milliseconds{epoch_ms});

  // Compute duration since last UTC midnight
  auto day_start = floor<days>(tp); // Truncates to midnight UTC
  auto since_midnight = tp - day_start;

  // Convert to milliseconds
  return static_cast<int32_t>(
      duration_cast<milliseconds>(since_midnight).count());
}

/**
 * @brief Convert nanoseconds since Unix epoch (UTC) to nanoseconds since
 * midnight (UTC).
 *
 * This is useful for computing intra-day timestamps or latencies with respect
 * to the start of the UTC day.
 *
 * @param epoch_ns Nanoseconds since Unix epoch (UTC)
 * @return int64_t Nanoseconds since UTC midnight
 */
inline int64_t epoch_ns_to_midnight_ns_utc(int64_t epoch_ns) {
  using namespace std::chrono;

  // Convert to time_point in nanoseconds
  system_clock::time_point tp =
      time_point<system_clock, nanoseconds>(nanoseconds{epoch_ns});

  // Truncate to UTC midnight (00:00:00)
  auto day_start = floor<days>(tp);

  // Duration since midnight
  auto since_midnight = tp - day_start;

  // Convert to nanoseconds
  return duration_cast<nanoseconds>(since_midnight).count();
}
