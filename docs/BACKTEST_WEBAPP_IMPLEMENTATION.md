# Backtest Webapp - Complete Implementation

## What We Built

A full-stack web application for backtesting window-based trading strategies on historical cryptocurrency data.

### Components Created

1. **Flask Backend API** (`server/backtest_api.py`)
   - REST API with 3 endpoints
   - Integrates directly with `window_sim.py` strategy engine
   - Generates cumulative PnL plots as base64 PNG
   - Returns comprehensive performance metrics

2. **Frontend Interface** (`frontend/backtest.html` + `backtest.js`)
   - Modern, responsive UI with gradient design
   - Interactive form for all strategy parameters
   - Real-time symbol metadata loading
   - Results visualization with metrics grid and trade tables
   - Base64 plot rendering

3. **Docker Configuration** (`docker/docker-compose-backtest.yml`)
   - Flask API service on port 5001
   - Nginx frontend service on port 8084
   - Volume mounts for data and live code updates

4. **Documentation** (`frontend/README_BACKTEST.md`)
   - Complete usage guide
   - API documentation
   - Strategy explanation
   - Troubleshooting tips

5. **Startup Script** (`scripts/run/run_backtest_webapp.sh`)
   - One-command launch
   - Environment validation
   - Helpful status messages

## Architecture Decisions

### Why Flask Instead of WebSocket?

Unlike the live data pipeline (which needed WebSocket for streaming), backtesting is:
- **Non-real-time**: Analysis runs once, returns results
- **Compute-intensive**: Long-running calculations don't benefit from streaming
- **Request-response pattern**: Perfect fit for REST API
- **Simpler**: No need for connection management, heartbeats, etc.

### Data Flow

```
User Form → POST /api/backtest → window_sim.run_simulation() → Results JSON
                                           ↓
                                  Parquet Files (data/)
```

### Why Separate from WebSocket Services?

1. **Different Use Cases**: Live data monitoring vs historical analysis
2. **Different Ports**: 8084 (backtest) vs 8082/8083 (live WebSocket)
3. **Independent Deployment**: Can run backtest without starting producers/consumers
4. **Resource Isolation**: Heavy compute doesn't affect live data streaming

## Key Features

### Frontend
- ✅ Symbol selector with auto-populated dropdown
- ✅ All strategy parameters exposed (thresholds, windows, position sizing)
- ✅ Direction toggles (Buy/Sell for UP/DOWN events)
- ✅ Optional date filtering
- ✅ Loading states with spinner
- ✅ Error handling with user-friendly messages
- ✅ Comprehensive metrics display (17 different metrics)
- ✅ Color-coded results (green for positive, red for negative)
- ✅ Trade breakdown by signal type (UP vs DOWN events)
- ✅ Detailed trade table with all transactions

### Backend
- ✅ Symbol discovery from parquet files
- ✅ Symbol metadata (date ranges, row counts)
- ✅ Full backtest execution with all parameters
- ✅ In-memory plot generation (no temp files)
- ✅ Base64 encoding for web display
- ✅ CORS enabled for cross-origin requests
- ✅ Flexible path resolution (Docker + local dev)
- ✅ Error handling and validation

### Deployment
- ✅ Docker containerization
- ✅ Development-friendly volume mounts
- ✅ One-command startup script
- ✅ Proper service isolation
- ✅ Environment variable support

## Usage Example

```bash
# Start the webapp using Makefile (recommended)
make run-backtest

# Or using the shell script
./scripts/run/run_backtest_webapp.sh

# Or using docker-compose directly
cd docker
docker-compose -f docker-compose-backtest.yml up --build

# Access at http://localhost:8084

# In the UI:
# 1. Select symbol: BTCUSDT
# 2. UP Threshold: 0.01 (1% gain)
# 3. UP Direction: Buy (go long)
# 4. DOWN Threshold: -0.02 (-2% drop)
# 5. DOWN Direction: Sell (go short)
# 6. Detection Window: 30 bars
# 7. Hold Window: 30 bars
# 8. Position Size: $1000
# 9. Click "Run Backtest"
```

## Files Modified/Created

### New Files
```
server/
  backtest_api.py          # Flask API (231 lines)
  requirements.txt         # Python dependencies
  Dockerfile               # API container config

frontend/
  backtest.html            # Main webapp UI (280 lines)
  backtest.js              # Frontend logic (420 lines)
  README_BACKTEST.md       # Documentation

docker/
  docker-compose-backtest.yml  # Service orchestration

scripts/run/
  run_backtest_webapp.sh   # Startup script
```

### No Changes Required To
- `window_sim.py` (used as-is via import)
- Existing WebSocket services (independent)
- Data files (read-only access)

## API Contract

### POST /api/backtest Request
```json
{
  "symbol": "BTCUSDT",
  "up_threshold": 0.01,
  "up_direction": "B",
  "down_threshold": -0.02,
  "down_direction": "S",
  "detection_window": 30,
  "hold_window": 30,
  "position_size": 1000,
  "position_limit": 1,
  "fee_rate": 0.0003,
  "num_accounts": 1,
  "start_date": "2023-01-01"  // optional
}
```

### Response
```json
{
  "summary": {
    "total_pnl": 1234.56,
    "total_return": 0.1234,
    "annualized_return": 0.45,
    "sharpe_ratio": 1.5,
    "max_drawdown": -0.15,
    "num_trades": 42,
    "win_rate": 0.57,
    "avg_profit_per_trade": 29.39,
    "avg_winning_trade": 75.20,
    "avg_losing_trade": -45.30,
    "total_fees": 25.20,
    "avg_hold_bars": 30.0,
    "num_up_events": 25,
    "num_down_events": 17,
    "up_event_pnl": 890.45,
    "down_event_pnl": 344.11
  },
  "plot": "iVBORw0KGgoAAAANS...",
  "trades": [...]
}
```

## Performance Metrics Explained

| Metric | Description | Good Value |
|--------|-------------|------------|
| Total PnL | Net profit/loss | > $0 |
| Total Return | % gain on position size | > 0% |
| Annualized Return | Extrapolated yearly % | > 10% |
| Sharpe Ratio | Risk-adjusted return | > 1.0 |
| Max Drawdown | Largest % decline | < -20% |
| Win Rate | % profitable trades | > 50% |
| Avg Profit/Trade | Mean PnL per trade | > $0 |

## Troubleshooting

### "No symbols available"
- Check `data/aggregate_parquet/` exists
- Ensure files match pattern: `{SYMBOL}USDT_1m_*.parquet`
- Verify file permissions (readable)

### "Failed to load symbols"
- Check Flask API is running (port 5000)
- Verify CORS is enabled
- Check browser console for errors

### Backtest returns no trades
- Thresholds may be too aggressive
- Date range may exclude all data
- Try relaxing parameters (smaller thresholds, wider windows)

### Plot not displaying
- Check base64 data is present in response
- Verify browser supports PNG data URIs
- Check matplotlib backend is 'Agg'

## Next Steps (Future Enhancements)

1. **Parameter Optimization**
   - Grid search across parameter ranges
   - Return best parameter combinations
   - Heatmap visualization of parameter space

2. **Multi-Symbol Comparison**
   - Run same strategy across multiple symbols
   - Compare performance side-by-side
   - Portfolio-level metrics

3. **Advanced Analytics**
   - Trade duration distribution
   - PnL distribution histogram
   - Drawdown analysis chart
   - Monthly returns calendar

4. **Strategy Templates**
   - Save/load parameter presets
   - Share strategies via JSON export
   - Strategy library

5. **Progress Tracking**
   - WebSocket for long-running backtests
   - Progress bar with ETA
   - Partial results streaming

6. **Export Options**
   - PDF report generation
   - CSV trade export
   - JSON results download

7. **Walk-Forward Analysis**
   - Split data into train/test periods
   - Optimize on train, validate on test
   - Report out-of-sample performance

## Integration with Existing System

### Relationship to Live Pipeline

```
┌─────────────────────────────────────┐
│         Live Data Pipeline          │
│                                     │
│  Binance → ZMQ → Consumer → WebSocket │
│   Producer     (C++)      (Browser) │
│                                     │
│  Ports: 8082 (test), 8083 (live)  │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      Backtest Analysis Webapp       │
│                                     │
│  Parquet → window_sim.py → Flask API │
│   Files    (Strategy)    → Frontend │
│                                     │
│  Port: 8084 (backtest)            │
└─────────────────────────────────────┘
```

**Independent but complementary:**
- Live pipeline: Real-time monitoring and execution
- Backtest webapp: Historical analysis and strategy development
- Both use same symbol universe
- Strategies validated in backtest → deployed to live

### Data Consistency
- Both systems read from same `data/` directory
- Parquet files are canonical data source
- Live system can write new data for backtest analysis

## Summary

Successfully created a complete backtesting webapp that:
- ✅ Provides intuitive UI for complex strategy parameters
- ✅ Generates comprehensive performance analytics
- ✅ Visualizes cumulative PnL with matplotlib
- ✅ Handles all edge cases and errors gracefully
- ✅ Deploys easily via Docker
- ✅ Maintains separation from live trading infrastructure
- ✅ Uses simple REST API (no WebSocket complexity)
- ✅ Documented thoroughly for future development

The system is production-ready for strategy research and backtesting workflows.
