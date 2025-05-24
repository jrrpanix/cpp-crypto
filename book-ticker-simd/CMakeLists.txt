cmake_minimum_required(VERSION 3.10)
project(MainApp)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# User-configurable include and library paths
set(LOCAL_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/install/include" CACHE PATH "IXWebSocket/simd include path")
set(LOCAL_LIB_DIR "${CMAKE_SOURCE_DIR}/install/lib" CACHE PATH "IXWebSocket/simd library path")

# Common compile options and libraries
set(COMMON_COMPILE_OPTIONS -O3 -march=native)
set(COMMON_LIBS simdjson ixwebsocket ssl crypto z pthread)

# Helper macro to avoid repeating configuration
function(add_custom_executable exe_name src_file)
    add_executable(${exe_name} ${src_file})
    target_include_directories(${exe_name} PRIVATE ${LOCAL_INCLUDE_DIR})
    target_link_directories(${exe_name} PRIVATE ${LOCAL_LIB_DIR})
    target_compile_options(${exe_name} PRIVATE ${COMMON_COMPILE_OPTIONS})
    target_link_libraries(${exe_name} PRIVATE ${COMMON_LIBS})
endfunction()

# Define executables
add_custom_executable(main             main.cpp)
add_custom_executable(test_clock_time  test_clock_time.cpp)
add_custom_executable(test_simd_parser test_simd_parser.cpp)
add_custom_executable(test_lookup      test_lookup.cpp)
add_custom_executable(msub             msub.cpp)
add_custom_executable(test_json_times  test_json_times.cpp)

