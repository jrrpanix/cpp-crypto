#pragma once
#include <iostream>
#include <string>
#include <vector>
#include <nlohmann/json.hpp>

/**
 * @brief Parses a JSON configuration stream to extract the WebSocket endpoint and subscription list.
 *
 * The expected JSON format is:
 * @code{.json}
 * {
 *     "endpoint": "wss://stream.binance.com:9443/ws",
 *     "subs": ["btcusdt", "ethusdt", "adausdt"]
 * }
 * @endcode
 *
 * @param[in]  in       An input stream already opened to a JSON source (e.g., ifstream or istringstream).
 * @param[out] endpoint A string reference where the WebSocket endpoint will be stored.
 * @param[out] subs     A vector of strings where the subscription symbols will be stored.
 *
 * @return true if parsing was successful and required fields were present; false otherwise.
 */
inline bool parse_config(std::istream& in, std::string& endpoint, std::vector<std::string>& subs) {
    try {
        nlohmann::json config;
        in >> config;

        if (!config.contains("endpoint") || !config.contains("subs")) {
            std::cerr << "❌ JSON missing required fields" << std::endl;
            return false;
        }

        endpoint = config["endpoint"].get<std::string>();
        subs = config["subs"].get<std::vector<std::string>>();
        return true;

    } catch (const std::exception& e) {
        std::cerr << "❌ JSON parsing error: " << e.what() << std::endl;
        return false;
    }
}

