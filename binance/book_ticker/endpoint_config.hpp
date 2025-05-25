#pragma once

#include <fstream>
#include <iostream>
#include <map>
#include <nlohmann/json.hpp>
#include <string>
#include <vector>

struct EndpointConfig {
  std::string endpoint;
  std::vector<std::string> subs;
};

// using json = nlohmann::json
using EndpointConfigMap = std::map<std::string, EndpointConfig>;

/**
 * @brief Deserializes a JSON object into an EndpointConfig struct.
 *
 * This function is used by nlohmann::json to automatically convert a JSON
 * object into a user-defined C++ struct (`EndpointConfig`). It extracts the
 * "endpoint" string and the "subs" array of strings and assigns them to the
 * corresponding fields.
 *
 * This function is typically invoked internally when calling:
 * @code
 * EndpointConfig cfg = j.get<EndpointConfig>();
 * @endcode
 *
 * @param j       The JSON object to deserialize. It must contain:
 *                - "endpoint": a string representing the WebSocket URL
 *                - "subs": an array of strings representing subscribed symbols
 * @param config  The EndpointConfig instance that will be populated.
 *
 * @example
 * Example input JSON:
 * @code{.json}
 * {
 *     "endpoint": "wss://fstream.binance.com/ws",
 *     "subs": [
 *         "btcusdt", "ethusdt", "adausdt"
 *     ]
 * }
 * @endcode
 *
 * @throws std::out_of_range or nlohmann::json::type_error if required fields
 * are missing or have incorrect types.
 */
inline void from_json(const nlohmann::json &j, EndpointConfig &config) {
  j.at("endpoint").get_to(config.endpoint);
  j.at("subs").get_to(config.subs);
}

/**
 * @brief Parses a JSON configuration from an input stream and populates a
 * config map.
 *
 * This function reads a JSON object from the given input stream and extracts
 * named configuration entries (e.g., "spot", "fut"). Each entry is converted
 * into an EndpointConfig struct and stored in the provided config_map.
 *
 * @param is          Input stream containing JSON configuration (e.g., a file
 * or stringstream).
 * @param config_map  Output map where each key is a section name (e.g., "spot")
 * and the value is an EndpointConfig struct with endpoint and subscription
 * info.
 *
 * @return true if parsing was successful; false if an error occurred.
 *
 * @note The input must be a valid JSON object where each top-level key maps to
 * an object with the fields:
 *         - "endpoint" (string): the WebSocket endpoint URL
 *         - "subs" (array of strings): a list of subscription symbols
 *
 * @example
 * The JSON should follow this format:
 * @code{.json}
 * {
 *     "spot": {
 *         "endpoint": "wss://stream.binance.com:9443/ws",
 *         "subs": [
 *             "btcusdt", "ethusdt", "adausdt"
 *         ]
 *     },
 *     "fut": {
 *         "endpoint": "wss://fstream.binance.com/ws",
 *         "subs": [
 *             "btcusdt", "ethusdt", "adausdt"
 *         ]
 *     }
 * }
 * @endcode
 */

inline bool parse_config(std::istream &is, EndpointConfigMap &config_map) {
  try {
    nlohmann::json j;
    is >> j;
    std::cout << j << std::endl;
    for (auto &[key, val] : j.items()) {
      config_map[key] = val.get<EndpointConfig>();
    }

    return true;
  } catch (const std::exception &e) {
    std::cerr << "❌ Failed to parse config: " << e.what() << "\n";
    return false;
  }
}

/**
 * @brief Opens and parses a JSON configuration file into an EndpointConfigMap.
 *
 * This function attempts to open a configuration file from the given path,
 * and if successful, parses its JSON content into a map of named EndpointConfig
 * entries. It also prints out each parsed configuration section and its
 * associated symbols to standard output for verification.
 *
 * @param file_name   Path to the JSON configuration file (null-terminated C
 * string).
 * @param config_map  Output map that will be populated with named
 * EndpointConfig entries.
 *
 * @return true if the file was opened and parsed successfully; false otherwise.
 *
 * @note This function delegates the actual JSON parsing to `parse_config()`.
 *       It expects the file to contain a top-level JSON object like:
 * @code{.json}
 * {
 *     "spot": {
 *         "endpoint": "wss://stream.binance.com:9443/ws",
 *         "subs": ["btcusdt", "ethusdt", "adausdt"]
 *     },
 *     "fut": {
 *         "endpoint": "wss://fstream.binance.com/ws",
 *         "subs": ["btcusdt", "ethusdt", "adausdt"]
 *     }
 * }
 * @endcode
 *
 * @see parse_config
 */
inline bool parse_config_file(const char *file_name,
                              EndpointConfigMap &config_map) {
  std::ifstream file(file_name);
  if (!file.is_open()) {
    std::cerr << "Cannot open " << file_name << "\n";
    return false;
  }

  if (parse_config(file, config_map)) {
    for (const auto &[name, conf] : config_map) {
      std::cout << "[" << name << "] endpoint = " << conf.endpoint << "\n";
      for (const auto &sym : conf.subs) {
        std::cout << "  - " << sym << "\n";
      }
    }
  }
  return true;
}
