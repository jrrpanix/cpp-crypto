#!/bin/sh
set -e  # Exit immediately on error

INSTALLDIR="/workspace/install"
THIRD_PARTY_DIR="/workspace/third_party"

# Create necessary directories
mkdir -p "$INSTALLDIR"
mkdir -p "$THIRD_PARTY_DIR"

cd "$THIRD_PARTY_DIR"

# Check if IXWebSocket directory already exists
if [ -d IXWebSocket ]; then
    echo "Directory '$THIRD_PARTY_DIR/IXWebSocket' already exists."
    echo "To perform a clean build, please remove it:"
    echo "  rm -rf $THIRD_PARTY_DIR/IXWebSocket"
    exit 1
fi

# Clone and build IXWebSocket with TLS support
git clone https://github.com/machinezone/IXWebSocket.git
cd IXWebSocket
mkdir -p build && cd build
cmake -DCMAKE_INSTALL_PREFIX="$INSTALLDIR" -DUSE_TLS=TRUE ..
make -j$(nproc)
make install
cd "$THIRD_PARTY_DIR"

# Clone and build fast_float
git clone https://github.com/fastfloat/fast_float.git
cd fast_float && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX="$INSTALLDIR" ..
make -j$(nproc)
make install
cd "$THIRD_PARTY_DIR"

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

