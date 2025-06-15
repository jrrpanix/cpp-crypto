cmake_minimum_required(VERSION 3.10)
project(SimdD)

if(NOT DEFINED PROJECT_SRC_DIR)
  set(PROJECT_SRC_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../..)
endif()

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Allow overriding via -D in CLI
set(LOCAL_INCLUDE_DIR "${CMAKE_SOURCE_DIR}/../../install/include" CACHE PATH "Local include path")
set(LOCAL_LIB_DIR "${CMAKE_SOURCE_DIR}/../../install/lib" CACHE PATH "Local lib path")

# Add binance_main executable
add_executable(binance_main binance_main.cpp)
target_include_directories(binance_main
  PRIVATE
  ${PROJECT_SRC_DIR}/src  
  ${CMAKE_CURRENT_SOURCE_DIR}/book_ticker
  ${LOCAL_INCLUDE_DIR}
)
target_link_directories(binance_main PRIVATE ${LOCAL_LIB_DIR})
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
  ${PROJECT_SRC_DIR}/src  
  ${CMAKE_CURRENT_SOURCE_DIR}/book_ticker
  ${LOCAL_INCLUDE_DIR}
)
target_link_directories(mock_binance_main PRIVATE ${LOCAL_LIB_DIR})
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
target_link_directories(mock_producer_main PRIVATE ${LOCAL_LIB_DIR})
target_include_directories(mock_producer_main
  PRIVATE
    ${PROJECT_SRC_DIR}/src
    ${LOCAL_INCLUDE_DIR}
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
            ${PROJECT_SRC_DIR}/src
            ${CMAKE_CURRENT_SOURCE_DIR}/book_ticker
            ${LOCAL_INCLUDE_DIR}
    )

    target_link_directories(${TEST_NAME} PRIVATE ${LOCAL_LIB_DIR})
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
