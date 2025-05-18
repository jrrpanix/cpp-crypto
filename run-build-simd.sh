git clone https://github.com/simdjson/simdjson.git
cd simdjson && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/workspace/install ..
make -j2
make install

