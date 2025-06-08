#pragma once

#include "bar_aggregator.hpp"
#include "ohlc_report.hpp"
#include "symbol_id_map.hpp"
#include <algorithm>
#include <iostream>
#include <vector>

class BarReportPrinter {
public:
  BarReportPrinter(const SymbolIdMap &symbol_map)
      : id_to_symbol_(invert_map(symbol_map)) {}
  /**
   * @brief Print the OHLC report from a BarAggregator, sorted by symbol name.
   *
   * @param aggregator Reference to the BarAggregator containing completed bars.
   * @param os Output stream to print to (e.g. std::cout, std::ofstream).
   */
  void print(const BarAggregator &aggregator, std::ostream &os) const {
    const auto &bars = aggregator.consume_completed_bars();
    if (bars.empty())
      return;

    std::vector<std::pair<std::string, const OHLCBar *>> rows;

    for (const auto &[id, bar] : bars) {
      auto it = id_to_symbol_.find(id);
      if (it != id_to_symbol_.end()) {
        rows.emplace_back(it->second, &bar);
      }
    }

    std::sort(rows.begin(), rows.end(),
              [](const auto &a, const auto &b) { return a.first < b.first; });

    os << format_ohlc_header() << '\n';
    for (const auto &[symbol, bar_ptr] : rows) {
      os << format_ohlc_row(symbol, *bar_ptr) << '\n';
    }
  }

private:
  using reverse_map = robin_hood::unordered_flat_map<int32_t, std::string>;
  reverse_map id_to_symbol_;

  static reverse_map invert_map(const SymbolIdMap &symbol_map) {
    reverse_map reversed;
    for (const auto &[sym, id] : symbol_map) {
      reversed[id] = sym;
    }
    return reversed;
  }
};
