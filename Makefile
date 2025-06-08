.PHONY: build_image_cpp build_image_full launch_docker_cpp launch_docker_full install_deps build_code help

# Default help target
help:
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  build_image_cpp       build the C++-only Docker image, large footprint "
	@echo "  build_image_full      build the full (C++ + Python) Docker image, largefoot print"
	@echo "  build_image_runtime   build the Runtime Docker image, smaller footprint "
	@echo "  launch_docker_cpp     launch cpp-dev Docker container"
	@echo "  launch_docker_full    launch full-dev Docker container"
	@echo "  launch_docker_runtime run runtime docker image"
	@echo "  install_deps          Install dependencies in container"
	@echo "  build_code            build Binance C++ Code"
	@echo ""

# Build C++ Docker image
build_image_cpp:
	./scripts/build/docker_build.sh cpp

# Build full C++ + Python Docker image
build_image_full:
	./scripts/build/docker_build.sh full

# Build Runtime  Docker image
build_image_runtime:
	./scripts/build/docker_build.sh runtime

# Run C++ dev container
launch_docker_cpp:
	./scripts/run/run_image.sh cpp

# Run full C++ + Python dev container
launch_docker_full:
	./scripts/run/run_image.sh full

# Run full C++ + Python dev container
launch_docker_runtime:
	./scripts/run/run_image.sh runtime

# Install dependencies
install_deps:
	./scripts/install/deps_install.sh

# Build C++ code
build_code:
	./scripts/build/binance_build.sh
