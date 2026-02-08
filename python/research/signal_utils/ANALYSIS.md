# Signal Utils Code Analysis

## 📊 Summary

**Total Files:** 13 Python files (3,411 lines)  
**Active Files (used by apps):** 2 files (window_sim.py, daily_sim.py)  
**Obsolete/Duplicative Files:** 6 files  
**Support Files:** 5 files  

---

## ✅ Code Used by JavaScript Applications

### 1. **window_sim.py** (1,323 lines) ⭐ ACTIVE
**Used by:** 
- `server/backtest_api.py` - Main API endpoint
- `frontend/backtest/single-symbol.js` - References field names
- `src/research/examples/multisymbol_backtest_example.py`

**Key Functions:**
- `run_simulation_from_file()` - Main entry point
- `detect_signals()` - Signal detection with thresholds
- `simulate_trades()` - Trade execution simulation
- `multisymbol_simulation()` - Multi-symbol backtesting

**Purpose:** Minute-level trade simulator for tactical strategies

---

### 2. **daily_sim.py** (869 lines) ⭐ ACTIVE
**Used by:**
- `server/backtest_api.py` - Daily backtest endpoint

**Key Functions:**
- `run_simulation_from_file()` - Daily-level entry point
- `detect_signals()` - Daily signal detection
- `simulate_trades()` - Trade execution

**Purpose:** Daily-level trade simulator for strategic analysis (similar to window_sim but operates on daily bars)

---

## ⚠️ Obsolete/Legacy Code

These files use an **old pattern-based approach** that has been superseded by window_sim.py and daily_sim.py:

### 3. **trade_move.py** (212 lines) ❌ OBSOLETE
- Imports `moves.trigger()` and `patterns.summary()`
- Old approach: separate trigger detection + trade execution
- **Replacement:** window_sim.py has integrated signal detection

### 4. **moves.py** (47 lines) ❌ OBSOLETE
- `trigger()` function for windowed returns
- Non-overlapping trigger logic
- **Replacement:** window_sim.detect_signals() is more sophisticated

### 5. **patterns.py** (249 lines) ❌ OBSOLETE
- `count_intervals()` - Rolling window counting
- `summary()` - Basic stats (min/max/date ranges)
- **Replacement:** window_sim has better statistical summaries

### 6. **symbol_trade.py** (59 lines) ❌ OBSOLETE
- CLI wrapper for `trade_move.symbol_trade_move()`
- Usage: `python calc4.py <dir> <symbol> <window> <threshold> <holding> <price_type>`
- **Replacement:** Use `window_sim.py` with same parameters

### 7. **ex1.py** (59 lines) ❌ OBSOLETE
- Multi-symbol runner using `trade_move.symbol_trade_move()`
- Loops over all symbols in directory
- **Replacement:** window_sim.multisymbol_simulation()

---

## 🔄 Duplicative Code Analysis

### Signal Detection Logic (DUPLICATED)
**window_sim.py** (lines 34-135):
```python
def detect_signals(df, up_threshold, down_threshold, detection_window, ...):
    # Get open price from detection_window periods ago
    # Calculate return from window start to current close
    # Compare to thresholds
```

**daily_sim.py** (lines 41-146):
```python
def detect_signals(df, up_threshold, down_threshold, detection_window, ...):
    # Exact same logic but operates on daily data
    # 90% code overlap with window_sim
```

**Duplication:** ~100 lines duplicated between window_sim and daily_sim

---

### Trade Simulation Logic (DUPLICATED)
**window_sim.py** (lines 151-748):
```python
def simulate_trades(df, hold_window, position_size, ...):
    # Signal processing
    # Position tracking with multiple accounts
    # Trade execution with fees
    # PnL calculation
    # Summary statistics
```

**daily_sim.py** (lines 165-547):
```python
def simulate_trades(df, hold_window, position_size, ...):
    # Nearly identical logic
    # Same position tracking
    # Same fee calculation
    # 95% code overlap with window_sim
```

**Duplication:** ~400 lines duplicated between window_sim and daily_sim

---

## 🛠️ Support/Utility Files

### 8. **detection_filters.py** (83 lines) ✅ ACTIVE
- 5 signal detection variants for overfitting analysis
- Used by data_utils (documented in data_utils/README.md)
- **Note:** Lives in signal_utils but referenced from data_utils

### 9. **threshold_count.py** (206 lines) ✅ UTILITY
- Counts threshold breach events
- Standalone analysis tool (not imported by other code)
- Usage: `python threshold_count.py data.parquet 0.01 5`

### 10. **kline_stats.py** (142 lines) ✅ UTILITY
- Basic kline statistics and plotting
- EMA and Savitzky-Golay smoothing
- Standalone analysis tool

### 11. **pl_loaders.py** (35 lines) ✅ UTILITY
- Polars data loading helpers
- **Status:** May be unused (no imports found)

### 12. **polars_analysis_example.py** (82 lines) ✅ EXAMPLE
- Example notebook/demo code
- Shows how to use Polars for analysis

### 13. **detection_filters_demo.py** (45 lines) ✅ EXAMPLE
- Demo for detection_filters.py
- Usage: `uv run python detection_filters_demo.py --csv path/to/daily.csv`

---

## 📸 PNG Files (4 files)
- DOGEUSDT.png
- ETHUSDT.png
- ethusdt_cumpnl.png

**Status:** Likely old output/artifacts - can be regenerated

---

## 🎯 Recommendations

### High Priority: Remove Obsolete Code
**Delete these 6 files (881 lines):**
1. ❌ trade_move.py (212 lines)
2. ❌ moves.py (47 lines)
3. ❌ patterns.py (249 lines)
4. ❌ symbol_trade.py (59 lines)
5. ❌ ex1.py (59 lines)
6. ❌ PNG files (4 artifacts)

**Impact:** Reduces codebase by 25%, eliminates confusion about which approach to use

---

### Medium Priority: Consolidate window_sim + daily_sim
**Problem:** 500+ lines of duplicated code between window_sim.py and daily_sim.py

**Solution Options:**

**Option 1: Extract Common Base Class**
```python
# sim_base.py
class TradeSimulator:
    def detect_signals(self, df, up_threshold, down_threshold, ...):
        # Common signal detection logic
    
    def simulate_trades(self, df, hold_window, ...):
        # Common trade execution logic

# window_sim.py
class WindowSimulator(TradeSimulator):
    # Minute-level specifics only

# daily_sim.py  
class DailySimulator(TradeSimulator):
    # Daily-level specifics only
```

**Option 2: Unified Simulator with Time Resolution Parameter**
```python
# unified_sim.py
def run_simulation(df, time_resolution='minute', ...):
    if time_resolution == 'minute':
        # Minute-specific adjustments
    elif time_resolution == 'daily':
        # Daily-specific adjustments
    # Shared logic for both
```

**Recommended:** Option 1 (base class) - cleaner separation, easier testing

---

### Low Priority: Relocate detection_filters.py
**Problem:** detection_filters.py lives in signal_utils but is documented/used by data_utils

**Solution:** Move to data_utils/ where it's actually used
```bash
git mv src/research/signal_utils/detection_filters.py src/research/data_utils/
git mv src/research/signal_utils/detection_filters_demo.py src/research/data_utils/
```

Update imports in any files that reference it.

---

## 📋 Migration Checklist

### Phase 1: Remove Obsolete (30 min)
- [ ] Verify no external dependencies on obsolete files
- [ ] Delete trade_move.py, moves.py, patterns.py
- [ ] Delete symbol_trade.py, ex1.py  
- [ ] Delete PNG artifacts
- [ ] Update any documentation referencing old files
- [ ] Test: Verify backtest_api.py still works

### Phase 2: Consolidate Simulators (2-4 hours)
- [ ] Create sim_base.py with TradeSimulator base class
- [ ] Extract detect_signals() common logic (100 lines)
- [ ] Extract simulate_trades() common logic (400 lines)
- [ ] Refactor window_sim.py to inherit from base
- [ ] Refactor daily_sim.py to inherit from base
- [ ] Test: Run full backtest suite
- [ ] Update server/backtest_api.py imports if needed

### Phase 3: Relocate detection_filters (15 min)
- [ ] Move detection_filters.py to data_utils/
- [ ] Move detection_filters_demo.py to data_utils/
- [ ] Update imports (should be minimal/none)
- [ ] Update data_utils/README.md (already references it)

---

## 📊 Expected Impact

**Before:**
- 13 files, 3,411 lines
- 6 obsolete files (881 lines)
- 500+ lines duplicated
- Confusing: which approach to use?

**After:**
- 8 files, ~2,000 lines
- 0 obsolete files
- ~100 lines duplicated (acceptable)
- Clear: window_sim & daily_sim for production, utilities for analysis

**Benefits:**
- 40% reduction in code volume
- Clearer architecture
- Easier maintenance
- Better testing (shared base class)
- No confusion about which files to use

---

## 🔍 Additional Findings

### pl_loaders.py Status
No imports found - likely unused. Verify and potentially delete.

### threshold_count.py vs window_sim.py
threshold_count.py has overlapping functionality with window_sim but:
- Simpler (no trade execution)
- Good for quick event counting
- Keep as analysis utility

### kline_stats.py
Standalone utility with plotting - keep for ad-hoc analysis.

---

## 💡 Usage Guidance

**For Production Backtesting:**
- ✅ Use `window_sim.py` for minute-level strategies
- ✅ Use `daily_sim.py` for daily strategies
- ❌ Don't use trade_move.py or related files

**For Analysis:**
- ✅ Use `threshold_count.py` for event counting
- ✅ Use `kline_stats.py` for basic stats
- ✅ Use `detection_filters.py` for signal variants (move to data_utils first)

**For Examples:**
- ✅ See `polars_analysis_example.py` for Polars patterns
- ✅ See `detection_filters_demo.py` for filter examples
