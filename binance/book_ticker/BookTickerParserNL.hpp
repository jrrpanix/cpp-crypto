#pragma once

#include "BookTicker.hpp"
#include <charconv> // for fast_float::from_chars if used
#include <nlohmann/json.hpp>
#include <string>
#include <string_view>

using json = nlohmann::json;

inline bool parse_book_ticker_nlohmann(const std::string &s, BookTicker &bt) {
  json doc;
  try {
    doc = json::parse(s);
  } catch (const json::parse_error &e) {
    return false;
  }

  try {
    // Extract values as strings and convert using fast_float for consistency
    std::string bid_price_str = doc.at("b").get<std::string>();
    std::string bid_qty_str = doc.at("B").get<std::string>();
    std::string ask_price_str = doc.at("a").get<std::string>();
    std::string ask_qty_str = doc.at("A").get<std::string>();

    auto err1 = fast_float::from_chars(
        bid_price_str.data(), bid_price_str.data() + bid_price_str.size(),
        bt.bid_price);
    auto err2 = fast_float::from_chars(bid_qty_str.data(),
                                       bid_qty_str.data() + bid_qty_str.size(),
                                       bt.bid_qty);
    auto err3 = fast_float::from_chars(
        ask_price_str.data(), ask_price_str.data() + ask_price_str.size(),
        bt.ask_price);
    auto err4 = fast_float::from_chars(ask_qty_str.data(),
                                       ask_qty_str.data() + ask_qty_str.size(),
                                       bt.ask_qty);

    if ((err1.ec != std::errc()) || (err2.ec != std::errc()) ||
        (err3.ec != std::errc()) || (err4.ec != std::errc())) {
      return false;
    }

    bt.update_id = doc.at("u").get<int64_t>();
    bt.trade_time = doc.at("T").get<int64_t>();
    // bt.event_time = doc.at("E").get<int64_t>();
  } catch (const json::exception &e) {
    return false;
  }

  return true;
}
