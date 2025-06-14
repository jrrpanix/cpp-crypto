FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Step 1: Core build tools and C++ environment
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    time \
    git \
    curl \
    wget \
    gperf \
    pkg-config \
    libssl-dev \
    zlib1g-dev \
    libzmq3-dev \
    libspdlog-dev \
    libcurl4-openssl-dev \
    ca-certificates \
    gnupg \
    emacs-nox \
    clang-format \
    clang-tidy \
    vim \
    software-properties-common && \
    rm -rf /var/lib/apt/lists/*

# Step 2: Add deadsnakes PPA and install Python 3.12
RUN add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-dev \
    python3.12-venv && \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12 && \
    ln -sf /usr/bin/python3.12 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3 /usr/bin/pip && \
    rm -rf /var/lib/apt/lists/*

# Step 3: Install uv (fast virtualenv + package manager)
RUN curl -Ls https://astral.sh/uv/install.sh | bash

ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /workspace

CMD ["/bin/bash"]

