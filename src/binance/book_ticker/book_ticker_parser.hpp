// BookTickerParser.hpp
#pragma once
#include "book_ticker.hpp"
#include "common/time_utils.hpp"
#include "symbol_id_map.hpp"
#include <fast_float/fast_float.h>
#include <simdjson.h>

inline bool field_exists(simdjson::ondemand::object obj,
                         const std::string &field) {
  auto result = obj.find_field(field);
  return result.error() == simdjson::SUCCESS;
}

/**
 * Parses a JSON message from Binance and extracts relevant fields
 * into the provided BookTicker struct.
 *
 * @param json_message A JSON message string from Binance.
 * @param parser simdjson ondemand parser used for efficient parsing.
 * @param book_ticker Reference to a BookTicker struct that will be populated
 * with parsed data.
 */

inline bool parse_book_ticker(simdjson::ondemand::parser &parser,
                              const std::string &s, BookTicker &bt,
                              bool set_recv_time,
                              const SymbolIdMap *symbol_lookup) {
  simdjson::padded_string padded(s);
  auto doc = parser.iterate(padded);

  // Extract the string views
  std::string_view bid_price_str = doc["b"].get_string().value();
  std::string_view bid_qty_str = doc["B"].get_string().value();
  std::string_view ask_price_str = doc["a"].get_string().value();
  std::string_view ask_qty_str = doc["A"].get_string().value();

  // Convert to double using fast_float
  auto err1 = fast_float::from_chars(
      bid_price_str.data(), bid_price_str.data() + bid_price_str.size(),
      bt.bid_price);
  auto err2 = fast_float::from_chars(
      bid_qty_str.data(), bid_qty_str.data() + bid_qty_str.size(), bt.bid_qty);
  auto err3 = fast_float::from_chars(
      ask_price_str.data(), ask_price_str.data() + ask_price_str.size(),
      bt.ask_price);
  auto err4 = fast_float::from_chars(
      ask_qty_str.data(), ask_qty_str.data() + ask_qty_str.size(), bt.ask_qty);

  if ((err1.ec != std::errc()) || (err2.ec != std::errc()) ||
      (err3.ec != std::errc()) || (err4.ec != std::errc())) {
    return false;
  }
  bt.update_id = doc["u"].get_int64().value();

  if (symbol_lookup) {
    std::string symbol = std::string(doc["s"].get_string().value());
    auto it = symbol_lookup->find(symbol);
    if (it != symbol_lookup->end())
      bt.id = it->second;
    else {
      throw std::runtime_error("ticker " + symbol + " no in lookup table");
    }
  }

  bt.trade_time = doc["T"].get_int64().value();
  int64_t event_time = doc["E"].get_int64().value();
  bt.event_time_ms_midnight = epoch_ms_to_midnight_ms_utc(event_time);

  if (set_recv_time) {
    bt.my_receive_time_ns = now_ns_since_epoch();
  }
  return true;
}
