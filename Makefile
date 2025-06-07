.PHONY: build_cpp build_full run_cpp run_full deps build_code run_fut run_spot help

# Default help target
help:
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  build_cpp      Build the C++-only Docker image"
	@echo "  build_full     Build the full (C++ + Python) Docker image"
	@echo "  build_runtime  Build the Runtime Docker image"
	@echo "  run_cpp        Launch cpp-dev Docker container"
	@echo "  run_full       Launch full-dev Docker container"
	@echo "  run_runtime    run runtime docker image"
	@echo "  deps           Install dependencies in container"
	@echo "  build_code     Build Binance C++ Code"
	@echo "  run_fut        run Binance futures"
	@echo "  run_spot       run Binance spot"
	@echo ""

# Build C++ Docker image
build_cpp:
	./scripts/build/docker_build.sh cpp

# Build full C++ + Python Docker image
build_full:
	./scripts/build/docker_build.sh full

# Build Runtime  Docker image
build_runtime:
	./scripts/build/docker_build.sh runtime

# Run C++ dev container
run_cpp:
	./scripts/run/run_image.sh cpp

# Run full C++ + Python dev container
run_full:
	./scripts/run/run_image.sh full

# Run full C++ + Python dev container
run_runtime:
	./scripts/run/run_image.sh runtime

# Install dependencies
deps:
	./scripts/install/deps_install.sh

# Build C++ code
build_code:
	./scripts/build/binance_build.sh

run_fut:
	./binance/build/binance_main --config_file ./binance/config/config.json --key fut

run_spot:
	./binance/build/binance_main --config_file ./binance/config/config.json --key spot
