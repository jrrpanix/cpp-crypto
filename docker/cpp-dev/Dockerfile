FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install essential build tools and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    time \
    git \
    curl \
    wget \
    pkg-config \
    libssl-dev \
    zlib1g-dev \
    libzmq3-dev \
    libspdlog-dev \
    libcurl4-openssl-dev \
    ca-certificates \
    emacs-nox \
    vim \
    clang-format \
    clang-tidy \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /workspace

# Default command
CMD ["/bin/bash"]

