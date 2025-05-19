cmake_minimum_required(VERSION 3.10)
project(MainApp)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)


# Allow the user to define these paths at configure time, but set defaults
set(LOCAL_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/install/include" CACHE PATH "IXWebSocket/simd include path")
set(LOCAL_LIB_DIR "${CMAKE_SOURCE_DIR}/install/lib" CACHE PATH "IXWebSocket/simd library path")

# Add your executable
add_executable(main main.cpp)

# Include headers from install/include
target_include_directories(main PRIVATE ${LOCAL_INCLUDE_DIR})

# Link against libixwebsocket and dependencies from install/lib
target_link_directories(main PRIVATE ${LOCAL_LIB_DIR})
target_compile_options(main PRIVATE -O3 -march=native)

# Define compile-time flags
#target_compile_definitions(main PRIVATE)

# Link libraries
target_link_libraries(main PRIVATE simdjson ixwebsocket ssl crypto z pthread)

