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
COMPOSE_FILE_2C := $(COMPOSE_DIR)/docker-compose-2-consumers.yml

# Use this to run commands inside the running dev container
DOCKER_EXEC := docker exec -it $(DEV_CONTAINER_NAME)
DOCKER_EXEC_CI := docker exec $(DEV_CONTAINER_NAME)

.PHONY: help build-dev run-dev shell-dev stop-dev deps build-code run-live rebuild-live stop-live run-test rebuild-test stop-test test

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
	@echo "  make run-test       Start the mock/test services using docker-compose"
	@echo "  make rebuild-test   Rebuild and start the mock/test services"
	@echo "  make stop-test      Stop the mock/test services"
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

# Run test services (mock data)
run-test:
	docker-compose -f $(COMPOSE_FILE_TEST) up

# Rebuild and run test services
rebuild-test:
	docker-compose -f $(COMPOSE_FILE_TEST) up --build

# Stop test services
stop-test:
	docker-compose -f $(COMPOSE_FILE_TEST) down

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


