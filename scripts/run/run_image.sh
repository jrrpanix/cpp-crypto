#!/bin/sh
set -e

DEFAULT_IMAGE="cpp-dev"
DEFAULT_WORKDIR="$PWD"

# Help message
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [cpp|full|runtime] [WORKDIR] [-- binance_args...]"
    echo
    echo "Arguments:"
    echo "  cpp         Use lightweight C++ dev image (default)"
    echo "  full        Use full Python+C++ dev image"
    echo "  runtime     Run production image (binance-runtime)"
    echo "  WORKDIR     Optional path to mount (default: current dir)"
    echo "  -- args...  If using 'runtime', pass args to binance_main"
    echo
    echo "Examples:"
    echo "  $0 runtime                        # opens /bin/bash"
    echo "  $0 runtime -- --help             # runs binance_main --help"
    echo "  $0 full                          # starts full dev shell"
    echo "  $0 cpp ~/dev                     # mounts ~/dev"
    exit 0
fi

# Image selection
IMAGETYPE="${1:-cpp}"
case "$IMAGETYPE" in
    cpp)     IMAGE="cpp-dev" ;;
    full)    IMAGE="full-dev" ;;
    runtime) IMAGE="binance-runtime" ;;
    *)
        echo "❌ Invalid image type: $IMAGETYPE"
        exit 1
        ;;
esac

# Optional workdir
shift
if [ -n "$1" ] && [ "$1" != "--" ]; then
    WORKDIR="$1"
    shift
else
    WORKDIR="$DEFAULT_WORKDIR"
fi

# Remaining args
CMD_ARGS="$@"

# Validate dir
if [ ! -d "$WORKDIR" ]; then
    echo "❌ Error: Directory '$WORKDIR' does not exist."
    exit 1
fi

echo "✅ Launching image: $IMAGE"
echo "📂 Mounting: $WORKDIR → /workspace"

if [ "$IMAGETYPE" = "runtime" ]; then
    if [ -z "$CMD_ARGS" ]; then
        docker run -it --rm \
            -v "$WORKDIR:/workspace" \
            -w /workspace/apps/bin \
            "$IMAGE" \
            /bin/bash
    else
        docker run --rm \
            -v "$WORKDIR:/workspace" \
            -w /workspace/apps/bin \
            "$IMAGE" \
            ./binance_main $CMD_ARGS
    fi
else
    docker run -it --rm \
        -v "$WORKDIR:/workspace" \
        -w /workspace \
        "$IMAGE" \
        /bin/bash
fi

