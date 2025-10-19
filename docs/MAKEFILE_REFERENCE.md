# Makefile Quick Reference

All services in this project are managed via the Makefile for consistency. Simply run `make help` to see all available commands.

## 🚀 Quick Start Commands

### Backtest Webapp (Strategy Analysis)
```bash
make run-backtest        # Start backtest webapp on port 8084
make logs-backtest       # View logs
make stop-backtest       # Stop services
```

### Live WebSocket (Real-Time Data)
```bash
make run-websocket           # Test mode with mock data (port 8082)
make run-live-websocket      # Live Binance data (port 8083)
make stop-websocket          # Stop test services
make stop-live-websocket     # Stop live services
```

### Development Environment
```bash
make build-dev          # Build Docker development image
make run-dev            # Start dev container in background
make shell-dev          # Get shell inside container
make build-code         # Compile all C++ applications
make stop-dev           # Stop dev container
```

## 📊 Service Overview

| Command | Port | Purpose | Data Source |
|---------|------|---------|-------------|
| `make run-backtest` | 8084 (UI), 5001 (API) | Strategy backtesting | Historical parquet files |
| `make run-websocket` | 8082 | Real-time monitoring | Mock test data |
| `make run-live-websocket` | 8083 | Real-time monitoring | Live Binance stream |

## 🛠️ Common Workflows

### Backtest a Trading Strategy
```bash
# 1. Start the webapp
make run-backtest

# 2. Open browser to http://localhost:8084

# 3. When done, stop services
make stop-backtest
```

### Watch Live Market Data
```bash
# Test with mock data first
make run-websocket
# Open: http://localhost:8082

# Then try live data
make run-live-websocket
# Open: http://localhost:8083

# Stop when done
make stop-websocket
make stop-live-websocket
```

### Develop C++ Code
```bash
# 1. Build and start dev environment
make build-dev
make run-dev

# 2. Get a shell
make shell-dev

# 3. Inside container, build your code
make build-code

# 4. Exit and stop when done
exit
make stop-dev
```

### Python Code Quality
```bash
# Format and lint Python code
make py-format
make py-lint

# Run Python tests
make py-test

# Do all Python checks
make py-all
```

## 📝 Service Control Patterns

All services follow the same pattern:

```bash
make run-{service}          # Start in background
make run-{service}-verbose  # Start with output visible
make logs-{service}         # View logs
make status-{service}       # Check status
make rebuild-{service}      # Rebuild and restart
make stop-{service}         # Stop services
make clean-{service}        # Remove containers/volumes (if available)
```

### Examples:
```bash
# Backtest webapp
make run-backtest
make logs-backtest
make stop-backtest

# WebSocket services
make run-websocket
make logs-websocket
make stop-websocket

# Fast test services
make run-fast-test
make logs-fast-test
make stop-fast-test
```

## 🔍 Troubleshooting

### Check what's running
```bash
docker ps
```

### View service status
```bash
make status-backtest
make status-websocket
make status-live-websocket
```

### View logs for debugging
```bash
make logs-backtest
make logs-websocket
make logs-live-websocket
```

### Clean up everything
```bash
make stop-backtest
make stop-websocket
make stop-live-websocket
make stop-dev
```

### Port conflicts
If you see port binding errors:
```bash
# Check what's using the port
lsof -i :8084    # For backtest frontend
lsof -i :5001    # For backtest API
lsof -i :8082    # For test WebSocket
lsof -i :8083    # For live WebSocket

# Stop conflicting services first
make stop-backtest
make stop-websocket
```

## 📚 Full Command Reference

Run `make help` to see all available commands with descriptions.

Key categories:
- **Development Environment**: build-dev, run-dev, shell-dev, stop-dev
- **Build Commands**: deps, build-code
- **Python Quality**: py-format, py-lint, py-check, py-test, py-all
- **Live Services**: run-live, rebuild-live, stop-live
- **Test Services**: run-test, rebuild-test, stop-test, logs-test
- **Fast Test**: run-fast-test, rebuild-fast-test, stop-fast-test
- **WebSocket**: run-websocket, rebuild-websocket, stop-websocket
- **Live WebSocket**: run-live-websocket, rebuild-live-websocket, stop-live-websocket
- **Backtest**: run-backtest, rebuild-backtest, stop-backtest, logs-backtest
- **Testing**: test

## 💡 Pro Tips

1. **Always use Makefile commands** instead of raw docker-compose for consistency
2. **Check status first** with `make status-{service}` before starting
3. **View logs** with `make logs-{service}` to debug issues
4. **Use verbose mode** (`make run-{service}-verbose`) when developing
5. **Stop services** when not in use to free up resources
6. **Rebuild** with `make rebuild-{service}` after code changes

## 🔗 Related Documentation

- Main README: `README.md`
- Architecture: `docs/ARCHITECTURE.md`
- Backtest Guide: `docs/BACKTEST_QUICKSTART.md`
- Python Setup: `docs/PYTHON_CI_SETUP.md`
