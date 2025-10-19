# Backtest Webapp

Web-based interface for the window_sim.py trading strategy backtesting tool.

## Overview

This webapp provides an easy-to-use interface for testing window-based trading strategies on historical cryptocurrency data. Define event thresholds, hold periods, and position parameters through a web form, then view cumulative PnL charts and comprehensive performance metrics.

## Architecture

- **Backend**: Flask API server (`server/backtest_api.py`)
- **Frontend**: Static HTML/JS (`frontend/backtest.html`, `frontend/backtest.js`)
- **Data**: Parquet files from `data/aggregate_parquet/`
- **Engine**: `window_sim.py` strategy simulator

## Quick Start

### Docker (Recommended)

```bash
# Build and start services
cd docker
docker-compose -f docker-compose-backtest.yml up --build

# Access webapp at http://localhost:8084
```

### Local Development

```bash
# Terminal 1: Start Flask API
cd server
pip install -r requirements.txt
python backtest_api.py

# Terminal 2: Serve frontend
cd frontend
python -m http.server 8084

# Access webapp at http://localhost:8084/backtest.html
# API runs on http://localhost:5000
```

## Strategy Logic

The window-based strategy works as follows:

1. **Detection Window**: Monitor price changes over N bars
2. **Thresholds**: Define UP (+X%) and DOWN (-Y%) movement triggers
3. **Direction**: Choose to go LONG or SHORT when threshold hit
4. **Hold Period**: Maintain position for specified number of bars
5. **Position Management**: Limit concurrent positions (1 or 2 accounts)

### Example Strategy

"BTC 0.01 B -0.02 S 30 30" means:
- Symbol: BTCUSDT
- If price rises +1% in 30 bars → BUY (go long)
- If price drops -2% in 30 bars → SELL (go short)
- Hold each position for 30 bars

## API Endpoints

### GET /api/symbols
Returns list of available trading symbols from parquet files.

**Response:**
```json
{
  "symbols": ["BTCUSDT", "ETHUSDT", ...]
}
```

### GET /api/symbol-info/<symbol>
Returns date range and row count for a specific symbol.

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "date_range": {
    "min": "2023-01-01",
    "max": "2024-01-01"
  },
  "row_count": 525600
}
```

### POST /api/backtest
Run backtest simulation with specified parameters.

**Request:**
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

**Response:**
```json
{
  "summary": {
    "total_pnl": 1234.56,
    "total_return": 0.1234,
    "sharpe_ratio": 1.5,
    "max_drawdown": -0.15,
    "num_trades": 42,
    "win_rate": 0.57,
    "avg_profit_per_trade": 29.39,
    "total_fees": 25.20,
    ...
  },
  "plot": "iVBORw0KGgoAAAANS...",  // base64 PNG
  "trades": [
    {
      "entry_time": "2023-01-15 10:30:00",
      "signal_type": "UP",
      "direction": "B",
      "entry_price": 20000.0,
      "exit_price": 20500.0,
      "pnl": 25.0,
      "fees": 0.6,
      ...
    },
    ...
  ]
}
```

## Performance Metrics

The webapp displays the following metrics:

### Return Metrics
- **Total PnL**: Net profit/loss in dollars
- **Total Return**: Percentage return on position size
- **Annualized Return**: Extrapolated annual return rate
- **Sharpe Ratio**: Risk-adjusted return measure

### Risk Metrics
- **Max Drawdown**: Largest peak-to-trough decline
- **Total Fees**: Cumulative trading fees paid

### Trade Statistics
- **Total Trades**: Number of positions taken
- **Win Rate**: Percentage of profitable trades
- **Avg Profit/Trade**: Mean PnL per trade
- **Avg Winning Trade**: Mean profit when winning
- **Avg Losing Trade**: Mean loss when losing
- **Avg Hold Time**: Mean bars per position

### Event Breakdown
- **UP Events**: Trades triggered by upward price moves
- **DOWN Events**: Trades triggered by downward price moves
- Per-event PnL statistics

## Data Requirements

Backtest data must be in Parquet format with the following schema:

```
timestamp: datetime
open: float
high: float
low: float
close: float
volume: float
```

Files should be placed in `data/aggregate_parquet/` with naming pattern:
```
{SYMBOL}USDT_1m_YYYYMMDD_YYYYMMDD.parquet
```

Example: `BTCUSDT_1m_20230101_20240101.parquet`

## Docker Services

The `docker-compose-backtest.yml` configuration includes:

### backtest-api
- **Image**: Custom Python Flask container
- **Port**: 5001 (mapped from internal 5000)
- **Volumes**: 
  - `data/` (read-only parquet files)
  - `server/` (live code reload for development)
  - `src/research/signal_utils/` (simulator module)

### backtest-frontend
- **Image**: nginx:alpine
- **Port**: 8084
- **Volumes**: 
  - `frontend/backtest.html`
  - `frontend/backtest.js`

## Development

### Adding New Metrics

1. Modify `window_sim.py` to calculate new metric in `run_simulation()`
2. Add metric to response in `backtest_api.py`
3. Update `backtest.js` metrics array with display configuration
4. New metric will automatically appear in results grid

### Customizing Frontend

Edit `frontend/backtest.html` for layout/styling changes.
Edit `frontend/backtest.js` for API interactions and display logic.

Both files are mounted as volumes in Docker for live updates.

## Troubleshooting

### No symbols available
- Ensure parquet files exist in `data/aggregate_parquet/`
- Check file naming matches pattern: `{SYMBOL}USDT_1m_*.parquet`
- Verify Docker volume mounts are correct

### API connection failed
- Check Flask server is running on port 5001
- Verify CORS is enabled (should be by default)
- Update `API_BASE_URL` in `backtest.js` if using custom port

### Backtest runs slowly
- Large date ranges take longer to process
- Use `start_date` parameter to limit analysis period
- Consider aggregating data to higher timeframes

## Future Enhancements

- [ ] Multiple strategy comparison
- [ ] Parameter optimization grid search
- [ ] Real-time progress updates via WebSocket
- [ ] Export results to PDF report
- [ ] Strategy preset templates
- [ ] Walk-forward analysis
- [ ] Monte Carlo simulations

## Related Files

- **Strategy Engine**: `src/research/signal_utils/window_sim.py`
- **Backend API**: `server/backtest_api.py`
- **Frontend UI**: `frontend/backtest.html`, `frontend/backtest.js`
- **Docker Config**: `docker/docker-compose-backtest.yml`
- **Data**: `data/aggregate_parquet/*.parquet`
