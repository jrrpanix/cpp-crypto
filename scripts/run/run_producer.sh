#!/bin/sh
set -x

IMAGE="binance-runtime"
#IMAGE="cpp-dev"
DEFAULT_WORKDIR="$PWD"

# Optional workdir
if [ -n "$1" ] && [ "$1" != "--" ]; then
    WORKDIR="$1"
    shift
else
    WORKDIR="$DEFAULT_WORKDIR"
fi

# Validate directory
if [ ! -d "$WORKDIR" ]; then
    echo "❌ Error: Directory '$WORKDIR' does not exist."
    exit 1
fi

# Config path inside container
CFGDIR="/workspace/apps/config/binance"

# Command-line args for binance_main
CMD_ARGS="--config_file $CFGDIR/config.json --key fut --symbol_file $CFGDIR/symbols.json --debug"

# Launch docker container
echo "✅ Launching image: $IMAGE"
echo "📂 Mounting: $WORKDIR → /workspace"
echo "🚀 Args: $CMD_ARGS"

docker run --rm \
    -v "$WORKDIR:/workspace" \
    -w /workspace/apps/bin \
    "$IMAGE" \
    ./binance_main $CMD_ARGS

