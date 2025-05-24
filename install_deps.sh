#!/bin/sh
set -e  # Exit immediately on error

INSTALLDIR="/workspace/install"

# Check if IXWebSocket directory already exists
if [ -d IXWebSocket ]; then
    echo "Directory 'IXWebSocket' already exists."
    echo "To perform a clean build, please remove it:"
    echo "  rm -rf IXWebSocket"
    exit 1
fi

# Create install directory
mkdir -p "$INSTALLDIR"

# Clone and build IXWebSocket with TLS support
git clone https://github.com/machinezone/IXWebSocket.git
cd IXWebSocket
mkdir -p build && cd build
cmake -DCMAKE_INSTALL_PREFIX="$INSTALLDIR" -DUSE_TLS=TRUE ..
make -j$(nproc)
make install
cd ../..

# Clone and build fast_float (header-only fast float parsing)
git clone https://github.com/fastfloat/fast_float.git
cd fast_float && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX="$INSTALLDIR" ..
make -j$(nproc)
make install
cd ../..

# Download nlohmann/json single header
mkdir -p "$INSTALLDIR/include/nlohmann"
wget -q https://github.com/nlohmann/json/releases/latest/download/json.hpp \
    -O "$INSTALLDIR/include/nlohmann/json.hpp"

# Clone and build simdjson
git clone https://github.com/simdjson/simdjson.git
cd simdjson && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX="$INSTALLDIR" ..
make -j$(nproc)
make install

