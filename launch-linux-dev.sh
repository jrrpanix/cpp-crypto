                                                                                                                                                                                                             #!/bin/sh

# Default work directory if none is given
DEFAULT_WORKDIR="$HOME/cpp-crypto"

# Handle --help
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [WORKDIR]"
    echo
    echo "Runs the linux-dev Docker container with WORKDIR mounted to /workspace."
    echo
    echo "Options:"
    echo "  WORKDIR    Directory to mount into the container (default: $DEFAULT_WORKDIR)"
    echo
    echo "Examples:"
    echo "  $0                            # uses $DEFAULT_WORKDIR"
    echo "  $0 \$HOME/dev                 # uses your dev directory"
    echo "  WORKDIR=/tmp $0              # override using env var"
    exit 0
fi

# Determine the workdir (env var > arg > default)
WORKDIR=${WORKDIR:-${1:-$DEFAULT_WORKDIR}}

# Verify that WORKDIR exists
if [ ! -d "$WORKDIR" ]; then
    echo "❌ Error: WORKDIR '$WORKDIR' does not exist."
    exit 1
fi

echo "✅ WORKDIR is set to: $WORKDIR"

# Run the container
docker run -it --rm -v "$WORKDIR:/workspace" linux-dev

