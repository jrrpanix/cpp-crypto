# Help: list all available make targets
help:
	@echo ""
	@echo "📦 Makefile Commands:"
	@echo ""
	@echo "🛠️  Build + Run:"
	@echo "  build          Build Docker image for development"
	@echo "  run            Run the Docker development container"
	@echo "  deps           Install C++ dependencies inside the container"
	@echo "  build_code     Compile the Binance C++ engine"
	@echo ""
	@echo "🐳 Docker Compose:"
	@echo "  run_local      Start all services using docker-compose"
	@echo "  rebuild_local  Rebuild and start all services"
	@echo "  build_local    Rebuild docker images only (no run)"
	@echo "  reset_local    Stop and remove all containers/networks"
	@echo "  full_reset     Full clean: down + remove volumes + rebuild"
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

# Docker Compose Targets
run_local:
	docker-compose up

rebuild_local:
	docker-compose up --build

build_local:
	docker-compose build

reset_local:
	docker-compose down

full_reset:
	docker-compose down --volumes --remove-orphans
	docker-compose up --build

