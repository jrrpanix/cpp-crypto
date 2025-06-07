#!/bin/sh
set -e

if [ "$1" = "cpp" ]; then
    echo "🔨 Building C++-only dev image..."
    docker build -t cpp-dev -f docker/cpp-dev/Dockerfile .
elif [ "$1" = "full" ]; then
    echo "🔨 Building full Python+C++ dev image..."
    docker build -t full-dev -f docker/full-dev/Dockerfile .
elif [ "$1" = "runtime" ]; then
    echo "🔨 Building runtime image..."
    docker build -f docker/runtime/Dockerfile -t binance-runtime .
else
    echo "Usage: $0 [cpp|full]"
    exit 1
fi

