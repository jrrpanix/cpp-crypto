#!/bin/sh
set -e

# Ensure we're running from inside simd-d
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Clean and create build directory
rm -rf build_consumer
mkdir -p build_consumer
cd build_consumer

# Configure and build
cmake .. \
  -DLOCAL_INCLUDE_DIR=/workspace/install/include \
  -DLOCAL_LIB_DIR=/workspace/install/lib \
  -DCMAKE_INSTALL_PREFIX=/workspace/apps \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_COMPILER=/usr/bin/g++

make -j"$(nproc)"
make install

