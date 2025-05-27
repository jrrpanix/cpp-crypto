#pragma once

#include <fstream>
#include <nlohmann/json.hpp>
#include <string>
#include <unordered_map>

/**
 * @brief Represents a WebSocket stream configuration for a market type (e.g.,
 * spot or fut).
 */
struct StreamConfig {
  /// WebSocket endpoint URL
  std::string endpoint;

  /// Symbol-to-ID subscription map
  std::unordered_map<std::string, int> subs;
};

/**
 * @brief JSON deserialization function for StreamConfig using nlohmann::json.
 *
 * @param j The input JSON object.
 * @param config The target StreamConfig to populate.
 *
 * Example input JSON:
 * {
 *   "endpoint": "wss://stream.binance.com:9443/ws",
 *   "subs": {
 *     "btcusdt": 1,
 *     "ethusdt": 2
 *   }
 * }
 */
inline void from_json(const nlohmann::json &j, StreamConfig &config) {
  j.at("endpoint").get_to(config.endpoint);
  j.at("subs").get_to(config.subs);
}

/// JSON serialization for StreamConfig
inline void to_json(nlohmann::json &j, const StreamConfig &config) {
  j = nlohmann::json{{"endpoint", config.endpoint}, {"subs", config.subs}};
}

/// A mapping from "spot" / "fut" → StreamConfig
using StreamConfigMap = std::unordered_map<std::string, StreamConfig>;

inline void to_json(nlohmann::json &j, const StreamConfigMap &config_map) {
  j = nlohmann::json::object();
  for (const auto &[key, val] : config_map) {
    j[key] = val; // relies on to_json(StreamConfig) above
  }
}

/**
 * @brief Parses a JSON input stream into a StreamConfigMap.
 *
 * @param is Input stream to read JSON from (e.g., std::ifstream).
 * @param config_map Output map to populate with key → StreamConfig entries.
 * @return true if parsing was successful, false on failure.
 *
 * Example JSON structure:
 * {
 *   "spot": { "endpoint": "...", "subs": { "btcusdt": 123, ... }},
 *   "fut":  { "endpoint": "...", "subs": { "ethusdt": 456, ... }}
 * }
 */
inline bool parse_stream_config(std::istream &is, StreamConfigMap &config_map) {
  try {
    nlohmann::json j;
    is >> j;

    for (auto &[key, val] : j.items()) {
      config_map[key] = val.get<StreamConfig>();
    }
    return true;
  } catch (const std::exception &e) {
    std::cerr << "❌ Failed to parse stream config: " << e.what() << "\n";
    return false;
  }
}

/**
 * @brief Opens a JSON config file and parses it into a StreamConfigMap.
 *
 * This function wraps file I/O and JSON parsing logic. It opens the given file,
 * reads the content, and populates the StreamConfigMap using
 * parse_stream_config().
 *
 * @param file_name Path to the JSON configuration file.
 * @param config_map Output map to populate with key → StreamConfig entries.
 * @return true if the file was successfully opened and parsed, false otherwise.
 *
 * Example usage:
 * @code
 *   StreamConfigMap config_map;
 *   if (!load_stream_config_file("config.json", config_map)) {
 *       std::cerr << "Failed to load config file\n";
 *   }
 * @endcode
 */
inline bool load_stream_config_file(const std::string &file_name,
                                    StreamConfigMap &config_map) {
  std::ifstream file(file_name);
  if (!file.is_open()) {
    std::cerr << "❌ Could not open config file: " << file_name << "\n";
    return false;
  }

  return parse_stream_config(file, config_map);
}

/**
 * @brief Serializes a StreamConfigMap to JSON and writes it to an output
 * stream.
 *
 * This function converts a map of StreamConfig objects into JSON and writes it
 * to the given output stream (e.g., a file or stdout).
 *
 * @param os Output stream to write to (e.g., std::ofstream or std::cout)
 * @param config_map Map of stream keys (e.g., "spot", "fut") to StreamConfig
 *
 * Example output JSON:
 * {
 *   "spot": {
 *     "endpoint": "wss://stream.binance.com:9443/ws",
 *     "subs": {
 *       "btcusdt": 290,
 *       "ethusdt": 476
 *     }
 *   }
 * }
 */
inline void write_stream_config(std::ostream &os,
                                const StreamConfigMap &config_map) {
  nlohmann::json j = config_map;
  os << std::setw(2) << j << std::endl;
}
