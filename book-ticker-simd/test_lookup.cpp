#include <iostream>
#include <vector>
#include <string>
#include <unordered_map>
#include <map>
#include <algorithm>
#include <chrono>
#include <random>
#include <functional>
#include <numeric>

using namespace std;
using namespace std::chrono;

vector<string> generate_random_strings(size_t count, size_t max_length) {
    static const char charset[] = "abcdefghijklmnopqrstuvwxyz";
    static mt19937 rng(random_device{}());
    uniform_int_distribution<> len_dist(5, max_length);
    uniform_int_distribution<> char_dist(0, sizeof(charset) - 2);

    vector<string> result;
    for (size_t i = 0; i < count; ++i) {
        int len = len_dist(rng);
        string s;
        for (int j = 0; j < len; ++j) {
            s += charset[char_dist(rng)];
        }
        result.push_back(s);
    }
    return result;
}

long long benchmark_unordered_map(const unordered_map<string, int>& umap, const vector<string>& keys, const vector<int>& indices) {
    long long total_ns = 0;
    for (int idx : indices) {
        auto start = high_resolution_clock::now();
        volatile int x = umap.at(keys[idx]);
        auto end = high_resolution_clock::now();
        total_ns += duration_cast<nanoseconds>(end - start).count();
    }
    return total_ns / indices.size();
}

long long benchmark_map(const map<string, int>& omap, const vector<string>& keys, const vector<int>& indices) {
    long long total_ns = 0;
    for (int idx : indices) {
        auto start = high_resolution_clock::now();
        volatile int x = omap.at(keys[idx]);
        auto end = high_resolution_clock::now();
        total_ns += duration_cast<nanoseconds>(end - start).count();
    }
    return total_ns / indices.size();
}

long long benchmark_sorted_vector(const vector<pair<string, int>>& sorted_vec, const vector<string>& keys, const vector<int>& indices) {
    long long total_ns = 0;
    for (int idx : indices) {
        auto start = high_resolution_clock::now();
        auto it = lower_bound(sorted_vec.begin(), sorted_vec.end(), keys[idx],
            [](const auto& p, const string& val) {
                return p.first < val;
            });
        volatile int x = (it != sorted_vec.end() && it->first == keys[idx]) ? it->second : -1;
        auto end = high_resolution_clock::now();
        total_ns += duration_cast<nanoseconds>(end - start).count();
    }
    return total_ns / indices.size();
}

int main() {
    const int N = 200;
    const int trials = 20000000;
    mt19937 rng(random_device{}());

    auto keys = generate_random_strings(N, 20);
    unordered_map<string, int> umap;
    map<string, int> omap;
    vector<pair<string, int>> sorted_vec;

    for (int i = 0; i < N; ++i) {
        umap[keys[i]] = i;
        omap[keys[i]] = i;
        sorted_vec.emplace_back(keys[i], i);
    }
    sort(sorted_vec.begin(), sorted_vec.end());

    // Pre-generate random indices for fair testing
    uniform_int_distribution<> dist(0, N - 1);
    vector<int> indices(trials);
    for (int& i : indices) i = dist(rng);

    // Randomize benchmark order
    vector<pair<string, function<long long()>>> benchmarks = {
        {"unordered_map", [&]() { return benchmark_unordered_map(umap, keys, indices); }},
        {"map",           [&]() { return benchmark_map(omap, keys, indices); }},
        {"lower_bound",   [&]() { return benchmark_sorted_vector(sorted_vec, keys, indices); }}
    };
    shuffle(benchmarks.begin(), benchmarks.end(), rng);

    // Execute
    for (const auto& [name, func] : benchmarks) {
        long long avg_ns = func();
        cout << name << " average lookup time: " << avg_ns << " ns\n";
    }

    return 0;
}

