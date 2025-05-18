#!/bin/sh

WORKDIR=${WORKDIR:-$1}

# Require WORKDIR to be passed as an environment variable
if [ -z "$WORKDIR" ]; then
    echo "❌ Error: WORKDIR must be set before running this script."
    echo "✅ Example: WORKDIR=/home/ubuntu/dev $0 or $0 /home/ubuntu/dev"
    exit 1
fi

echo "✅ WORKDIR is set to: $WORKDIR"

# run docker image mapping $WORKDIR to internal container path /workspace
docker run -it --rm -v $WORKDIR:/workspace linux-dev
