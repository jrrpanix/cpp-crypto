#pragma once

#include <string>
#include <unordered_map>
#include <nlohmann/json.hpp>

/**
 * @brief Represents a WebSocket stream configuration for a market type (e.g., spot or fut).
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
inline void from_json(const nlohmann::json& j, StreamConfig& config) {
    j.at("endpoint").get_to(config.endpoint);
    j.at("subs").get_to(config.subs);
}

/// A mapping from "spot" / "fut" → StreamConfig
using StreamConfigMap = std::unordered_map<std::string, StreamConfig>;

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
inline bool parse_stream_config(std::istream& is, StreamConfigMap& config_map) {
    try {
        nlohmann::json j;
        is >> j;

        for (auto& [key, val] : j.items()) {
            config_map[key] = val.get<StreamConfig>();
        }
        return true;
    } catch (const std::exception& e) {
        std::cerr << "❌ Failed to parse stream config: " << e.what() << "\n";
        return false;
    }
}

/**
 * @brief Opens a JSON config file and parses it into a StreamConfigMap.
 *
 * This function wraps file I/O and JSON parsing logic. It opens the given file,
 * reads the content, and populates the StreamConfigMap using parse_stream_config().
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
inline bool load_stream_config_file(const std::string& file_name, StreamConfigMap& config_map) {
    std::ifstream file(file_name);
    if (!file.is_open()) {
        std::cerr << "❌ Could not open config file: " << file_name << "\n";
        return false;
    }

    return parse_stream_config(file, config_map);
}

