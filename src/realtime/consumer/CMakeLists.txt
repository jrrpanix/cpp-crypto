cmake_minimum_required(VERSION 3.10)
project(ConsumerZMQ)

if(NOT DEFINED PROJECT_SRC_DIR)
  set(PROJECT_SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../../..)
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Enable verbose output to see full compiler commands
set(CMAKE_VERBOSE_MAKEFILE ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Intelligently determine the dependency root directory
# Use /opt/cpp-crypto-deps for CI, otherwise use project's install directory
if(EXISTS "/opt/cpp-crypto-deps/include")
    set(DEPS_ROOT "/opt/cpp-crypto-deps")
    message(STATUS "Using CI dependencies: ${DEPS_ROOT}")
else()
    set(DEPS_ROOT "${PROJECT_SRC_DIR}/install")
    message(STATUS "Using local dependencies: ${DEPS_ROOT}")
endif()

# Add the dependency directories to the search paths
include_directories(${DEPS_ROOT}/include)
link_directories(${DEPS_ROOT}/lib)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ../common/ # Common utilities
)

# Build consumer_main executable
add_executable(consumer_main consumer_main.cpp)

# Include paths (aligned with BookTicker location)
target_include_directories(consumer_main
  PRIVATE
  ${PROJECT_SRC_DIR}/src/realtime
)

target_link_directories(consumer_main PRIVATE ${DEPS_ROOT}/lib)
target_compile_options(consumer_main PRIVATE -O3 -march=native)

# Link with ZeroMQ and other relevant libraries
target_link_libraries(consumer_main
  PRIVATE
    cpr
    zmq
    pthread
    curl
    ssl
    crypto
)

# Optional: install the consumer binary (like binance_main)
install(TARGETS consumer_main DESTINATION bin)

