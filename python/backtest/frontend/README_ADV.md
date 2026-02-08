# ADV Analysis Webpage

## Overview
The Average Daily Volume (ADV) Analysis page calculates and displays trading volume metrics across time periods to identify the most liquid trading pairs.

## Files Created
- `frontend/backtest/adv.html` - Main HTML page with form inputs
- `frontend/backtest/adv.js` - JavaScript for API calls and result display
- Updated `server/backtest_api.py` - Added `/api/calculate-adv` endpoint
- Updated `frontend/backtest/index.html` - Added ADV Analysis card

## Features
- **Time Units**: Choose between weekly or monthly intervals
- **Interval**: Set the number of time units per period (1-12)
- **Top N Symbols**: Display the top N symbols by volume (1-100)
- **Portfolio Weights**: Automatically calculates portfolio weights for each period
- **Interactive Table**: Displays begin date, end date, symbol, ADV in USD, and weight percentage
- **Statistics Cards**: Shows total periods, unique symbols, average ADV, and max ADV

## API Endpoint

### POST `/api/calculate-adv`

**Request Body:**
```json
{
  "units": "months",    // "months" or "weeks"
  "interval": 1,        // 1-12
  "top_n": 10          // 1-100
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "begin_date": "2024-07-01",
      "end_date": "2024-07-31",
      "symbol": "BTCUSDT",
      "adv": 1234567890.50,
      "weight": 0.45
    },
    ...
  ],
  "total_periods": 15,
  "total_symbols": 25,
  "file": "AGG_2024-07_2025-09.pq"
}
```

## Data Source
The endpoint uses the aggregate parquet file located at:
- Docker: `/workspace/data/klines_aggregate/AGG_*.pq`
- Local: `data/klines_aggregate/AGG_*.pq`

The function automatically filters to USDT symbols and uses the `calculate_adv` function from `src/research/data_utils/calc_adv.py`.

## Navigation
Access the page from:
1. Landing page (index.html) → "ADV Analysis" card
2. Direct URL: `http://localhost:5000/adv.html`

## Implementation Details
- **Backend**: Flask API endpoint calls `calc_adv.calculate_adv()` function
- **Data Processing**: Uses Polars DataFrame for efficient data handling
- **Frontend**: Vanilla JavaScript with fetch API
- **Styling**: Responsive design matching the platform's existing UI

## Usage Example
1. Navigate to the ADV Analysis page from the landing page
2. Select time units (e.g., "months")
3. Enter interval (e.g., 1 for monthly)
4. Enter top N (e.g., 10 for top 10 symbols)
5. Click "Calculate ADV"
6. View results in the interactive table with weights

## Performance
- Calculates ADV for 539 symbols across 15+ months
- Results typically return in 2-3 seconds
- Weight calculations ensure each period sums to 1.0

## Future Enhancements
- Add filtering by symbol prefix/suffix
- Export results to CSV
- Visualizations (charts showing ADV over time)
- Comparison between different time periods
