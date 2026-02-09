# ==============================================================================
# cpp-crypto Makefile - Simplified
# ==============================================================================
SHELL := /bin/bash

# Load environment variables from .env file
-include .env
export

# Docker configuration
DEV_IMAGE := cpp-crypto-dev
DEV_CONTAINER := cpp-crypto-dev-container
COMPOSE_DIR := docker/compose

# Shortcuts for running commands in dev container
EXEC := docker exec -it $(DEV_CONTAINER)

.PHONY: help dev stop backtest websocket logs format test rebuild clean

# ==============================================================================
# Help - Show available commands
# ==============================================================================
help:
	@echo ""
	@echo "🚀 cpp-crypto Makefile"
	@echo "================================================================"
	@echo ""
	@echo "Essential Commands:"
	@echo "  make dev         Build & start dev container, drop into shell"
	@echo "  make stop        Stop all running containers"
	@echo "  make backtest    Run backtest webapp (port 8084)"
	@echo "  make websocket   Run websocket server (port 8082)"
	@echo "  make logs        View logs from running services"
	@echo "  make format      Format Python code"
	@echo "  make test        Run tests"
	@echo "  make rebuild     Rebuild dev container from scratch"
	@echo "  make clean       Stop everything and remove volumes"
	@echo ""
	@echo "Inside Dev Container:"
	@echo "  bash scripts/monthly_data_update.sh    # Update monthly data"
	@echo "  cd cpp/src/binance && make             # Build C++ code"
	@echo "  uv run python python/research/...      # Run Python scripts"
	@echo ""


# ==============================================================================
# Development Environment
# ==============================================================================

# One command to rule them all - build, start, and enter dev container
dev:
	@echo "🔧 Setting up development environment..."
	@if ! docker images -q $(DEV_IMAGE) | grep -q .; then \
		echo "📦 Building dev image (first time)..."; \
		docker build -t $(DEV_IMAGE) -f docker/Dockerfile.dev .; \
	fi
	@if ! docker ps -q -f name=$(DEV_CONTAINER) | grep -q .; then \
		echo "🚀 Starting dev container..."; \
		if [ -z "$(DATA_DIR)" ]; then \
			docker run -d --rm -v .:/workspace --name $(DEV_CONTAINER) $(DEV_IMAGE) sleep infinity; \
		else \
			docker run -d --rm -v .:/workspace -v $(DATA_DIR):/workspace/data --name $(DEV_CONTAINER) $(DEV_IMAGE) sleep infinity; \
		fi; \
	fi
	@echo "✅ Entering dev container (type 'exit' to leave)..."
	@$(EXEC) /bin/bash

# Stop all containers
stop:
	@echo "🛑 Stopping all containers..."
	@docker stop $(DEV_CONTAINER) 2>/dev/null || true
	@docker compose -f $(COMPOSE_DIR)/backtest.yml down 2>/dev/null || true
	@docker compose -f $(COMPOSE_DIR)/websocket.yml down 2>/dev/null || true
	@docker compose -f $(COMPOSE_DIR)/live-websocket.yml down 2>/dev/null || true
	@echo "✅ All containers stopped"

# Force rebuild dev container
rebuild:
	@echo "🔨 Rebuilding dev container..."
	@docker stop $(DEV_CONTAINER) 2>/dev/null || true
	@docker rmi $(DEV_IMAGE) 2>/dev/null || true
	@docker build -t $(DEV_IMAGE) -f docker/Dockerfile.dev .
	@echo "✅ Rebuild complete. Run 'make dev' to start."


# ==============================================================================
# WebSocket Services (Test Data)
# ==============================================================================

# Start the direct WebSocket services (consumer WebSocket + static frontend)
run-websocket:
	@echo "🚀 Starting direct WebSocket services (no FastAPI)..."
	docker-compose -f $(COMPOSE_FILE_WEBSOCKET) up -d --build

# Services
# ==============================================================================

# Start backtest webapp (port 8084)
backtest:
	@echo "🧪 Starting backtest webapp..."
	@DATA_DIR=$(shell cd ~/github && pwd)/data docker compose -f $(COMPOSE_DIR)/backtest.yml up -d --build
	@echo "✅ Backtest running at http://localhost:8084"

# Start websocket server (port 8082)
websocket:
	@echo "📡 Starting websocket server..."
	@docker compose -f $(COMPOSE_DIR)/websocket.yml up -d --build
	@echo "✅ Websocket running at http://localhost:8082"

# View logs from running services
logs:
	@echo "📋 Showing logs (Ctrl+C to exit)..."
	@docker compose -f $(COMPOSE_DIR)/backtest.yml logs -f 2>/dev/null || \
	 docker compose -f $(COMPOSE_DIR)/websocket.yml logs -f 2>/dev/null || \
	 echo "No services running"

# ==============================================================================
# Code Quality
# ==============================================================================

# Format Python code
format:
	@echo "🎨 Formatting Python code..."
	@if command -v docker >/dev/null 2>&1 && docker ps | grep -q $(DEV_CONTAINER); then \
		$(EXEC) bash -c "cd python && uv sync --extra dev && uv run black ."; \
	elif [ -f /.dockerenv ]; then \
		cd python && uv sync --extra dev && uv run black .; \
	else \
		echo "⚠️  Dev container not running. Start with 'make dev' first."; \
	fi

# Run tests
test:
	@echo "🧪 Running C++ tests..."
	@if command -v docker >/dev/null 2>&1 && docker ps | grep -q $(DEV_CONTAINER); then \
		$(EXEC) bash -c "cd cpp/src/binance && ./build_local.sh && cd build && ./test_simd_parser ../test_data/sample.json && ./test_json_times ../test_data/sample.json && ./test_lookup && ./test_clock_time"; \
	elif [ -f /.dockerenv ]; then \
		cd cpp/src/binance && ./build_local.sh && cd build && ./test_simd_parser ../test_data/sample.json && ./test_json_times ../test_data/sample.json && ./test_lookup && ./test_clock_time; \
	else \
		echo "⚠️  Dev container not running. Start with 'make dev' first."; \
	fi

# ==============================================================================
# Cleanup
# ==============================================================================

# Remove everything and clean up
clean:
	@echo "🧹 Cleaning up..."
	@docker compose -f $(COMPOSE_DIR)/backtest.yml down -v 2>/dev/null || true
	@docker compose -f $(COMPOSE_DIR)/websocket.yml down -v 2>/dev/null || true
	@docker compose -f $(COMPOSE_DIR)/live-websocket.yml down -v 2>/dev/null || true
	@docker stop $(DEV_CONTAINER) 2>/dev/null || true
	@echo "✅ Cleanup complete