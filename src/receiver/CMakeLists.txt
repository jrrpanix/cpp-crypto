cmake_minimum_required(VERSION 3.10)
project(ConsumerZMQ)

if(NOT DEFINED PROJECT_SRC_DIR)
  set(PROJECT_SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../..)
endif()

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Allow overriding via -D in CLI
set(LOCAL_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/../../install/include" CACHE PATH "Local include path")
set(LOCAL_LIB_DIR "${CMAKE_SOURCE_DIR}/../../install/lib" CACHE PATH "Local lib path")

# Build consumer_main executable
add_executable(consumer_main consumer_main.cpp)

# Include paths (aligned with BookTicker location)
target_include_directories(consumer_main
  PRIVATE
  ${PROJECT_SRC_DIR}/src
  ${PROJECT_SRC_DIR}/src/binance/book_ticker
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

