#!/bin/bash

# Exit on error
set -e

# Set default working directory
DEFAULT_WORKDIR="$HOME/cpp-crypto"
WORKDIR=${WORKDIR:-$DEFAULT_WORKDIR}

# Step 1: Build the Docker container
echo "🛠️  Building Docker container..."
./scripts/build/docker_build.sh cpp

# Step 2: Launch the container and run build and run scripts inside
echo "🚀 Launching container and running setup..."

docker run -it --rm -v "$WORKDIR:/workspace" cpp-dev /bin/bash -c '
  set -e
  echo "🔧 Running install_deps.sh..."
  /workspace/scripts/install/deps_install.sh

  echo "📦 Building Binance inside /workspace/binance..."
  /workspace/scripts/build/binance_build.sh

#  echo "🏁 Running binance_main..."
#  ./build/binance_main --config_file config/config.json --key spot
'

