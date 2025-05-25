#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <unordered_map>
#include <random>
#include <chrono>
#include <nlohmann/json.hpp>
#include "symbol_lookup.hpp" // from gperf

using json = nlohmann::json;

constexpr int NUM_TRIALS = 1'000'000;

// Load symbol → id map from symbols.json
std::unordered_map<std::string, int32_t> load_symbol_map(const std::string& filename, std::vector<std::string>& symbols_out) {
    std::ifstream f(filename);
    if (!f.is_open()) {
        throw std::runtime_error("Failed to open symbols.json");
    }

    json j;
    f >> j;

    std::unordered_map<std::string, int32_t> map;
    for (auto& [sym, id] : j.items()) {
        map[sym] = id;
        symbols_out.push_back(sym);  // preserve order
    }
    return map;
}

void benchmark_unordered_map(const std::unordered_map<std::string, int32_t>& map, const std::vector<std::string>& symbols) {
    std::mt19937 rng(42);
    std::uniform_int_distribution<size_t> dist(0, symbols.size() - 1);
    volatile int32_t result = 0;

    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < NUM_TRIALS; ++i) {
        const std::string& key = symbols[dist(rng)];
        result ^= map.at(key);  // use at() for bounds-checked access
    }
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double, std::nano> duration = end - start;
    std::cout << "unordered_map avg lookup time: "
              << duration.count() / NUM_TRIALS << " ns\n";
}

void benchmark_gperf(const std::vector<std::string>& symbols) {
    std::mt19937 rng(42);
    std::uniform_int_distribution<size_t> dist(0, symbols.size() - 1);
    volatile int32_t result = 0;
    Perfect_Hash ph;
    auto start = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < NUM_TRIALS; ++i) {
        const std::string& key = symbols[dist(rng)];
        const SymbolEntry* entry = ph.lookup_symbol(key.c_str(), key.length());
        if (entry) result ^= entry->id;
	if (!entry) throw std::runtime_error("lookup fail");
    }
    auto end = std::chrono::high_resolution_clock::now();

    std::chrono::duration<double, std::nano> duration = end - start;
    std::cout << "gperf lookup avg time: "
              << duration.count() / NUM_TRIALS << " ns\n";
}

int main() {
    std::vector<std::string> symbols;
    auto map = load_symbol_map("symbols.json", symbols);
    std::cout << "size " << map.size() << std::endl;

    std::cout << "Benchmarking " << symbols.size() << " symbols over " << NUM_TRIALS << " trials:\n\n";
    benchmark_unordered_map(map, symbols);
    benchmark_gperf(symbols);
    return 0;
}

