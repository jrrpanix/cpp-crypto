.PHONY: build-cpp build-full run-cpp run-full setup deps help

# Default help target
help:
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  build-cpp      Build the C++-only Docker image"
	@echo "  build-full     Build the full (C++ + Python) Docker image"
	@echo "  run-cpp        Launch cpp-dev Docker container"
	@echo "  run-full       Launch full-dev Docker container"
	@echo "  setup          Run full setup (build + launch + deps)"
	@echo "  deps           Install dependencies in container"
	@echo ""

build-cpp:
	./scripts/build_docker.sh cpp

build-full:
	./scripts/build_docker.sh full

run-cpp:
	./scripts/launch-dev.sh cpp

run-full:
	./scripts/launch-dev.sh full

setup:
	./scripts/setup_and_run.sh

deps:
	./scripts/install_deps.sh

