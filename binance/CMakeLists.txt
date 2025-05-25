cmake_minimum_required(VERSION 3.10)
project(SimdD)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Allow overriding via -D in CLI
set(LOCAL_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/../install/include" CACHE PATH "Local include path")
set(LOCAL_LIB_DIR "${CMAKE_SOURCE_DIR}/../install/lib" CACHE PATH "Local lib path")

# Include paths
include_directories(
    ${LOCAL_INCLUDE_DIR}
    ${CMAKE_SOURCE_DIR}/book_ticker
)

# Main executable
add_executable(binance_main binance_main.cpp)
target_link_directories(binance_main PRIVATE ${LOCAL_LIB_DIR})
target_compile_options(binance_main PRIVATE -O3 -march=native)
target_link_libraries(binance_main
    PRIVATE
        simdjson
        ixwebsocket      # <-- This was missing
        ssl
        crypto
        z
        pthread
)

# Add tests from tests/ directory
file(GLOB TEST_SOURCES ${CMAKE_SOURCE_DIR}/tests/test_*.cpp)
foreach(TEST_SRC ${TEST_SOURCES})
    get_filename_component(TEST_NAME ${TEST_SRC} NAME_WE)
    add_executable(${TEST_NAME} ${TEST_SRC})
    target_include_directories(${TEST_NAME} PRIVATE ${LOCAL_INCLUDE_DIR} ${CMAKE_SOURCE_DIR}/book_ticker)
    target_link_directories(${TEST_NAME} PRIVATE ${LOCAL_LIB_DIR})
    target_compile_options(${TEST_NAME} PRIVATE -O3 -march=native)
    target_link_libraries(${TEST_NAME}
        PRIVATE
            simdjson
            ixwebsocket  # <-- Also include here if any tests use it
            ssl
            crypto
            z
            pthread
    )
endforeach()

