#!/bin/bash

# Exit on error
set -e

# Set default working directory
DEFAULT_WORKDIR="$HOME/cpp-crypto"
WORKDIR=${WORKDIR:-$DEFAULT_WORKDIR}

# Step 1: Build the Docker container
echo "🛠️  Building Docker container..."
./build_docker.sh cpp

# Step 2: Launch the container and run build and run scripts inside
echo "🚀 Launching container and running setup..."

docker run -it --rm -v "$WORKDIR:/workspace" cpp-dev /bin/bash -c '
  set -e
  echo "🔧 Running install_deps.sh..."
  ./install_deps.sh

  echo "📦 Building Binance inside /workspace/binance..."
  cd binance
  ./build_local.sh

  echo "🏁 Running binance_main..."
  ./build/binance_main --config_file config.json --key spot
'

