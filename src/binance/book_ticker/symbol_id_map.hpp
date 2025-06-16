#pragma once

#include "robin_hood.h"
#include <algorithm> // std::ranges::transform
#include <cctype>    // std::toupperg
#include <cstdint>
#include <fstream>
#include <nlohmann/json.hpp>
#include <string>

/// Alias for a fast flat hash map from symbol name to integer ID
using SymbolIdMap = robin_hood::unordered_flat_map<std::string, int32_t>;
using ReverseSymbolIdMap = robin_hood::unordered_flat_map<int32_t, std::string>;

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
    result[upper_key] = it.value().get<int32_t>();
  }

  return result;
}

/**
 * @brief Loads a JSON file containing a string-to-int32_t mapping into a
 * robin_hood unordered_flat_map.
 *
 * The JSON file should have the format:
 * {
 *     "key1": 1,
 *     "key2": 2,
 *     ...
 * }
 *
 * @param filename Path to the JSON file to load.
 * @return robin_hood::unordered_flat_map<std::string, int32_t> containing the
 * parsed key-value pairs.
 * @throws std::runtime_error if the file cannot be opened or if the JSON
 * structure is invalid.
 */
SymbolIdMap load_symbol_map(const std::string &filename) {
  std::ifstream in_file(filename);
  if (!in_file) {
    throw std::runtime_error("❌ Failed to open file: " + filename);
  }

  nlohmann::json j;
  in_file >> j;

  if (!j.is_object()) {
    throw std::runtime_error("❌ JSON root must be an object.");
  }

  SymbolIdMap symbol_map;

  for (const auto &[key, value] : j.items()) {
    if (!value.is_number_integer()) {
      throw std::runtime_error("❌ Invalid value type for key: " + key);
    }
    symbol_map[key] = value.get<int32_t>();
  }

  return symbol_map;
}

/**
 * @brief Filters a SymbolIdMap by keeping only the keys present in the provided
 * symbol list.
 *
 * @param full_map The original SymbolIdMap containing all symbol-ID pairs.
 * @param symbols_to_keep A vector of symbols (keys) to retain in the resulting
 * map.
 * @return A new SymbolIdMap containing only the entries whose keys are found in
 * symbols_to_keep.
 */
SymbolIdMap filter_symbol_map(const SymbolIdMap &full_map,
                              const std::vector<std::string> &symbols_to_keep) {

  robin_hood::unordered_flat_map<std::string, int32_t> filtered_map;
  for (const auto &symbol : symbols_to_keep) {
    auto it = full_map.find(symbol);
    if (it != full_map.end()) {
      std::string key = to_upper(it->first);
      filtered_map.emplace(key, it->second);
    }
  }
  return filtered_map;
}


ReverseSymbolIdMap make_reverse_symbol_map(const std::string &filename) {
    std::ifstream in_file(filename);
    if (!in_file) {
      throw std::runtime_error("❌ Failed to open file: " + filename);
    }

    nlohmann::json j;
    in_file >> j;

    if (!j.is_object()) {
      throw std::runtime_error("❌ JSON root must be an object.");
    }

    ReverseSymbolIdMap rsymbol_map;
    for (const auto &[symbol, value] : j.items()) {
      if (!value.is_number_integer()) {
	throw std::runtime_error("❌ Invalid value type for key: " + symbol);
      }
      int32_t ikey = value.get<int32_t>();
      rsymbol_map[ikey] = to_upper(symbol);
    }

    return rsymbol_map;
}
