#include "common/time_utils.hpp"
#include <iostream>

void benchmark_clock_calls() {
  constexpr int N = 1'000'000;

  auto start = std::chrono::high_resolution_clock::now();

  volatile int64_t sink = 0; // prevent optimization
  for (int i = 0; i < N; ++i) {
    sink = sink + now_ns_since_epoch();
  }

  auto end = std::chrono::high_resolution_clock::now();
  auto duration_ns =
      std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count();

  std::cout << "Total time: " << duration_ns << " ns\n";
  std::cout << "Average time per call: " << (duration_ns / N) << " ns\n";
}

int main() {
  benchmark_clock_calls();
  return 0;
}
