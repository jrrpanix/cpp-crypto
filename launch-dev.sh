#!/bin/sh
set -e

# Default values
DEFAULT_IMAGE="cpp-dev"
DEFAULT_WORKDIR="$PWD"

# Help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [cpp|full] [WORKDIR]"
    echo
    echo "Runs the specified Docker image with WORKDIR mounted to /workspace."
    echo
    echo "Arguments:"
    echo "  cpp        Use the C++-only lightweight image (default)"
    echo "  full       Use the full Python+C++ development image"
    echo "  WORKDIR    Path to mount (default: current directory)"
    echo
    echo "Examples:"
    echo "  $0                    # launches cpp-dev with current dir"
    echo "  $0 full               # launches full-dev with current dir"
    echo "  $0 cpp \$HOME/cpp-dev   # launches cpp-dev with specific path"
    exit 0
fi

# First arg: image type
IMAGETYPE="${1:-cpp}"
case "$IMAGETYPE" in
    cpp)  IMAGE="cpp-dev" ;;
    full) IMAGE="full-dev" ;;
    *)
        echo "❌ Invalid image type: $IMAGETYPE"
        echo "   Use 'cpp' or 'full'"
        exit 1
        ;;
esac

# Second arg (if provided): mount directory
if [ -n "$2" ]; then
    WORKDIR="$2"
else
    WORKDIR="$DEFAULT_WORKDIR"
fi

# Validate working directory
if [ ! -d "$WORKDIR" ]; then
    echo "❌ Error: Directory '$WORKDIR' does not exist."
    exit 1
fi

echo "✅ Launching image: $IMAGE"
echo "📂 Mounting: $WORKDIR → /workspace"

docker run -it --rm \
  -v "$WORKDIR:/workspace" \
  -w /workspace \
  "$IMAGE" \
  /bin/bash

