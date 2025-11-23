# Index Architecture

## Overview

This document describes the architecture for managing synthetic indexes (IX10, IX25, etc.) separately from raw Binance market data.

## Directory Structure

```
data/
├── klines/                  # Minute-level raw Binance data
├── klines_daily/            # Daily aggregated Binance data
├── klines_index/            # 🆕 Synthetic indexes (constructed)
└── klines_aggregate/        # Combined aggregate files
    ├── AGG_*.pq                        # Binance data only
    └── AGG_WITH_INDEXES_*.pq           # 🆕 Binance + indexes
```

## Why Separate Indexes?

### Problems with Mixing Data:
- ❌ Scripts assume all files are raw Binance data
- ❌ Potential confusion about data source
- ❌ Risk of processing synthetic data as real market data
- ❌ Difficult to maintain and regenerate independently

### Benefits of Separation:
- ✅ Clear distinction between raw and constructed data
- ✅ Scripts processing Binance data won't touch indexes
- ✅ Easy to regenerate indexes without affecting raw data
- ✅ Self-documenting directory structure
- ✅ Can create aggregates with or without indexes

## Building Indexes

### 1. Create an Index

```bash
# Build top 10 USDT index with monthly rebalancing
uv run python src/research/data_utils/build_index.py \
  --klines-dir /workspace/data/klines_daily \
  --start-date 2024-07-01 --end-date 2025-10-31 \
  --top-n 10 --symbol IX10USDT --name "Top 10 Monthly Index" \
  --plot

# Output: /workspace/data/klines_index/IX10USDT_daily_2024-08_2025-10.parquet
```

### 2. Create Multiple Indexes

```bash
# Top 10 index
uv run python src/research/data_utils/build_index.py \
  --klines-dir /workspace/data/klines_daily \
  --start-date 2024-07-01 --end-date 2025-10-31 \
  --top-n 10 --symbol IX10USDT

# Top 25 excluding BTC (drop rank 1)
uv run python src/research/data_utils/build_index.py \
  --klines-dir /workspace/data/klines_daily \
  --start-date 2024-07-01 --end-date 2025-10-31 \
  --top-n 25 --drop-n 1 --symbol IX25USDT

# Top 50 index
uv run python src/research/data_utils/build_index.py \
  --klines-dir /workspace/data/klines_daily \
  --start-date 2024-07-01 --end-date 2025-10-31 \
  --top-n 50 --symbol IX50USDT
```

### 3. Generate Aggregate with Indexes

```bash
# Combine Binance data + indexes into single aggregate
uv run python src/research/data_utils/make_aggregate_with_indexes.py

# Output: /workspace/data/klines_aggregate/AGG_WITH_INDEXES_*.pq
```

## Webapp Integration

### Backend Updates

The backend (`server/backtest_api.py`) has been updated to:

1. **Prefer aggregate files with indexes** (`AGG_WITH_INDEXES_*.pq`)
2. **Fallback to regular aggregates** if indexes version doesn't exist
3. **Load symbols from aggregate** to include indexes in symbol list

### Affected Endpoints

- **`GET /api/symbols`** - Returns both Binance symbols and indexes
- **`POST /api/daily-data`** - Uses AGG_WITH_INDEXES file if available
- **`POST /api/calculate-adv`** - Uses AGG_WITH_INDEXES file if available

### Workflow

```bash
# 1. Build indexes
uv run python src/research/data_utils/build_index.py [options]

# 2. Create aggregate with indexes
uv run python src/research/data_utils/make_aggregate_with_indexes.py

# 3. Restart backend
docker restart <backend-container>

# 4. Indexes now appear in daily market data visualization!
```

## Index File Format

Indexes use the same schema as Binance kline files:

```python
{
    'open_time': datetime[ms],    # Bar timestamp
    'open': float64,               # Index level (same as close)
    'high': float64,               # Index level (no intraday variation)
    'low': float64,                # Index level (no intraday variation)
    'close': float64,              # Index level
    'volume': float64,             # 0.0 (synthetic index)
    'quote_volume': float64,       # 0.0 (synthetic index)
    'symbol': str                  # e.g., "IX10USDT"
}
```

Note: For daily indexes, OHLC all equal the index level since there's no intraday variation.

## Scripts Reference

### Core Scripts

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `build_index.py` | Build weighted index | Daily klines | Index file in `klines_index/` |
| `make_aggregate_with_indexes.py` | Combine Binance + indexes | Both directories | `AGG_WITH_INDEXES_*.pq` |
| `make_aggregate.py` | Combine Binance only | `klines_daily/` | `AGG_*.pq` |

### Options for `build_index.py`

- `--klines-dir`: Source directory with Binance daily data
- `--output-dir`: Where to save index (default: `klines_index/`)
- `--start-date` / `--end-date`: Date range
- `--top-n`: Number of top symbols to include
- `--drop-n`: Drop top N symbols (e.g., exclude BTC)
- `--symbol`: Index symbol name (e.g., IX10USDT)
- `--interval` / `--units`: Rebalance frequency (default: 1 month)
- `--plot`: Generate visualization

## Best Practices

1. **Always separate raw and constructed data**
   - Keep Binance data in `klines_daily/`
   - Keep indexes in `klines_index/`

2. **Use descriptive index names**
   - `IX10USDT` - Top 10 USDT symbols
   - `IX25USDT` - Top 25 USDT symbols
   - `IX50XBTC` - Top 50 excluding BTC

3. **Regenerate aggregates after building indexes**
   - Run `make_aggregate_with_indexes.py` to update
   - Restart backend to pick up changes

4. **Document your indexes**
   - Note the construction methodology
   - Track rebalance frequency
   - Document any exclusions (drop_n)

## Troubleshooting

### Index doesn't appear in webapp

1. **Check file exists**
   ```bash
   ls /workspace/data/klines_index/IX*
   ```

2. **Regenerate aggregate with indexes**
   ```bash
   uv run python make_aggregate_with_indexes.py
   ```

3. **Verify aggregate file**
   ```bash
   ls /workspace/data/klines_aggregate/AGG_WITH_INDEXES*
   ```

4. **Restart backend**
   ```bash
   docker restart <backend-container>
   ```

### Index has wrong symbol name

The symbol is extracted from the filename pattern: `{SYMBOL}_daily_*.parquet`

Example: `IX10USDT_daily_2024-08_2025-10.parquet` → symbol = `IX10USDT`

Make sure to use the correct `--symbol` parameter when building.

## Future Enhancements

- [ ] Add index metadata file (construction details, rebalance dates)
- [ ] Support for custom rebalancing strategies
- [ ] Equal-weighted indexes (not just ADV-weighted)
- [ ] Sector/category-based indexes
- [ ] Index comparison tools
- [ ] Automated index regeneration on data updates

## Related Documentation

- [Data Pipeline README](../src/research/data_utils/README.md)
- [Makefile Reference](MAKEFILE_REFERENCE.md)
- [Backtest Webapp](../frontend/backtest/README_BACKTEST.md)
