.PHONY: build_cpp build_full run_cpp run_full setup deps help

# Default help target
help:
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  build_cpp      Build the C++-only Docker image"
	@echo "  build_full     Build the full (C++ + Python) Docker image"
	@echo "  run_cpp        Launch cpp-dev Docker container"
	@echo "  run_full       Launch full-dev Docker container"
	@echo "  setup          Run full setup (build + launch + deps)"
	@echo "  deps           Install dependencies in container"
	@echo ""

# Build C++ Docker image
build_cpp:
	./scripts/build/docker_build.sh cpp

# Build full C++ + Python Docker image
build_full:
	./scripts/build/docker_build.sh full

# Run C++ dev container
run_cpp:
	./scripts/run/run_image.sh cpp

# Run full C++ + Python dev container
run_full:
	./scripts/run/run_image.sh full

# Full setup (build + run + deps)
setup:
	./scripts/run/bootstrap.sh

# Install dependencies
deps:
	./scripts/install/deps_install.sh

