#!/bin/sh
set -e  # Exit on error

INSTALLDIR="/opt/cpp-crypto-deps"
THIRD_PARTY_DIR="/workspace/third_party"

# Create required directories
mkdir -p "$INSTALLDIR/include"
mkdir -p "$THIRD_PARTY_DIR"
cd "$THIRD_PARTY_DIR"

build_project() {
  local name="$1"
  local git_url="$2"
  local cmake_flags="$3"

  if [ -d "$name" ]; then
    echo "✅ $name already exists, skipping clone and build."
    return
  fi

  echo "📥 Cloning $name..."
  git clone "$git_url" "$name"

  echo "🔧 Building $name..."
  cd "$name"
  mkdir -p build && cd build
  cmake -DCMAKE_INSTALL_PREFIX="$INSTALLDIR" $cmake_flags ..
  make -j"$(nproc)"
  make install
  cd "$THIRD_PARTY_DIR"
}

# Build simdjson
build_project "simdjson" "https://github.com/simdjson/simdjson.git" ""

# Build IXWebSocket (with TLS)
build_project "IXWebSocket" "https://github.com/machinezone/IXWebSocket.git" "-DUSE_TLS=TRUE"

# Build fast_float
build_project "fast_float" "https://github.com/fastfloat/fast_float.git" ""

# Build CPR (HTTP client, depends on libcurl)
build_project "cpr" "https://github.com/libcpr/cpr.git" "-DCPR_USE_SYSTEM_CURL=ON"

# Install nlohmann/json single-header
NLOHMANN_HEADER="$INSTALLDIR/include/nlohmann/json.hpp"
if [ -f "$NLOHMANN_HEADER" ]; then
  echo "✅ nlohmann/json.hpp already exists, skipping download."
else
  echo "📥 Downloading nlohmann/json.hpp..."
  mkdir -p "$INSTALLDIR/include/nlohmann"
  wget -q https://github.com/nlohmann/json/releases/latest/download/json.hpp \
      -O "$NLOHMANN_HEADER"
fi

# Install robin_hood single-header
ROBIN_HOOD_HEADER="$INSTALLDIR/include/robin_hood.h"
if [ -f "$ROBIN_HOOD_HEADER" ]; then
  echo "✅ robin_hood.h already exists, skipping download."
else
  echo "📥 Downloading robin_hood.h..."
  wget https://raw.githubusercontent.com/martinus/robin-hood-hashing/master/src/include/robin_hood.h \
      -O "$ROBIN_HOOD_HEADER"
fi

# Install moodycamel/concurrentqueue headers
MOODYCAMEL_HEADER_DIR="$INSTALLDIR/include/moodycamel"
if [ -f "$MOODYCAMEL_HEADER_DIR/concurrentqueue.h" ]; then
  echo "✅ moodycamel/concurrentqueue.h already exists, skipping download."
else
  echo "📥 Downloading moodycamel concurrentqueue..."
  mkdir -p "$MOODYCAMEL_HEADER_DIR"
  wget -q https://raw.githubusercontent.com/cameron314/concurrentqueue/master/concurrentqueue.h \
      -O "$MOODYCAMEL_HEADER_DIR/concurrentqueue.h"
  wget -q https://raw.githubusercontent.com/cameron314/concurrentqueue/master/lightweightsemaphore.h \
      -O "$MOODYCAMEL_HEADER_DIR/lightweightsemaphore.h"
fi

# Install cppzmq (header-only C++ bindings for ZeroMQ)
CPPZMQ_HEADER="$INSTALLDIR/include/zmq.hpp"
if [ -f "$CPPZMQ_HEADER" ]; then
  echo "✅ cppzmq (zmq.hpp) already exists, skipping download."
else
  echo "📥 Downloading cppzmq (zmq.hpp)..."
  mkdir -p "$INSTALLDIR/include"
  wget -q https://raw.githubusercontent.com/zeromq/cppzmq/master/zmq.hpp \
      -O "$CPPZMQ_HEADER"
fi

# Final check to see what was installed
echo "--- Listing contents of installation directory: $INSTALLDIR ---"
echo "--- Include directory ($INSTALLDIR/include): ---"
ls -l $INSTALLDIR/include
echo "--- Lib directory ($INSTALLDIR/lib): ---"
ls -l $INSTALLDIR/lib
echo "-------------------------------------------------"

