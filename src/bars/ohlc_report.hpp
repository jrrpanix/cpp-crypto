#pragma once

#include "ohlc_bar.hpp"
#include <iomanip>
#include <sstream>
#include <string>

/**
 * @brief Returns a formatted string representing the OHLC bar for a given
 * symbol.
 */
inline std::string format_ohlc_row(const std::string &symbol,
                                   const OHLCBar &bar) {
  std::ostringstream oss;
  oss << std::left << std::setw(10) << symbol << std::right << std::fixed
      << std::setprecision(2) << std::setw(10) << bar.open << std::setw(10)
      << bar.high << std::setw(10) << bar.low << std::setw(10) << bar.close
      << std::setw(10) << bar.count;
  return oss.str();
}

/**
 * @brief Returns a header string with aligned column labels.
 */
inline std::string format_ohlc_header() {
  std::ostringstream oss;
  oss << std::left << std::setw(10) << "Symbol" << std::right << std::setw(10)
      << "Open" << std::setw(10) << "High" << std::setw(10) << "Low"
      << std::setw(10) << "Close" << std::setw(10) << "Count";
  return oss.str();
}
