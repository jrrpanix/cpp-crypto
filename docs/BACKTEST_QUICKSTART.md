# Backtest Webapp Quick Reference

## 🚀 Start the Webapp

```bash
# Using Makefile (recommended)
make run-backtest

# Or using docker-compose directly
cd docker
docker-compose -f docker-compose-backtest.yml up --build

# Or using the shell script
./scripts/run/run_backtest_webapp.sh
```

Then open: **http://localhost:8084**

## 📋 Parameter Guide

### Core Strategy
- **Symbol**: Choose from dropdown (e.g., BTCUSDT, ETHUSDT)
- **UP Threshold**: Price increase % to trigger (e.g., 0.01 = 1%)
- **UP Direction**: Buy (long) or Sell (short) when threshold hit
- **DOWN Threshold**: Price decrease % to trigger (e.g., -0.02 = -2%)
- **DOWN Direction**: Buy (long) or Sell (short) when threshold hit
- **Detection Window**: Bars to monitor for threshold (e.g., 30)
- **Hold Window**: Bars to hold position (e.g., 30)

### Position Management
- **Position Size**: Dollar amount per trade (e.g., $1000)
- **Position Limit**: Max concurrent positions (1 or 2)
- **Fee Rate**: Trading fee % (e.g., 0.0003 = 0.03%)
- **Number of Accounts**: 1 (reversal) or 2 (separate long/short)

### Optional Filters
- **Start Date**: Only analyze data from this date forward

## 📊 Example Strategies

### Conservative Trend Following
```
Symbol: BTCUSDT
UP: 0.015 (1.5%) → Buy
DOWN: -0.015 (-1.5%) → Sell
Detection: 50 bars
Hold: 50 bars
Position: $1000
```

### Aggressive Mean Reversion
```
Symbol: ETHUSDT
UP: 0.02 (2%) → Sell (short)
DOWN: -0.02 (-2%) → Buy (long)
Detection: 20 bars
Hold: 20 bars
Position: $500
```

### Asymmetric Long Bias
```
Symbol: BTCUSDT
UP: 0.01 (1%) → Buy
DOWN: -0.03 (-3%) → Sell
Detection: 30 bars
Hold: 30 bars
Position: $2000
```

## 📈 Understanding Results

### Key Metrics to Watch

| Metric | What It Means | Target |
|--------|---------------|--------|
| **Total PnL** | Your profit/loss | Green = good |
| **Sharpe Ratio** | Risk-adjusted returns | > 1.0 is solid |
| **Max Drawdown** | Worst losing streak | < -20% acceptable |
| **Win Rate** | % of winning trades | > 50% ideal |

### Trade Breakdown
- **UP Events**: Triggered by upward price moves
- **DOWN Events**: Triggered by downward price moves
- Compare their PnL to see which works better

## 🛠️ Common Tasks

### View Logs
```bash
make logs-backtest
```

### Check Status
```bash
make status-backtest
```

### Stop Services
```bash
make stop-backtest
```

### Restart After Code Changes
```bash
make rebuild-backtest
```

### Test Locally (without Docker)
```bash
# Terminal 1: API
cd server
pip install -r requirements.txt
python backtest_api.py

# Terminal 2: Frontend
cd frontend
python -m http.server 8084
# Open: http://localhost:8084/backtest.html
```

## 🔍 Troubleshooting

### No symbols showing?
Check data files exist:
```bash
ls -la data/aggregate_parquet/*.parquet
```

### API not responding?
Check if running:
```bash
curl http://localhost:5001/health
# Should return: {"status": "ok"}
```

### Browser can't connect?
1. Check services are running: `docker ps`
2. Verify ports 5000 and 8084 are not in use
3. Clear browser cache and reload

### Backtest takes forever?
- Try adding a start_date to limit data
- Check file size: `ls -lh data/aggregate_parquet/BTCUSDT*.parquet`
- Large files (>500MB) will be slower

## 💡 Tips & Tricks

### Finding Good Parameters
1. Start with moderate thresholds (±1-2%)
2. Match detection and hold windows
3. Test with position_limit=1 first
4. Look for Sharpe > 1.0 and drawdown < -20%

### Interpreting UP vs DOWN
- If UP events profit and DOWN loses → trend following works
- If UP loses and DOWN profits → consider reversing directions
- If both lose → thresholds may be wrong size

### Fee Impact
- 0.03% (0.0003) is typical for spot trading
- 0.01% (0.0001) for maker orders
- 0.1% (0.001) for smaller exchanges
- Fees compound quickly at high trade frequencies

### Position Sizing
- Start small ($100-500) to see if strategy works
- Scale up only if Sharpe > 1.5 and consistent
- Consider Kelly Criterion for optimal sizing

## 📚 Further Reading

- Full docs: `frontend/README_BACKTEST.md`
- Implementation: `docs/BACKTEST_WEBAPP_IMPLEMENTATION.md`
- Strategy code: `src/research/signal_utils/window_sim.py`
