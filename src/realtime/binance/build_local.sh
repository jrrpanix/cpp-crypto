#!/bin/sh
set -e

# Clean and create build directory
rm -rf build
mkdir -p build
cd build

# Run cmake
cmake .. \
    -DCMAKE_BUILD_TYPE=Release

# Build the project
make -j"$(nproc)"
make install

