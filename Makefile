# ==============================================================================
# Variables
# ==============================================================================
SHELL := /bin/bash

# Load environment variables from .env file if it exists
-include .env
export

# Docker image and container names
DEV_IMAGE_NAME := cpp-crypto-dev
DEV_CONTAINER_NAME := cpp-crypto-dev-container

# Docker Compose file paths
COMPOSE_DIR := docker
COMPOSE_FILE_WEBSOCKET := $(COMPOSE_DIR)/docker-compose-websocket.yml
COMPOSE_FILE_LIVE_WEBSOCKET := $(COMPOSE_DIR)/docker-compose-live-websocket.yml
COMPOSE_FILE_BACKTEST := $(COMPOSE_DIR)/docker-compose-backtest.yml
COMPOSE_FILE_2C := $(COMPOSE_DIR)/docker-compose-2-consumers.yml

# Use this to run commands inside the running dev container
DOCKER_EXEC := docker exec -it $(DEV_CONTAINER_NAME)
DOCKER_EXEC_CI := docker exec $(DEV_CONTAINER_NAME)

.PHONY: help build-dev run-dev shell-dev stop-dev deps build-code run-websocket rebuild-websocket stop-websocket run-live-websocket rebuild-live-websocket stop-live-websocket run-backtest rebuild-backtest stop-backtest test

# ==============================================================================
# Help Target
# ==============================================================================
help:
	@echo ""
	@echo "📦 cpp-crypto Makefile"
	@echo "------------------------------------------------------------------------------"
	@echo ""
	@echo "--- Development Environment ---"
	@echo "  make build-dev      Build the main development Docker image ($(DEV_IMAGE_NAME))"
	@echo "  make run-dev        Run the development container in the background"
	@echo "  make shell-dev      Get a shell inside the running development container"
	@echo "  make stop-dev       Stop and remove the development container"
	@echo ""
	@echo "--- In-Container Build Commands ---"
	@echo "  make deps           Install C++ third-party dependencies inside the dev container"
	@echo "  make build-code     Compile all C++ applications inside the dev container"
	@echo ""
	@echo "--- Python Code Quality ---"
	@echo "  make py-format      Format Python code with Black"
	@echo "  make py-lint        Lint Python code with Ruff"
	@echo "  make py-check       Check Python formatting and linting (no changes)"
	@echo "  make py-test        Run Python tests"
	@echo "  make py-all         Format, lint, and test Python code"
	@echo ""
	@echo "--- WebSocket Services (Test Data) ---"
	@echo "  make run-websocket         Start consumer→WebSocket→frontend (TEST data, port 8082)"
	@echo "  make run-websocket-verbose Start WebSocket services with output"
	@echo "  make rebuild-websocket     Rebuild and start WebSocket services"
	@echo "  make logs-websocket        View logs from WebSocket services"
	@echo "  make status-websocket      Check status of WebSocket services"
	@echo "  make stop-websocket        Stop WebSocket services"
	@echo "  make clean-websocket       Remove containers, networks, volumes"
	@echo ""
	@echo "--- Live WebSocket Services (Real Binance Data) ---"
	@echo "  make run-live-websocket         Start LIVE Binance→WebSocket→frontend (port 8083)"
	@echo "  make run-live-websocket-verbose Start LIVE services with output"
	@echo "  make rebuild-live-websocket     Rebuild and start LIVE WebSocket services"
	@echo "  make logs-live-websocket        View logs from LIVE WebSocket services"
	@echo "  make status-live-websocket      Check status of LIVE WebSocket services"
	@echo "  make stop-live-websocket        Stop LIVE WebSocket services"
	@echo "  make clean-live-websocket       Remove containers, networks, volumes"
	@echo ""
	@echo "--- Backtest Webapp Services ---"
	@echo "  make run-backtest         Start backtest webapp (Flask API + frontend, port 8084)"
	@echo "  make run-backtest-verbose Start backtest services with output"
	@echo "  make rebuild-backtest     Rebuild and start backtest services"
	@echo "  make logs-backtest        View logs from backtest services"
	@echo "  make status-backtest      Check status of backtest services"
	@echo "  make stop-backtest        Stop backtest services"
	@echo "  make clean-backtest       Remove containers, networks, volumes"
	@echo ""
	@echo "--- Testing ---"
	@echo "  make test           Run all C++ tests inside the container"


# ==============================================================================
# Development Environment
# ==============================================================================

# Build the main development image from our new Dockerfile.dev
build-dev:
	docker build -t $(DEV_IMAGE_NAME) -f $(COMPOSE_DIR)/Dockerfile.dev .

# Run the development container, mounting the current directory and external data
run-dev:
	docker run -d --rm \
		-v .:/workspace \
		-v $(DATA_DIR):/workspace/data:ro \
		--name $(DEV_CONTAINER_NAME) \
		$(DEV_IMAGE_NAME) sleep infinity

# Get a shell inside the running development container
shell-dev:
	$(DOCKER_EXEC) /bin/bash

# Stop and remove the development container
stop-dev:
	docker stop $(DEV_CONTAINER_NAME)


# ==============================================================================
# In-Container Build Commands
# ==============================================================================

# Install C++ dependencies inside the container
deps:
	$(DOCKER_EXEC_CI) ./scripts/install/deps_install.sh

# Build all C++ applications inside the container
build-code:
	$(DOCKER_EXEC_CI) ./scripts/build/binance_build.sh
	$(DOCKER_EXEC_CI) ./scripts/build/consumer_build.sh


# ==============================================================================
# WebSocket Services (Test Data)
# ==============================================================================

# Start the direct WebSocket services (consumer WebSocket + static frontend)
run-websocket:
	@echo "🚀 Starting direct WebSocket services (no FastAPI)..."
	docker-compose -f $(COMPOSE_FILE_WEBSOCKET) up -d --build

# Start the direct WebSocket services with output visible
run-websocket-verbose:
	@echo "🚀 Starting direct WebSocket services with output..."
	docker-compose -f $(COMPOSE_FILE_WEBSOCKET) up --build

# Rebuild and start the direct WebSocket services
rebuild-websocket:
	docker-compose -f $(COMPOSE_FILE_WEBSOCKET) down && docker-compose -f $(COMPOSE_FILE_WEBSOCKET) up -d --build

# View logs from running WebSocket services
logs-websocket:
	docker-compose -f $(COMPOSE_FILE_WEBSOCKET) logs -f

# Check status of WebSocket services
status-websocket:
	docker-compose -f $(COMPOSE_FILE_WEBSOCKET) ps

# Stop WebSocket services
stop-websocket:
	docker-compose -f $(COMPOSE_FILE_WEBSOCKET) down

# Clean WebSocket services (remove containers, networks, volumes)
clean-websocket:
	docker-compose -f $(COMPOSE_FILE_WEBSOCKET) down -v --remove-orphans

# ==============================================================================
# Live WebSocket Services (Real Binance + WebSocket Frontend)
# ==============================================================================

# Start live WebSocket services (real Binance data + WebSocket frontend)
run-live-websocket:
	@echo "🚀 Starting LIVE WebSocket services (real Binance data)..."
	docker-compose -f $(COMPOSE_FILE_LIVE_WEBSOCKET) up -d --build

# Start live WebSocket services with output visible
run-live-websocket-verbose:
	@echo "🚀 Starting LIVE WebSocket services with output..."
	docker-compose -f $(COMPOSE_FILE_LIVE_WEBSOCKET) up --build

# Rebuild and start live WebSocket services
rebuild-live-websocket:
	docker-compose -f $(COMPOSE_FILE_LIVE_WEBSOCKET) down && docker-compose -f $(COMPOSE_FILE_LIVE_WEBSOCKET) up -d --build

# View logs from live WebSocket services
logs-live-websocket:
	docker-compose -f $(COMPOSE_FILE_LIVE_WEBSOCKET) logs -f

# Check status of live WebSocket services
status-live-websocket:
	docker-compose -f $(COMPOSE_FILE_LIVE_WEBSOCKET) ps

# Stop live WebSocket services
stop-live-websocket:
	docker-compose -f $(COMPOSE_FILE_LIVE_WEBSOCKET) down

# Clean live WebSocket services
clean-live-websocket:
	docker-compose -f $(COMPOSE_FILE_LIVE_WEBSOCKET) down -v --remove-orphans

# ==============================================================================
# Backtest Webapp Services (Strategy Analysis)
# ==============================================================================

# Start backtest webapp services (Flask API + static frontend)
run-backtest:
	@echo "🚀 Starting backtest webapp (Flask API + frontend on port 8084)..."
	docker-compose -f $(COMPOSE_FILE_BACKTEST) up -d --build

# Start backtest services with output visible
run-backtest-verbose:
	@echo "🚀 Starting backtest webapp with output..."
	docker-compose -f $(COMPOSE_FILE_BACKTEST) up --build

# Rebuild and start backtest services
rebuild-backtest:
	docker-compose -f $(COMPOSE_FILE_BACKTEST) down && docker-compose -f $(COMPOSE_FILE_BACKTEST) up -d --build

# View logs from backtest services
logs-backtest:
	docker-compose -f $(COMPOSE_FILE_BACKTEST) logs -f

# Check status of backtest services
status-backtest:
	docker-compose -f $(COMPOSE_FILE_BACKTEST) ps

# Stop backtest services
stop-backtest:
	docker-compose -f $(COMPOSE_FILE_BACKTEST) down

# Clean backtest services
clean-backtest:
	docker-compose -f $(COMPOSE_FILE_BACKTEST) down -v --remove-orphans

# ==============================================================================
# Testing
# ==============================================================================

# Run all C++ tests inside the container
test:
	$(DOCKER_EXEC_CI) ./scripts/run_tests.sh


# ==============================================================================
# Python Code Quality
# ==============================================================================

# Format Python code with Black
py-format:
	@echo "🎨 Formatting Python code with Black..."
	$(DOCKER_EXEC_CI) black src/research server

# Lint Python code with Ruff
py-lint:
	@echo "🔍 Linting Python code with Ruff..."
	$(DOCKER_EXEC_CI) ruff check --fix src/research server

# Check Python formatting and linting without making changes
py-check:
	@echo "✅ Checking Python code formatting..."
	$(DOCKER_EXEC_CI) black --check src/research server
	@echo "✅ Checking Python code linting..."
	$(DOCKER_EXEC_CI) ruff check src/research server

# Run Python tests
py-test:
	@echo "🧪 Running Python tests..."
	@if $(DOCKER_EXEC_CI) bash -c "[ -d 'src/research/tests' ] && [ -n \"\$$(ls -A src/research/tests/test_*.py 2>/dev/null)\" ]"; then \
		$(DOCKER_EXEC_CI) pytest src/research/tests; \
	else \
		echo "⚠️  No tests found in src/research/tests"; \
	fi

# Run all Python quality checks
py-all: py-format py-lint py-test
	@echo "✨ Python code quality checks complete!"


