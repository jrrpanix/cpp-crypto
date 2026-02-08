# Daily Symbol Comparison - Multi-Scale Support

## Problem
When comparing symbols with vastly different price scales (e.g., BTC at $100,000 vs XRP at $4), the absolute price chart becomes difficult to read as one symbol dominates the Y-axis scale.

## Solution
Added three price display modes to handle different comparison scenarios:

### 1. **Absolute Prices** (Default)
- Shows actual USD prices for each symbol
- Best for: Single symbol or symbols with similar price ranges
- Y-axis: Displays dollar values ($)

### 2. **Normalized (Start at 100)** ⭐ RECOMMENDED for multi-symbol comparison
- All symbols start at 100, showing relative performance
- Makes it easy to compare returns regardless of absolute price
- Best for: Comparing performance of multiple symbols
- Y-axis: Displays normalized values (100 = starting price)
- Tooltip: Shows both normalized value and % change from start

**Example:**
- BTC starts at $90,000 → normalized to 100
- XRP starts at $3.50 → normalized to 100
- After 1 week:
  - BTC at $95,000 (5.56% gain) → 105.56
  - XRP at $3.85 (10% gain) → 110.00
- Now you can clearly see XRP outperformed BTC!

### 3. **Log Scale**
- Uses logarithmic Y-axis
- Shows percentage changes as equal visual distance
- Best for: Very wide price ranges or long time periods
- Y-axis: Logarithmic scale with dollar values

## Usage

1. **Select multiple symbols** from the dropdown (hold Ctrl/Cmd for multiple)
2. **Click "Load Data"** to fetch data
3. **Change "Price Display"** dropdown:
   - Select "Absolute Prices" to see actual dollar values
   - Select "Normalized (Start at 100)" to compare performance
   - Select "Log Scale" for very different price ranges
4. Chart automatically updates when you change the scale

## Technical Details

### Normalization Formula
```javascript
normalizedPrice = (currentPrice / firstPrice) * 100
```

Where:
- `currentPrice` = price at time T
- `firstPrice` = first price in the selected date range
- Result starts at 100 and moves proportionally

### Return Calculation
```javascript
percentReturn = ((normalizedPrice - 100) / 100) * 100
```

## Use Cases

### Comparing Altcoins
**Problem:** ETH ($4,000) vs DOGE ($0.40)
**Solution:** Use "Normalized" mode to see which gained more percentage-wise

### Large Cap vs Small Cap
**Problem:** BTC ($100K) vs PEPE ($0.000001)
**Solution:** Use "Normalized" mode for apples-to-apples comparison

### Long-Term Analysis
**Problem:** BTC price from $1,000 to $100,000
**Solution:** Use "Log Scale" to see early price movements clearly

### Portfolio Rebalancing
**Problem:** Decide which asset performed better
**Solution:** Use "Normalized" mode to compare total returns

## Benefits

✅ **Fair Comparison** - All symbols on equal footing
✅ **Performance Focused** - See returns, not just prices
✅ **Visual Clarity** - No more invisible lines
✅ **Instant Toggle** - Switch between views without reloading
✅ **Percentage Display** - Tooltips show % change from start

## Example Workflow

```
1. Select: BTCUSDT, ETHUSDT, XRPUSDT, ADAUSDT
2. Date Range: Last 3 Months
3. Click: Load Data
4. Price Display: Normalized (Start at 100)
5. Result: Clear visualization of which asset had best returns!
```

## Notes

- Normalized mode is **purely for visualization** - no data is changed
- Original prices are preserved and can be viewed by switching to "Absolute Prices"
- Volume chart is unaffected and always shows actual volume
- Normalization is recalculated if you change date range
