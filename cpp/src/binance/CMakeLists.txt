cmake_minimum_required(VERSION 3.10)
project(SimdD)

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
# Priority:
#   1. CI environment: /opt/cpp-crypto-deps (precompiled optimized libraries)
#   2. Offline/fallback: /workspace/cpp/third_party (vendored copy of dependencies)
#
# The cpp/third_party/ directory contains vendored headers and compiled libraries
# for resilience against external project unavailability. This allows builds
# even if original upstream projects become unavailable.
if(EXISTS "/opt/cpp-crypto-deps/include")
    set(DEPS_ROOT "/opt/cpp-crypto-deps")
    message(STATUS "Using CI dependencies: ${DEPS_ROOT}")
else()
    set(DEPS_ROOT "${PROJECT_SRC_DIR}/cpp/third_party")
    message(STATUS "Using vendored dependencies (offline fallback): ${DEPS_ROOT}")
endif()

# Always include cpp/third_party for header-only libraries
include_directories(${PROJECT_SRC_DIR}/cpp/third_party)

# Add the dependency directories to the search paths
include_directories(${DEPS_ROOT})
link_directories(${DEPS_ROOT}/lib)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}
    ../common/ # Common utilities
)

# Add binance_main executable
add_executable(binance_main binance_main.cpp)
target_include_directories(binance_main
  PRIVATE
  ${PROJECT_SRC_DIR}/cpp/src
  ${CMAKE_CURRENT_SOURCE_DIR}/book_ticker
)
target_link_directories(binance_main PRIVATE ${DEPS_ROOT}/lib)
target_compile_options(binance_main PRIVATE -O3 -march=native)
target_link_libraries(binance_main
  PRIVATE
    simdjson
    ixwebsocket
    ssl
    crypto
    z
    pthread
    zmq
)
install(TARGETS binance_main DESTINATION bin)

# Add mock_binance_main executable
add_executable(mock_binance_main mock_binance_main.cpp)
target_include_directories(mock_binance_main
  PRIVATE
  ${PROJECT_SRC_DIR}/cpp/src
  ${CMAKE_CURRENT_SOURCE_DIR}/book_ticker
)
target_link_directories(mock_binance_main PRIVATE ${DEPS_ROOT}/lib)
target_compile_options(mock_binance_main PRIVATE -O3 -march=native)
target_link_libraries(mock_binance_main
  PRIVATE
    simdjson
    ixwebsocket
    ssl
    crypto
    z
    pthread
    zmq
)
install(TARGETS mock_binance_main DESTINATION bin)


# mock_producer
add_executable(mock_producer_main mock_producer_main.cpp)
target_link_directories(mock_producer_main PRIVATE ${DEPS_ROOT}/lib)
target_include_directories(mock_producer_main
  PRIVATE
    ${PROJECT_SRC_DIR}/cpp/src
)

target_compile_options(mock_producer_main PRIVATE -O3 -march=native)

target_link_libraries(mock_producer_main
  PRIVATE
    simdjson
    zmq
    pthread
)

# Install the test producer binary
install(TARGETS mock_producer_main DESTINATION bin)


# Add parquet_reader executable
add_executable(parquet_reader parquet_reader.cpp)
target_include_directories(parquet_reader
  PRIVATE
  ${PROJECT_SRC_DIR}/cpp/src
)
target_link_directories(parquet_reader PRIVATE ${DEPS_ROOT}/lib)
target_compile_options(parquet_reader PRIVATE -O3 -march=native)
target_link_libraries(parquet_reader
  PRIVATE
    arrow
    parquet
    pthread
)
install(TARGETS parquet_reader DESTINATION bin)


# Install config files
install(DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}/config/
        DESTINATION ${CMAKE_INSTALL_PREFIX}/config/binance
        FILES_MATCHING PATTERN "*.json")


# ================================
# Add and configure test targets
# ================================
file(GLOB TEST_SOURCES ${CMAKE_CURRENT_SOURCE_DIR}/tests/test_*.cpp)

foreach(TEST_SRC ${TEST_SOURCES})
    get_filename_component(TEST_NAME ${TEST_SRC} NAME_WE)
    add_executable(${TEST_NAME} ${TEST_SRC})

    target_include_directories(${TEST_NAME}
        PRIVATE
            ${PROJECT_SRC_DIR}/cpp/src
            ${CMAKE_CURRENT_SOURCE_DIR}/book_ticker
    )

    target_link_directories(${TEST_NAME} PRIVATE ${DEPS_ROOT}/lib)
    target_compile_options(${TEST_NAME} PRIVATE -O3 -march=native)

    target_link_libraries(${TEST_NAME}
        PRIVATE
            simdjson
            ixwebsocket
            ssl
            crypto
            z
            pthread
    )

    # Install test binaries
    install(TARGETS ${TEST_NAME} DESTINATION bin/tests)
endforeach()
