#!/bin/bash
# Monthly Data Update Script
# Regenerates all aggregate files, indexes, and weights after monthly data downloads
#
# Usage:
#   ./scripts/monthly_data_update.sh
#
# Prerequisites:
#   - New monthly data already downloaded and parsed into /workspace/data/klines/
#   - Daily aggregates created in /workspace/data/klines_daily/

set -e  # Exit on error

echo "================================================================================"
echo "MONTHLY DATA UPDATE SCRIPT"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Create aggregate file (all Binance symbols)"
echo "  2. Build 5 market indexes (IX10, IX10EXBTC, IX60, IX100, IX130)"
echo "  3. Combine into AGG_WITH_INDEXES"
echo "  4. Generate WEIGHTS files for all universes"
echo ""
echo "================================================================================"
echo ""

# Configuration
START_DATE="2024-07-01"
END_DATE=$(date +%Y-%m-%d)  # Today's date
KLINES_DIR="/workspace/data/klines"
KLINES_DAILY_DIR="/workspace/data/klines_daily"
KLINES_INDEX_DIR="/workspace/data/klines_index"
KLINES_AGG_DIR="/workspace/data/klines_aggregate"
SCRIPTS_DIR="/workspace/src/research/data_utils"

echo "📅 Date range: $START_DATE to $END_DATE"
echo ""

# Step 1: Create aggregate file (Binance data only)
echo "================================================================================"
echo "STEP 1: Create Aggregate File"
echo "================================================================================"
uv run python $SCRIPTS_DIR/make_aggregate.py \
  --input-dir $KLINES_DAILY_DIR \
  --output-dir $KLINES_AGG_DIR

echo ""
echo "✅ Aggregate file created"
echo ""

# Step 2: Build all indexes (monthly rebalancing)
echo "================================================================================"
echo "STEP 2: Build Market Indexes"
echo "================================================================================"

# IX10 - Top 10 including BTC (monthly rebalancing)
echo ""
echo "📊 Building IX10 (Top 10 with BTC, monthly rebalancing)..."
uv run python $SCRIPTS_DIR/build_index.py \
  --klines-dir $KLINES_DAILY_DIR \
  --start-date $START_DATE \
  --end-date $END_DATE \
  --top-n 10 \
  --units months \
  --symbol IX10 \
  --name "Top 10 Monthly Index" \
  --plot

# IX10EXBTC - Top 10 excluding BTC (drop rank 1)
echo ""
echo "📊 Building IX10EXBTC (Top 10 excluding BTC, monthly rebalancing)..."
uv run python $SCRIPTS_DIR/build_index.py \
  --klines-dir $KLINES_DAILY_DIR \
  --start-date $START_DATE \
  --end-date $END_DATE \
  --top-n 10 \
  --drop-n 1 \
  --units months \
  --symbol IX10EXBTC \
  --name "Top 10 Excluding BTC"

# IX60 - Mid 60 (ranks 11-70)
echo ""
echo "📊 Building IX60 (Mid 60: ranks 11-70, monthly rebalancing)..."
uv run python $SCRIPTS_DIR/build_index.py \
  --klines-dir $KLINES_DAILY_DIR \
  --start-date $START_DATE \
  --end-date $END_DATE \
  --top-n 70 \
  --drop-n 10 \
  --units months \
  --symbol IX60 \
  --name "Mid 60 Index"

# IX100 - Small 100 (ranks 71-170)
echo ""
echo "📊 Building IX100 (Small 100: ranks 71-170, monthly rebalancing)..."
uv run python $SCRIPTS_DIR/build_index.py \
  --klines-dir $KLINES_DAILY_DIR \
  --start-date $START_DATE \
  --end-date $END_DATE \
  --top-n 170 \
  --drop-n 70 \
  --units months \
  --symbol IX100 \
  --name "Small 100 Index"

# IX130 - Tiny 130 (ranks 171-300)
echo ""
echo "📊 Building IX130 (Tiny 130: ranks 171-300, monthly rebalancing)..."
uv run python $SCRIPTS_DIR/build_index.py \
  --klines-dir $KLINES_DAILY_DIR \
  --start-date $START_DATE \
  --end-date $END_DATE \
  --top-n 300 \
  --drop-n 170 \
  --units months \
  --symbol IX130 \
  --name "Tiny 130 Index"

echo ""
echo "✅ All indexes built"
echo ""

# Step 3: Combine Binance data + indexes
echo "================================================================================"
echo "STEP 3: Combine Binance + Indexes"
echo "================================================================================"
uv run python $SCRIPTS_DIR/make_aggregate_with_indexes.py \
  --binance-dir $KLINES_DAILY_DIR \
  --index-dir $KLINES_INDEX_DIR \
  --output-dir $KLINES_AGG_DIR \
  --start-date $START_DATE \
  --end-date $END_DATE

echo ""
echo "✅ AGG_WITH_INDEXES file created"
echo ""

# Step 4: Generate WEIGHTS files for all universes
echo "================================================================================"
echo "STEP 4: Generate WEIGHTS Files"
echo "================================================================================"

# Find the most recent AGG_WITH_INDEXES file
AGG_FILE=$(ls -t $KLINES_AGG_DIR/AGG_WITH_INDEXES_*.pq | head -n1)
echo "📊 Using aggregate file: $AGG_FILE"
echo ""

# WEIGHTS_10_1_MONTH (top 10 with BTC)
echo "📊 Generating WEIGHTS_10 (Top 10 with BTC, monthly)..."
uv run python $SCRIPTS_DIR/calc_adv.py \
  --input-file $AGG_FILE \
  --output-dir $KLINES_AGG_DIR \
  --nsymbols 10 \
  --interval 1 \
  --units months

# WEIGHTS_10_DROP1_1_MONTH (top 10 excluding BTC)
echo ""
echo "📊 Generating WEIGHTS_10_DROP1 (Top 10 excluding BTC, monthly)..."
uv run python $SCRIPTS_DIR/calc_adv.py \
  --input-file $AGG_FILE \
  --output-dir $KLINES_AGG_DIR \
  --nsymbols 10 \
  --drop-n 1 \
  --interval 1 \
  --units months

# WEIGHTS_70_DROP10_1_MONTH (mid 60)
echo ""
echo "📊 Generating WEIGHTS_70_DROP10 (Mid 60, monthly)..."
uv run python $SCRIPTS_DIR/calc_adv.py \
  --input-file $AGG_FILE \
  --output-dir $KLINES_AGG_DIR \
  --nsymbols 70 \
  --drop-n 10 \
  --interval 1 \
  --units months

# WEIGHTS_170_DROP70_1_MONTH (small 100)
echo ""
echo "📊 Generating WEIGHTS_170_DROP70 (Small 100, monthly)..."
uv run python $SCRIPTS_DIR/calc_adv.py \
  --input-file $AGG_FILE \
  --output-dir $KLINES_AGG_DIR \
  --nsymbols 170 \
  --drop-n 70 \
  --interval 1 \
  --units months

# WEIGHTS_300_DROP170_1_MONTH (tiny 130)
echo ""
echo "📊 Generating WEIGHTS_300_DROP170 (Tiny 130, monthly)..."
uv run python $SCRIPTS_DIR/calc_adv.py \
  --input-file $AGG_FILE \
  --output-dir $KLINES_AGG_DIR \
  --nsymbols 300 \
  --drop-n 170 \
  --interval 1 \
  --units months

echo ""
echo "✅ All WEIGHTS files generated"
echo ""

# Summary
echo "================================================================================"
echo "✅ MONTHLY UPDATE COMPLETE!"
echo "================================================================================"
echo ""
echo "Generated files in $KLINES_AGG_DIR:"
ls -lh $KLINES_AGG_DIR/AGG_WITH_INDEXES_*.pq | tail -1
echo ""
echo "Generated indexes in $KLINES_INDEX_DIR:"
ls -lh $KLINES_INDEX_DIR/*.parquet | tail -5
echo ""
echo "Generated weights in $KLINES_AGG_DIR:"
ls -lh $KLINES_AGG_DIR/WEIGHTS_*.pq | tail -5
echo ""
echo "💡 Next step: Restart the backend server to use the new data"
echo "================================================================================"
