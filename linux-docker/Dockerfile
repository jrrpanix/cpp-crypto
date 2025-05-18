# docker/Dockerfile

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install C++ build tools and common libraries
RUN apt-get update && \
    apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    pkg-config \
    libssl-dev \
    zlib1g-dev \
    libspdlog-dev \
    emacs-nox \
    clang-format \
    clang-tidy \	
    vim \
    && rm -rf /var/lib/apt/lists/*

# Working directory where you’ll mount your project
WORKDIR /workspace

CMD ["/bin/bash"]

