# Help: list all available make targets
help:
	@echo ""
	@echo "📦 Makefile Commands:"
	@echo "  build        Build Docker image for development"
	@echo "  run          Run the Docker development container"
	@echo "  deps         Install C++ dependencies inside the container"
	@echo "  build_code   Compile the Binance C++ engine"
	@echo ""

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
	./scripts/build/consumer_build.sh

