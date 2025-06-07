FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y \
    libzmq5 \
    libssl3 \
    zlib1g \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/apps/bin
COPY apps/bin/ /workspace/apps/bin/

CMD ["/bin/bash"]

