# Build Docker image for full development environment (C++ + Python)
build:
	./scripts/build/docker_build.sh full

# Run the full development container
run:
	./scripts/run/run_image.sh full

# Install dependencies inside container
deps:
	./scripts/install/deps_install.sh

# Build C++ engine
build_code:
	./scripts/build/binance_build.sh

