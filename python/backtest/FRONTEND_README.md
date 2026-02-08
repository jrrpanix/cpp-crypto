# Frontend Applications

This directory contains the web-based user interfaces for the crypto trading system. All frontends use vanilla JavaScript with no build steps or complex frameworks.

## Applications

### 1. Backtest Webapp (`backtest/`)
Strategy backtesting interface for testing window-based trading strategies on historical data.

**Features:**
- Multi-parameter testing with table-based input
- Run multiple backtests simultaneously
- Compare results side-by-side
- Performance metrics: PnL, ROI, Sharpe, win rate, etc.
- Visual PnL charts with modal viewing

**Access:** `http://localhost:8084` (via `make run-backtest`)

### 2. Real-time Monitoring (`realtime/`)
WebSocket-based real-time market data monitoring dashboard.

**Features:**
- Live price updates via WebSocket
- Real-time trade data display
- System metrics and logs
- Multiple views: direct, table, dashboard

**Access:** 
- Test data: `http://localhost:8082` (via `make run-websocket`)
- Live Binance: `http://localhost:8083` (via `make run-live-websocket`)

## File Structure

```
frontend/
├── backtest/           # Strategy backtesting webapp
│   ├── index.html      # Main UI with parameter table
│   ├── backtest.js     # API integration and logic
│   └── README_BACKTEST.md
├── realtime/           # Real-time monitoring dashboards
│   ├── index.html      # Main WebSocket dashboard
│   ├── direct.html     # Direct WebSocket view
│   ├── dashboard.html  # Enhanced dashboard view
│   ├── app.js         # WebSocket client logic
│   ├── websocket-direct.js
│   └── table.js
└── README.md          # This file
```

## Technology Stack

- **Frontend**: Pure vanilla JavaScript, HTML5, CSS3
- **Backend API (Backtest)**: Flask 3.0+ with Flask-CORS
- **Backend API (Realtime)**: C++ WebSocket server
- **Python Environment**: Managed with `uv` and `pyproject.toml`
- **No Build Steps**: Direct file serving via Docker or nginx

## Quick Start

### Backtest Webapp
```bash
# Start the backtest services
make run-backtest

# Access the webapp
open http://localhost:8084

# Stop when done
make stop-backtest
```

### Real-time Monitoring
```bash
# Test with mock data
make run-websocket
open http://localhost:8082

# Or use live Binance data
make run-live-websocket
open http://localhost:8083

# Stop services
make stop-websocket
make stop-live-websocket
```

## Backend Services

### Backtest API (Flask)
- **Technology**: Flask 3.0+ with Flask-CORS
- **Dependencies**: Managed via `pyproject.toml` and `uv`
- **Location**: `server/backtest_api.py`
- **Port**: 5001 (internal), 8084 (external via nginx)

**Setup:**
```bash
# Dependencies are installed automatically via Docker
# using uv from pyproject.toml

# Manual installation (if needed):
uv pip install --system flask flask-cors polars matplotlib pyarrow
```

### Real-time WebSocket Server
- **Technology**: C++ WebSocket server
- **Data Flow**: Producer → ZMQ → Consumer → WebSocket → Frontend
- **Port**: 9002 (WebSocket), 8082/8083 (HTTP via nginx)

## Development

All services use Docker with live volume mounts for development:

```bash
# Changes to frontend files are reflected immediately (no rebuild needed)
# Backend changes require container restart:
make rebuild-backtest      # For Flask API changes
make rebuild-websocket     # For C++ changes
```

## API Endpoints

### Backtest API
- `GET /api/symbols` - List available symbols
- `GET /api/symbol-info/<symbol>` - Symbol metadata
- `POST /api/backtest` - Run backtest with parameters

### Real-time WebSocket
- `WebSocket /ws` - Real-time data stream (JSON messages)
- Automatic reconnection on disconnect
- Direct C++ to browser, no middleware

## Design Philosophy

- **No Build Steps**: Pure vanilla JavaScript, edit and refresh
- **No Frameworks**: No React, Vue, or Angular complexity
- **Container-First**: All services run in Docker for consistency
- **Modern Tooling**: Python managed with `uv` (fast, reliable)
- **Separation of Concerns**: Backtest vs Real-time apps isolated

## Customization

Easily customizable:
- Edit HTML/CSS/JS directly in the respective directories
- No transpilation or bundling required
- Changes visible immediately with volume mounts
- All styling inline or in `<style>` tags for simplicity