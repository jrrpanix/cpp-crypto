#!/bin/bash
set -e

echo "=== Testing build with vendored dependencies ==="
echo "This script builds the project assuming /opt/cpp-crypto-deps is unavailable."
echo "If present, manually move it out of the way first:"
echo "  sudo mv /opt/cpp-crypto-deps /tmp/cpp-crypto-deps-backup"
echo ""

# Clean and create build directory
rm -rf build
mkdir -p build
cd build

# Run cmake - should use vendored deps from third_party
echo "Running CMake with vendored dependencies..."
cmake .. \
    -DCMAKE_BUILD_TYPE=Release

echo ""
echo "Building project..."
make -j"$(nproc)"

echo ""
echo "=== SUCCESS! ==="
echo "Project built successfully using vendored headers from /workspace/third_party"
echo ""
echo "If you moved /opt/cpp-crypto-deps, restore it with:"
echo "  sudo mv /tmp/cpp-crypto-deps-backup /opt/cpp-crypto-deps"

