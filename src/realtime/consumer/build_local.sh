#!/bin/sh
set -e

# Ensure we're running from inside simd-d
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Clean and create build directory
rm -rf build_consumer
mkdir -p build_consumer
cd build_consumer

# Run cmake
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_PREFIX_PATH=/opt/cpp-crypto-deps

# Build the project
make VERBOSE=1 -j"$(nproc)"
make install

