#pragma once

#include "robin_hood.h"
#include <algorithm> // std::ranges::transform
#include <cctype>    // std::toupperg
#include <nlohmann/json.hpp>
#include <string>

/// Alias for a fast flat hash map from symbol name to integer ID
using SymbolIdMap = robin_hood::unordered_flat_map<std::string, int>;

/**
 * @brief Convert a JSON object of string→int into a SymbolIdMap with uppercase
 * keys.
 */

inline std::string to_upper(const std::string &s) {
  std::string result;
  result.resize(s.size());

  std::ranges::transform(s, result.begin(),
                         [](unsigned char c) { return std::toupper(c); });

  return result;
}

/**
 * @brief Convert a JSON object of string → int into a SymbolIdMap with
 * UPPERCASE keys.
 *
 * Expected input JSON format:
 * {
 *   "btcusdt": 0,
 *   "ethusdt": 1
 * }
 *
 * @param j nlohmann::json object
 * @return SymbolIdMap with uppercase keys
 */
inline SymbolIdMap json_to_upper_flat_map(const nlohmann::json &j) {
  SymbolIdMap result;

  for (auto it = j.begin(); it != j.end(); ++it) {
    std::string upper_key = to_upper(it.key());
    result[upper_key] = it.value().get<int>();
  }

  return result;
}
