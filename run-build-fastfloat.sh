git clone https://github.com/fastfloat/fast_float.git
cd fast_float && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=/workspace/install ..
make -j2
make install

