#!/bin/bash
# Launch the backtest webapp

set -e

cd "$(dirname "$0")/.."

echo "🚀 Starting Backtest Webapp..."
echo ""

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Check if data directory exists
if [ ! -d "data/aggregate_parquet" ]; then
    echo "⚠️  Warning: data/aggregate_parquet directory not found"
    echo "   Backtest will fail without parquet data files"
    echo ""
fi

cd docker

echo "Building and starting services..."
docker-compose -f docker-compose-backtest.yml up --build -d

echo ""
echo "✅ Services started!"
echo ""
echo "📊 Backtest Webapp: http://localhost:8084"
echo "🔌 Flask API:       http://localhost:5000"
echo ""
echo "View logs:    docker-compose -f docker-compose-backtest.yml logs -f"
echo "Stop services: docker-compose -f docker-compose-backtest.yml down"
echo ""
