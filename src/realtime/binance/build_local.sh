#!/bin/sh
set -e

# Ensure we're running from inside simd-d
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Clean and create build directory
rm -rf build_binance
mkdir -p build_binance
cd build_binance

# Run cmake
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH=/opt/cpp-crypto-deps

# Build the project
make -j"$(nproc)"
make install

