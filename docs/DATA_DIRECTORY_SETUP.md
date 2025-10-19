# Data Directory Setup Guide

## Problem

The data directory is **not** included in the git repository (it's in `.gitignore`) because:
- Data files are large (often GBs)
- Data is user-specific
- Different users may store data in different locations

## Solution

This project uses an **environment variable** approach to configure the data directory location.

## Quick Setup

### 1. Copy the environment template

```bash
cp .env.example .env
```

### 2. Edit `.env` to point to your data location

```bash
# For macOS/Linux users
nano .env
# or
code .env
```

Set `DATA_DIR` to your actual data location:

```bash
# Example 1: Data outside the project
DATA_DIR=/Users/yourname/github/data

# Example 2: Data inside the project (default)
DATA_DIR=./data

# Example 3: Absolute path on Linux
DATA_DIR=/home/yourname/crypto-data
```

### 3. Create the data directory if it doesn't exist

```bash
mkdir -p /Users/yourname/github/data/kline_aggregate
# Or wherever you set DATA_DIR
```

### 4. Verify the setup

```bash
# Check that your .env file exists
cat .env

# Check that data directory exists
ls -la $DATA_DIR
```

## Data Directory Structure

The backtest webapp looks for parquet files in these locations (in order):

1. `{DATA_DIR}/kline_aggregate/*.parquet` (recommended)
2. `{DATA_DIR}/aggregate_parquet/*.parquet` (old structure)
3. `{DATA_DIR}/klines/*.parquet` (alternative)

Example structure:
```
/Users/yourname/github/data/
└── kline_aggregate/
    ├── BTCUSDT_1m_20230101_20241231.parquet
    ├── ETHUSDT_1m_20230101_20241231.parquet
    └── SOLUSDT_1m_20230101_20241231.parquet
```

## For Different Environments

### Local Development (macOS/Linux)

```bash
# .env
DATA_DIR=/Users/yourname/github/data
```

### Docker Development

The docker-compose files automatically use `DATA_DIR` from `.env`:

```bash
make run-backtest  # Uses DATA_DIR from .env
```

### CI/CD or Testing

```bash
# .env
DATA_DIR=./test_data
```

## For New Users Cloning the Repo

### Step 1: Clone the repository

```bash
git clone https://github.com/jrrpanix/cpp-crypto.git
cd cpp-crypto
```

### Step 2: Set up environment

```bash
# Copy the template
cp .env.example .env

# Edit to set your data directory
nano .env
```

### Step 3: Create or link data directory

**Option A: Create new data directory**
```bash
mkdir -p ./data/kline_aggregate
```

**Option B: Link to existing data directory**
```bash
# In .env, point to existing location
echo "DATA_DIR=/path/to/existing/data" > .env
```

**Option C: Download sample data** (if available)
```bash
# Download starter data
python src/research/data_utils/bootstrap_klines.py
```

### Step 4: Verify setup

```bash
# Check configuration
cat .env

# Check data exists
ls -la $(grep DATA_DIR .env | cut -d'=' -f2)/kline_aggregate/
```

### Step 5: Run the webapp

```bash
make run-backtest
# Access: http://localhost:8084
```

## Troubleshooting

### "No symbols available" error

**Problem**: The webapp can't find parquet files.

**Solution**:
1. Check your `.env` file:
   ```bash
   cat .env
   ```

2. Verify the data directory exists:
   ```bash
   ls -la /path/from/your/env/kline_aggregate/
   ```

3. Check for parquet files:
   ```bash
   ls -la /path/from/your/env/kline_aggregate/*.parquet
   ```

4. Check the API logs:
   ```bash
   make logs-backtest
   # Look for: "📁 Using data directory: /app/data/..."
   ```

### DATA_DIR not being used

**Problem**: Changes to `.env` not taking effect.

**Solution**:
1. Restart docker services:
   ```bash
   make stop-backtest
   make run-backtest
   ```

2. Verify environment variable is loaded:
   ```bash
   echo $DATA_DIR
   ```

### Permission errors

**Problem**: Docker can't read the data directory.

**Solution**:
```bash
# Make data readable
chmod -R +r /path/to/data

# Or add write permissions if needed
chmod -R 755 /path/to/data
```

## Default Behavior

If `.env` doesn't exist or `DATA_DIR` is not set:

1. **Docker**: Uses `./data` (relative to project root)
2. **Flask API**: Searches multiple locations automatically:
   - `/app/data/kline_aggregate`
   - `/app/data/aggregate_parquet`
   - `/app/data/klines`
   - `./data/kline_aggregate` (local)
   - Falls back to first location if none found

## Best Practices

### For Personal Use
- Store data outside the project: `/Users/yourname/github/data`
- Keeps project directory clean
- Easy to share data across multiple projects

### For Team Use
- Document the expected `DATA_DIR` structure in README
- Provide sample `.env.example` with placeholder paths
- Consider providing a data download script

### For Production
- Use absolute paths in `.env`
- Mount data as read-only (`:ro`) in docker-compose
- Keep data separate from code

## Example Workflows

### Workflow 1: Fresh Start

```bash
# Clone repo
git clone https://github.com/jrrpanix/cpp-crypto.git
cd cpp-crypto

# Setup environment
cp .env.example .env
echo "DATA_DIR=/Users/$(whoami)/crypto-data" >> .env

# Create data directory
mkdir -p /Users/$(whoami)/crypto-data/kline_aggregate

# Download data
python src/research/data_utils/bootstrap_klines.py

# Run backtest
make run-backtest
```

### Workflow 2: Using Existing Data

```bash
# Clone repo
git clone https://github.com/jrrpanix/cpp-crypto.git
cd cpp-crypto

# Point to existing data
cat > .env << EOF
DATA_DIR=/Users/johnreynolds/github/data
FLASK_ENV=development
EOF

# Verify data
ls -la /Users/johnreynolds/github/data/kline_aggregate/*.parquet

# Run backtest
make run-backtest
```

### Workflow 3: Multiple Data Sources

```bash
# Testing with small dataset
echo "DATA_DIR=./test_data" > .env
make run-backtest

# Production with full dataset
echo "DATA_DIR=/mnt/data/crypto" > .env
make run-backtest
```

## Related Documentation

- Main README: `README.md`
- Backtest Guide: `docs/BACKTEST_QUICKSTART.md`
- Architecture: `docs/ARCHITECTURE.md`
