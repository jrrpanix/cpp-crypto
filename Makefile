# ==============================================================================
# Variables
# ==============================================================================
SHELL := /bin/bash

# Docker image and container names
DEV_IMAGE_NAME := cpp-crypto-dev
DEV_CONTAINER_NAME := cpp-crypto-dev-container

# Docker Compose file paths
COMPOSE_DIR := docker
COMPOSE_FILE := $(COMPOSE_DIR)/docker-compose.yml
COMPOSE_FILE_TEST := $(COMPOSE_DIR)/docker-compose-test.yml
COMPOSE_FILE_FAST_TEST := $(COMPOSE_DIR)/docker-compose-fast-test.yml
COMPOSE_FILE_WEBSOCKET := $(COMPOSE_DIR)/docker-compose-websocket.yml
COMPOSE_FILE_LIVE_WEBSOCKET := $(COMPOSE_DIR)/docker-compose-live-websocket.yml
COMPOSE_FILE_2C := $(COMPOSE_DIR)/docker-compose-2-consumers.yml

# Use this to run commands inside the running dev container
DOCKER_EXEC := docker exec -it $(DEV_CONTAINER_NAME)
DOCKER_EXEC_CI := docker exec $(DEV_CONTAINER_NAME)

.PHONY: help build-dev run-dev shell-dev stop-dev deps build-code run-live rebuild-live stop-live run-test rebuild-test stop-test run-fast-test rebuild-fast-test stop-fast-test run-websocket rebuild-websocket stop-websocket test

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
	@echo "--- Application Services (Live) ---"
	@echo "  make run-live       Start all live services using docker-compose"
	@echo "  make rebuild-live   Rebuild and start all live services"
	@echo "  make stop-live      Stop all live services"
	@echo ""
	@echo "--- Application Services (Test) ---"
	@echo "  make run-test       Start mock/test services (10 msg/sec, realistic)"
	@echo "  make run-test-verbose  Start the mock/test services with output"
	@echo "  make rebuild-test   Rebuild and start the mock/test services"
	@echo "  make logs-test      View logs from running test services"
	@echo "  make status-test    Check status of test services"
	@echo "  make stop-test      Stop the mock/test services"
	@echo ""
	@echo "--- Fast Test Services (High-Frequency) ---"
	@echo "  make run-fast-test  Start FAST mock/test services (50 msg/sec max, shocks)"
	@echo "  make run-fast-test-verbose  Start FAST services with output"
	@echo "  make rebuild-fast-test  Rebuild and start FAST services"
	@echo "  make logs-fast-test View logs from running FAST test services"
	@echo "  make status-fast-test  Check status of FAST test services"
	@echo "  make stop-fast-test Stop the FAST mock/test services"
	@echo ""
	@echo "--- Direct WebSocket Services (No FastAPI!) ---"
	@echo "  make run-websocket  Start direct consumer→WebSocket→frontend (TEST data)"
	@echo "  make run-websocket-verbose  Start WebSocket services with output"
	@echo "  make rebuild-websocket  Rebuild and start WebSocket services"
	@echo "  make logs-websocket View logs from WebSocket services"
	@echo "  make status-websocket  Check status of WebSocket services"
	@echo "  make stop-websocket Stop WebSocket services"
	@echo ""
	@echo "--- Live WebSocket Services (Real Binance!) ---"
	@echo "  make run-live-websocket  Start LIVE Binance→WebSocket→frontend (port 8083)"
	@echo "  make run-live-websocket-verbose  Start LIVE services with output"
	@echo "  make rebuild-live-websocket  Rebuild and start LIVE WebSocket services"
	@echo "  make logs-live-websocket View logs from LIVE WebSocket services"
	@echo "  make status-live-websocket  Check status of LIVE WebSocket services"
	@echo "  make stop-live-websocket Stop LIVE WebSocket services"
	@echo ""
	@echo "--- Testing ---"
	@echo "  make test           Run all C++ tests inside the container"


# ==============================================================================
# Development Environment
# ==============================================================================

# Build the main development image from our new Dockerfile.dev
build-dev:
	docker build -t $(DEV_IMAGE_NAME) -f $(COMPOSE_DIR)/Dockerfile.dev .

# Run the development container, mounting the current directory
run-dev:
	docker run -d --rm \
		-v .:/workspace \
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
# Application Services (Live)
# ==============================================================================

# Run live services
run-live:
	docker-compose -f $(COMPOSE_FILE) up

# Rebuild and run live services
rebuild-live:
	docker-compose -f $(COMPOSE_FILE) up --build

# Stop live services
stop-live:
	docker-compose -f $(COMPOSE_FILE) down


# ==============================================================================
# Application Services (Test)
# ==============================================================================

# Run test services (mock data) in background
run-test:
	@echo "🚀 Starting test services in background..."
	docker-compose -f $(COMPOSE_FILE_TEST) up -d
	@echo "✅ Test services running. Use 'make logs-test' to view output or 'make stop-test' to stop."

# Run test services with output (foreground)
run-test-verbose:
	docker-compose -f $(COMPOSE_FILE_TEST) up

# Rebuild and run test services
rebuild-test:
	docker-compose -f $(COMPOSE_FILE_TEST) up --build -d

# View logs from test services
logs-test:
	docker-compose -f $(COMPOSE_FILE_TEST) logs -f

# Check status of test services
status-test:
	docker-compose -f $(COMPOSE_FILE_TEST) ps

# Stop test services
stop-test:
	docker-compose -f $(COMPOSE_FILE_TEST) down

# ==============================================================================
# Fast Test Services (High-Frequency Replay)
# ==============================================================================

# Start the fast mock/test services in background (5ms throttle, 0.5% variation)
run-fast-test:
	@echo "🚀 Starting FAST mock/test services (high-frequency replay)..."
	docker-compose -f $(COMPOSE_FILE_FAST_TEST) up -d --build

# Start the fast mock/test services with output visible
run-fast-test-verbose:
	@echo "🚀 Starting FAST mock/test services (high-frequency replay) with output..."
	docker-compose -f $(COMPOSE_FILE_FAST_TEST) up --build

# Rebuild and start the fast mock/test services
rebuild-fast-test:
	docker-compose -f $(COMPOSE_FILE_FAST_TEST) down && docker-compose -f $(COMPOSE_FILE_FAST_TEST) up -d --build

# View logs from running fast test services
logs-fast-test:
	docker-compose -f $(COMPOSE_FILE_FAST_TEST) logs -f

# Check status of fast test services
status-fast-test:
	docker-compose -f $(COMPOSE_FILE_FAST_TEST) ps

# Stop fast test services
stop-fast-test:
	docker-compose -f $(COMPOSE_FILE_FAST_TEST) down

# ==============================================================================
# Direct WebSocket Services (No FastAPI Middleman)
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


