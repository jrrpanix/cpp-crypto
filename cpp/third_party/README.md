# Vendored Dependencies

This directory contains vendored (bundled) copies of third-party dependencies required for building this project.

## Purpose

These are complete copies of header files and compiled libraries to ensure the project can build **offline** and remains functional even if upstream projects become unavailable or are removed from the internet.

## Contents

- **Headers**: All `.h`, `.hpp` files needed for compilation
- **Libraries**: Precompiled `.a` (static) libraries
  - `libsimdjson.a` - SIMD JSON parser
  - `libixwebsocket.a` - WebSocket library
  - `libcpr.a` - HTTP client library

## Version Information

These vendored copies were synchronized from `/opt/cpp-crypto-deps` on **February 1, 2026** and correspond to the versions used in the CI environment.

## Build Process

The CMakeLists.txt uses a two-tier strategy:

1. **CI builds** (preferred): Use `/opt/cpp-crypto-deps` for potentially newer/optimized versions
2. **Offline/fallback**: Automatically use `/workspace/third_party` if CI dependencies unavailable

## Updating Vendored Dependencies

To update these vendored copies with newer versions:

```bash
# From the binance build directory
cp -r /opt/cpp-crypto-deps/include/* ../../third_party/
cp -r /opt/cpp-crypto-deps/lib/* ../../third_party/lib/
```

Then commit the changes to git.

## Testing Offline Build

To verify the vendored dependencies work:

```bash
cd src/realtime/binance
chmod +x test_build_vendored.sh
sudo mv /opt/cpp-crypto-deps /tmp/cpp-crypto-deps-backup
./test_build_vendored.sh
sudo mv /tmp/cpp-crypto-deps-backup /opt/cpp-crypto-deps
```

This ensures your project is resilient and buildable anywhere, anytime.
