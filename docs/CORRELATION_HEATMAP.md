# Correlation Heatmap Feature

## Overview

Added a correlation heatmap to the Daily Market Data page that displays the correlation matrix between selected symbols based on their daily returns.

## What Was Added

### Backend (`server/backtest_api.py`)

**New API Endpoint: `/api/daily-correlation`**

```python
POST /api/daily-correlation
```

**Request Body:**
```json
{
    "symbols": ["BTCUSDT", "ETHUSDT", "IX10USDT", ...],
    "start_date": "2024-07-01",  // optional
    "end_date": "2025-10-31"      // optional
}
```

**Response:**
```json
{
    "success": true,
    "correlation_matrix": {
        "BTCUSDT": {"BTCUSDT": 1.0, "ETHUSDT": 0.85, "IX10USDT": 0.92},
        "ETHUSDT": {"BTCUSDT": 0.85, "ETHUSDT": 1.0, "IX10USDT": 0.88},
        "IX10USDT": {"BTCUSDT": 0.92, "ETHUSDT": 0.88, "IX10USDT": 1.0}
    },
    "symbols": ["BTCUSDT", "ETHUSDT", "IX10USDT"],
    "date_range": {
        "start": "2024-07-01T00:00:00",
        "end": "2025-10-31T23:59:59.999"
    },
    "data_points": 489,
    "file": "AGG_WITH_INDEXES_2024-07-01_2025-10-31.pq"
}
```

**How it works:**
1. Loads daily OHLCV data for requested symbols from aggregate file
2. Calculates daily returns: `return = (close - prev_close) / prev_close`
3. Pivots data so each symbol is a column
4. Computes Pearson correlation coefficient for each pair
5. Returns symmetric correlation matrix

### Frontend (`frontend/backtest/daily.html` & `daily.js`)

**New HTML Section:**
- Added correlation heatmap container below volume chart
- Includes explanation text about how to read correlations
- Shows number of data points used for calculation
- Hidden by default, only shows when 2+ symbols loaded

**New JavaScript Functions:**

1. **`loadCorrelationMatrix()`**
   - Fetches correlation data from API
   - Uses same date range as price/volume charts
   - Handles errors gracefully

2. **`renderCorrelationHeatmap(corrMatrix, symbols, dataPoints)`**
   - Generates HTML table with correlation values
   - Color-codes cells based on correlation strength

3. **`getCorrelationColor(corr)`**
   - Returns RGB color for correlation value
   - Green scale for positive correlations (0 to +1)
   - Red scale for negative correlations (0 to -1)
   - White for no correlation (0)

**CSS Styling:**
- `.corr-table`: Compact table design with borders
- Color-coded cells for easy visualization
- Responsive overflow scrolling for many symbols
- Monospace font for correlation values

## How to Use

1. Go to **Daily Market Data** page (`http://localhost:5001/daily.html`)
2. Select 2 or more symbols (works great with indexes like IX10USDT!)
3. Click "Load Data"
4. Scroll down past the price and volume charts
5. View the correlation heatmap

## Reading the Heatmap

- **+1.0 (Dark Green)**: Perfect positive correlation - symbols move together
- **+0.7 to +0.9 (Light Green)**: Strong positive correlation
- **+0.3 to +0.7 (Very Light Green)**: Moderate positive correlation
- **0.0 (White)**: No correlation
- **-0.3 to -0.7 (Light Red)**: Moderate negative correlation
- **-0.7 to -0.9 (Red)**: Strong negative correlation
- **-1.0 (Dark Red)**: Perfect negative correlation - symbols move opposite

## Use Cases

1. **Compare index to constituents**: See how IX10USDT correlates with BTCUSDT, ETHUSDT, etc.
2. **Find diversification opportunities**: Look for symbols with low/negative correlations
3. **Validate index construction**: Ensure index tracks major constituents
4. **Risk analysis**: High correlations mean less diversification benefit
5. **Pair trading**: Find negatively correlated pairs for mean-reversion strategies

## Example

If you load `["BTCUSDT", "ETHUSDT", "IX10USDT"]`:
- BTC-ETH might show 0.85 (strong positive - crypto markets move together)
- BTC-IX10 might show 0.92 (very strong - index tracks BTC closely)
- All diagonal cells show 1.0 (perfect self-correlation)

## Technical Notes

- Correlation calculated using Polars `corr()` method (Pearson correlation)
- Only uses overlapping dates where all symbols have data
- Minimum 2 data points required (realistic minimum is 30+ for meaningful results)
- Uses daily return series, not raw prices (returns are stationary)
- Automatically refreshes when you change date range or symbols

## Integration with Indexes

This feature is particularly useful for the new synthetic indexes:
- **IX10USDT**: See how top-10 index correlates with individual symbols
- **IX25USDT**: Compare broader index correlations
- **Custom indexes**: Validate your index construction methodology

The correlation will show whether your index is tracking the intended market segment.

## Future Enhancements

Potential improvements:
- [ ] Rolling correlation over time (line chart showing how correlation changes)
- [ ] Correlation clustering (group symbols by correlation similarity)
- [ ] Export correlation matrix to CSV
- [ ] Statistical significance testing (p-values)
- [ ] Cophenetic correlation for hierarchical clustering
- [ ] Add to other pages (minute bars, multisymbol backtest)

