# ADV Analysis Table - New Layout

## Overview
The ADV Analysis table has been redesigned to show periods as columns and symbols as rows, making it easier to track how symbols perform over time.

## Table Structure

### Layout
```
┌──────┬──────────┬─────────────────┬─────────────────┬─────────────────┐
│ Rank │ Symbol   │   Period 1      │   Period 2      │   Period 3      │
│      │          ├────────┬────────┼────────┬────────┼────────┬────────┤
│      │          │  ADV   │Weight %│  ADV   │Weight %│  ADV   │Weight %│
├──────┼──────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│  #1  │ BTCUSDT  │ $2.5B  │ 45.0%  │ $2.8B  │ 47.0%  │ $3.0B  │ 48.0%  │
│  #2  │ ETHUSDT  │ $1.8B  │ 32.0%  │ $1.9B  │ 31.0%  │ $2.1B  │ 33.0%  │
│  #3  │ SOLUSDT  │ $800M  │ 14.0%  │ $850M  │ 14.0%  │ $900M  │ 15.0%  │
└──────┴──────────┴────────┴────────┴────────┴────────┴────────┴────────┘
```

### Features

1. **Sticky Columns**
   - Rank and Symbol columns stay fixed when scrolling horizontally
   - Easy to identify which symbol you're looking at

2. **Rank Display**
   - Shows the best (lowest) rank achieved by each symbol across all periods
   - Symbols sorted by best rank

3. **Period Headers**
   - Top row: Begin date (e.g., "Jul 1, 2024")
   - Second line: End date (e.g., "Jul 31, 2024")
   - Spans both ADV and Weight % columns

4. **Subheaders**
   - "ADV" and "Weight %" labels under each period
   - Clear column identification

5. **Rank-Based Coloring**
   - Rank #1: Gold highlight (rgba(255, 215, 0, 0.15))
   - Rank #2: Silver highlight (rgba(192, 192, 192, 0.15))
   - Rank #3: Bronze highlight (rgba(205, 127, 50, 0.15))
   - Rank #4-5: Light blue highlight
   - Rank #6+: No highlight

6. **Hover Effects**
   - Entire row highlights on hover
   - Sticky columns maintain highlight

## Data Transformation

### Input (from API)
```json
[
  {
    "begin_date": "2024-07-01",
    "end_date": "2024-07-31",
    "symbol": "BTCUSDT",
    "adv": 2500000000.50,
    "weight": 0.45
  },
  ...
]
```

### Output (table structure)
- **Rows**: One per unique symbol
- **Columns**: Two per period (ADV + Weight %)
- **Sorting**: Symbols by best rank, periods chronologically

## JavaScript Logic

### Key Functions

1. **displayResults(data)**
   - Groups data by period and symbol
   - Calculates rank per period
   - Builds dynamic header with period columns
   - Creates rows with symbol data across periods

2. **Period Grouping**
   ```javascript
   const periodKey = `${row.begin_date}_${row.end_date}`;
   periodMap.set(periodKey, { begin_date, end_date, symbols })
   ```

3. **Rank Calculation**
   - Per period: Sort symbols by ADV descending
   - Assign rank 1, 2, 3, etc.
   - Track best rank for each symbol

4. **Empty Cells**
   - Shows "-" if symbol doesn't appear in a period
   - Gray, italic styling

## CSS Features

### Sticky Positioning
```css
th.sticky-col {
    position: sticky;
    left: 0;
    z-index: 20;
}

th.sticky-col-2 {
    position: sticky;
    left: 60px;
    z-index: 20;
}
```

### Scrollable Container
```css
.table-container {
    overflow-x: auto;
    max-height: 600px;
    overflow-y: auto;
}
```

### Rank Highlighting
```css
.rank-1 { background: rgba(255, 215, 0, 0.15); } /* Gold */
.rank-2 { background: rgba(192, 192, 192, 0.15); } /* Silver */
.rank-3 { background: rgba(205, 127, 50, 0.15); } /* Bronze */
```

## Usage Example

### Sample Query
- Units: months
- Interval: 1
- Top N: 10

### Result
- 15 periods (columns)
- 10-15 unique symbols (rows)
- 30 data points per period (10 symbols × 2 columns)
- Total: ~450 cells

### Wide Table Handling
- Horizontal scroll for many periods
- Sticky columns for reference
- Responsive design maintains usability

## Benefits

1. **Time Series View**: See how each symbol's ADV changes over time
2. **Comparison**: Easily compare symbols within each period
3. **Trends**: Identify rising/falling symbols across periods
4. **Rankings**: Visual highlighting shows top performers
5. **Compact**: More data visible without excessive scrolling

## Future Enhancements

Possible additions:
- Column wrapping option for very wide tables
- Sparklines showing ADV trend
- Symbol filtering
- Export to CSV
- Highlight cells on click to track specific symbol
- Sort by different metrics (avg rank, total ADV, etc.)
