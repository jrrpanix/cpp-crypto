#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <random>
#include <chrono>
#include <nlohmann/json.hpp>
#include "robin_hood.h"
#include "symbol_lookup.hpp"  // gperf

using json = nlohmann::json;
constexpr int NUM_TRIALS = 1'000'000;

using symbol_map_std = std::unordered_map<std::string, int32_t>;
using symbol_map_rh  = robin_hood::unordered_flat_map<std::string, int32_t>;

std::vector<std::string> load_symbols(const std::string& path, symbol_map_std& std_map, symbol_map_rh& rh_map) {
    std::ifstream f(path);
    json j;
    f >> j;

    std::vector<std::string> symbols;
    for (auto& [sym, id] : j.items()) {
        std_map[sym] = id;
        rh_map[sym] = id;
        symbols.push_back(sym);
    }
    return symbols;
}

template <typename Map>
void benchmark_map(const std::string& label, const Map& map, const std::vector<std::string>& symbols) {
    std::mt19937 rng(42);
    std::uniform_int_distribution<size_t> dist(0, symbols.size() - 1);
    volatile int32_t result = 0;

    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < NUM_TRIALS; ++i) {
        const std::string& sym = symbols[dist(rng)];
        result ^= map.at(sym);
    }
    auto end = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration<double, std::nano>(end - start);
    std::cout << label << " avg lookup: "
              << duration.count() / NUM_TRIALS << " ns\n";
}

void benchmark_gperf(const std::vector<std::string>& symbols) {
    std::mt19937 rng(42);
    std::uniform_int_distribution<size_t> dist(0, symbols.size() - 1);
    volatile int32_t result = 0;
    Perfect_Hash ph;
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < NUM_TRIALS; ++i) {
        const std::string& sym = symbols[dist(rng)];
        const SymbolEntry* entry = ph.lookup_symbol(sym.c_str(), sym.size());
        if (entry) result ^= entry->id;
    }
    auto end = std::chrono::high_resolution_clock::now();

    auto duration = std::chrono::duration<double, std::nano>(end - start);
    std::cout << "gperf avg lookup: "
              << duration.count() / NUM_TRIALS << " ns\n";
}

int main() {
    symbol_map_std std_map;
    symbol_map_rh rh_map;
    auto symbols = load_symbols("symbols.json", std_map, rh_map);

    std::cout << "Loaded " << symbols.size() << " symbols\n\n";

    benchmark_map("std::unordered_map", std_map, symbols);
    benchmark_map("robin_hood::flat_map", rh_map, symbols);
    benchmark_gperf(symbols);

    return 0;
}

