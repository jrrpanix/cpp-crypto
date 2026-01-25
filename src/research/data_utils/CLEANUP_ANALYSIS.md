# Data Utils Cleanup Analysis

## Executive Summary
The `data_utils` directory has grown organically and contains ~6.5K lines of code with significant overlap and unused functionality. This document categorizes files and identifies consolidation opportunities.

---

## File Categories & Dependencies

### Core Pipeline (5 files, ~1.0K lines)
**Purpose**: Main data processing workflow. Everything else depends on or feeds into these.

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| **config.py** | 53 | Centralized paths, symbols, constants | ✅ Core (new, clean) |
| **pipeline.py** | 297 | Orchestrator (5-step workflow) | ✅ Core (just wired) |
| **update_klines.py** | 227 | Parse downloaded zips → parquet | ✅ Core |
| **make_daily.py** | 221 | 1m bars → daily OHLC | ✅ Core (with wrapper added) |
| **make_aggregate.py** | 189 | Combine daily files per month | ✅ Core |

### Run Logging & Analytics (5 files, ~506 lines)
**Purpose**: Track backtest runs, metrics, Sharpe rankings, and cross-run analysis.

| File | Lines | Purpose | Status | Notes |
|------|-------|---------|--------|-------|
| **runlog.py** | 206 | SQLite run registry | ✅ Clean | New; replaces ad-hoc logging |
| **runlog_demo.py** | 60 | Demo for runlog | ✅ Clean | Can move to examples/ |
| **runlog_stats.py** | 109 | Query runs, rank by Sharpe | ✅ Clean | New |
| **duckdb_analytics.py** | 129 | Optional DuckDB queries | ✅ Clean | New; for advanced analytics |
| **duckdb_analytics_demo.py** | 101 | Demo for DuckDB | ✅ Clean | Can move to examples/ |

### Data Loading (1 file, 89 lines)
**Purpose**: Robust glob-based loading without brittle filenames.

| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| **daily_loader.py** | 89 | Load daily parquet by symbol/glob | ✅ Clean (new) |

### Utilities (2 files, ~235 lines)
**Purpose**: Calculation & indexing helpers.

| File | Lines | Purpose | Status | Notes |
|------|-------|---------|--------|-------|
| **calc_adv.py** | 840 | ADV + weights + plotting | ⚠️ Large; works | Self-contained |
| **build_index.py** | 570 | Build market indexes | ⚠️ Large; works | Self-contained |

### Data Validation & Debugging (5 files, ~920 lines)
**Purpose**: Find gaps, repair missing data, visualize.

| File | Lines | Purpose | Status | Frequency |
|------|-------|---------|--------|-----------|
| **check_missing.py** | 292 | Identify gaps vs aggregate | ⚠️ Works | Occasional |
| **repair_missing.py** | 411 | Merge gap-fill data | ⚠️ Works | Occasional |
| **debug_daily.py** | 135 | Inspect daily files | ⚠️ Debug | Ad-hoc |
| **debug_gaps.py** | 122 | Find time gaps in data | ⚠️ Debug | Ad-hoc |
| **plot_daily.py** | 260 | Visualize daily bars | ⚠️ Works | Ad-hoc |

### Download & Utilities (5 files, ~483 lines)
**Purpose**: One-off download helpers, partition management.

| File | Lines | Purpose | Status | Frequency | Alternative |
|------|-------|---------|--------|-----------|-------------|
| **bootstrap_klines.py** | 87 | Download all last year | ⚠️ Works | Rare | `pipeline.py --download` |
| **get_latest_klines.py** | 118 | Download for symbols | ⚠️ Works | Rare | Part of update_klines |
| **download_missing.py** | 251 | Download gap-fill data | ⚠️ Works | Occasional | check_missing → repair → manual |
| **partition_helper.py** | 117 | Parse filename patterns | ⚠️ Works | Rare | Config patterns used instead |
| **test_parse.py** | 163 | Test file parsing | ⚠️ Test | Once | Can archive |

### Demos & Examples (6 files, ~60 lines)
**Purpose**: Showcase functionality.

| File | Lines | Status | Move To | Notes |
|------|-------|--------|---------|-------|
| **runlog_demo.py** | 60 | ✅ Clean | examples/ | Runlog walkthrough |
| **duckdb_analytics_demo.py** | 101 | ✅ Clean | examples/ | DuckDB queries demo |
| (+ runlog, daily_loader examples) | TBD | N/A | N/A | Can add docstring examples |

### Other / Unsorted (3 files, ~169 lines)
| File | Lines | Purpose | Status |
|------|-------|---------|--------|
| **adv_index.py** | 337 | Correlate ADV → index weighting | ⚠️ Works | Single-use; could be util |
| **calc_index.py** | 451 | Calculate index via ADV weighting | ⚠️ Works | Single-use; could be util |
| **viewp.py** | 51 | Quick parquet viewer | ⚠️ Debug | Ad-hoc; consider archiving |
| **PIPELINE_GUIDE.py** | 133 | Quick ref for pipeline CLI | ⚠️ Docs | Merge into README |
| **view_kline.py** | ? | (not found) | ? | Check if exists/needed |
| **make_aggregate_with_indexes.py** | 261 | Combine + build indexes (old?) | ⚠️ Old | Replaced by pipeline.py |

---

## Key Redundancies & Issues

### 1. **Multiple Download Paths**
**Problem**: `bootstrap_klines`, `get_latest_klines`, and `download_missing` all download data. `update_klines` also downloads.

| Approach | Lines | Use Case | Status |
|----------|-------|----------|--------|
| `bootstrap_klines.download_all_last_year()` | ~40 | Initial full download | Used in pipeline |
| `get_latest_klines.download_kline()` | ~80 | Single symbol/month | Embedded in others |
| `download_missing.py` (CLI) | 251 | Gap-fill workflow | Manual; complex |
| `update_klines.py` (main) | 227 | Part of pipeline | Used in pipeline |

**Action**: Keep `bootstrap_klines` (called by pipeline) and `update_klines`. Deprecate `get_latest_klines` and `download_missing` (rarely used; complex workflow).

---

### 2. **Multiple Index/ADV Building Paths**
**Problem**: `calc_index.py`, `build_index.py`, `calc_adv.py`, `adv_index.py` overlap significantly.

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| **calc_adv.py** | ADV calculation + plotting | 840 | Comprehensive; used |
| **adv_index.py** | ADV → index correlation | 337 | Single-use; unclear UI |
| **calc_index.py** | Index via ADV weighting | 451 | Alternative approach? |
| **build_index.py** | Build index (unclear path) | 570 | Alternative approach? |
| **make_aggregate_with_indexes.py** | Old: aggregate + indexes | 261 | Replaced by pipeline.py |

**Questions**:
- Are `calc_index`, `build_index` still used?
- Is `adv_index` a demo or production?
- Should these consolidate into a single `index_builder.py`?

---

### 3. **Test/Debug Scripts**
**Problem**: Many one-off debug scripts; unclear which are "kept for reference" vs "actively used".

| File | Purpose | Used? | Status |
|------|---------|-------|--------|
| **test_parse.py** | Test kline parsing | Once | Archive to examples/ |
| **debug_daily.py** | Inspect daily files | Ad-hoc | Keep as utility; document |
| **debug_gaps.py** | Find gaps in time series | Ad-hoc | Keep as utility; document |
| **plot_daily.py** | Visualize bars | Rarely | Keep as utility; document |
| **viewp.py** | Parquet viewer | Ad-hoc | Keep as utility; document |
| **check_missing.py** | Verify vs aggregate | Occasionally | Core utility; keep |
| **repair_missing.py** | Merge gap-fill | Occasionally | Core utility; keep |

**Action**: Clearly mark as "Utilities" in README; add usage docs.

---

### 4. **Unused Helpers**
**Problem**: Some utility functions are defined in multiple places or not exported well.

| Function | File | Lines | Alternative |
|----------|------|-------|------------|
| `partition_helper.py` | 117 | Filename parsing | Use `config.py` patterns + glob |
| `view_kline.py` | ? | Parquet viewer | Use `viewp.py` or pandas |

**Action**: Deprecate `partition_helper` (config patterns are simpler). Document `viewp` usage.

---

### 5. **Configuration Brittleness (Now Fixed)**
✅ **Was**: Hardcoded paths scattered across files.
✅ **Now**: Centralized in `config.py`.
✅ **Impact**: Reduced future brittleness; all scripts should import from config.

---

## Proposed Cleanup

### Immediate Actions (Low Risk)

1. **Move Demos to `examples/`**
   - Create `examples/runlog_demo.py` → symlink or copy
   - Create `examples/duckdb_analytics_demo.py`
   - Keep one-liners in README

2. **Mark Utilities in README**
   - Table of "Core", "Utilities", "Debug", "Archive"
   - Add usage examples

3. **Deprecate/Archive**
   - `partition_helper.py` → Archive (use config patterns)
   - `test_parse.py` → Archive (one-time test)
   - `make_aggregate_with_indexes.py` → Archive (replaced by pipeline)

4. **Consolidate Docs**
   - Move `PIPELINE_GUIDE.py` content → main README
   - Keep PIPELINE_GUIDE.py as quick reference (`print(__doc__)`)

### Medium-Term Refactor (Needs Confirmation)

1. **Clarify Index/ADV Strategy**
   - Which of `calc_index`, `build_index`, `adv_index` are actively used?
   - Consider single `index_builder.py` with options

2. **Unify Download Logic** (if not already in pipeline)
   - Keep: `bootstrap_klines`, `update_klines`
   - Deprecate: `get_latest_klines`, `download_missing`

3. **Organize Utilities**
   - Create `utils/` subdirectory:
     - `utils/visualization.py` (plot_daily + viewp)
     - `utils/validation.py` (check_missing, repair_missing, debug_*.py)

---

## Recommended Directory Structure (Post-Cleanup)

```
src/research/data_utils/
├── Core Pipeline (5 files)
│   ├── config.py                    # Centralized config
│   ├── pipeline.py                  # Orchestrator
│   ├── update_klines.py             # Download + parse
│   ├── make_daily.py                # 1m → daily
│   └── make_aggregate.py            # Combine dailies
├── Run Tracking & Analytics (5 files)
│   ├── runlog.py                    # SQLite registry
│   ├── runlog_stats.py              # Query runs
│   ├── duckdb_analytics.py          # Optional DuckDB
│   ├── daily_loader.py              # Robust data loading
│   └── detection_filters.py         # Signal detection variants
├── Utilities (2 files)
│   ├── calc_adv.py                  # ADV calculation
│   └── build_index.py               # Index building
├── Validation & Debug (5 files, labeled as such)
│   ├── check_missing.py
│   ├── repair_missing.py
│   ├── debug_daily.py
│   ├── debug_gaps.py
│   ├── plot_daily.py
│   └── viewp.py
├── Examples (move to examples/)
│   ├── runlog_demo.py
│   └── duckdb_analytics_demo.py
├── Reference / Archive
│   ├── PIPELINE_GUIDE.py            # Quick ref (print(__doc__))
│   └── (deprecated files archived elsewhere)
└── README.md                        # Updated with this structure
```

---

## Next Steps

1. **Confirm Deprecations** with user
   - Which index/ADV files are actively used?
   - OK to archive make_aggregate_with_indexes?
   - OK to deprecate partition_helper, test_parse?

2. **Update README**
   - Add file directory table
   - Add "Core" vs "Utilities" vs "Debug" sections
   - Add usage examples for each category

3. **Execute Cleanup**
   - Move demos
   - Archive unused files
   - Update imports if needed

---

## Metrics

**Before**:
- 31 Python files
- ~6.5K lines
- Unclear which are "core" vs "utility" vs "debug"
- Config scattered; brittle filenames

**After** (estimated):
- ~20 Python files (core + utilities; debug separated; demos moved)
- ~5.5K lines (archived; consolidated)
- Clear file organization
- Centralized config; robust patterns
- Well-documented README with examples

