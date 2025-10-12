cmake_minimum_required(VERSION 3.10)
project(ConsumerZMQ)

if(NOT DEFINED PROJECT_SRC_DIR)
  set(PROJECT_SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../../..)
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Allow overriding via -D in CLI
set(LOCAL_INCLUDE_DIR "${PROJECT_SRC_DIR}/install/include" CACHE PATH "Local include path")
set(LOCAL_LIB_DIR "${PROJECT_SRC_DIR}/install/lib" CACHE PATH "Local lib path")

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ../common/ # Common utilities
    ../../../third_party/cpr/include
)

# Build consumer_main executable
add_executable(consumer_main consumer_main.cpp)

# Include paths (aligned with BookTicker location)
target_include_directories(consumer_main
  PRIVATE
  ${PROJECT_SRC_DIR}/src/realtime
  ${LOCAL_INCLUDE_DIR}
)

target_link_directories(consumer_main PRIVATE ${LOCAL_LIB_DIR})
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

