#!/bin/sh
export UV_LINK_MODE=copy
uv sync
uv run python generate_symbol_files.py
gperf symbol_keywords.gperf > symbol_lookup.hpp
g++ -std=c++17 -O3 benchmark.cpp -o bench -I ../install/include
