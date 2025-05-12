cmake_minimum_required(VERSION 3.10)

# Set project name and language
project(TestProgram LANGUAGES CXX)

# Set C++ standard (optional but recommended)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Add the executable target
add_executable(test test.cpp)

