#!/bin/sh
if [ -d IXWebSocket ]; then
    echo "directory IXWebSocket exists"
    echo "for a clean build ..."
    echo "rm -rf IXWebSocket"
    exit
fi
INSTALLDIR=/workspace/install
mkdir -p $INSTALLDIR
git clone https://github.com/machinezone/IXWebSocket.git
cd IXWebSocket
mkdir -p build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$INSTALLDIR -DUSE_TLS=TRUE ..
make -j4
make install
