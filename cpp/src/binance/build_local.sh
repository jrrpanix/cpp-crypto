#!/bin/sh
set -e

# Clean and create build directory
rm -rf build
mkdir -p build
cd build

# Determine install prefix based on environment
if [ -d "/opt/cpp-crypto-deps" ]; then
    INSTALL_PREFIX="/opt/cpp-crypto-deps"
else
    INSTALL_PREFIX="$(cd ../../.. && pwd)/cpp/install"
fi

# Run cmake
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${INSTALL_PREFIX}"

# Build the project
make -j"$(nproc)"
make install

