// BookTickerParser.hpp
#pragma once
#include <simdjson.h>
#include "BookTicker.hpp"

bool parse_book_ticker(simdjson::ondemand::parser &parser, const std::string &s, BookTicker &bt) {
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
  //std::string_view symbol = std::string(doc["s"].get_string().value());

  bt.trade_time = doc["T"].get_int64().value();
  bt.event_time = doc["E"].get_int64().value();
  return true;
}
