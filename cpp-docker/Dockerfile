FROM ubuntu:22.04

# Avoid interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Install build tools and CMake
RUN apt-get update && \
    apt-get install -y build-essential cmake && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the source code and CMakeLists.txt
COPY . .

# Create a build directory and compile the project
RUN mkdir build && cd build && \
    cmake .. && \
    make

# Run the built program
CMD ["./build/test"]

