mkdir build && cd build
cmake .. -DLOCAL_INCLUDE_DIR=/workspace/install/include -DLOCAL_LIB_DIR=/workspace/install/lib -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_BUILD_TYPE=Release
make

