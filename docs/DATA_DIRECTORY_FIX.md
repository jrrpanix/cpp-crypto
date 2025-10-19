# Data Directory Configuration - Summary

## ✅ Problem Solved

**Issue**: Data directory was hardcoded to `./data` inside the project, but you moved it to `/Users/johnreynolds/github/data` for better organization.

**Solution**: Implemented environment variable configuration so any user can specify their data location.

## 🔧 Changes Made

### 1. Environment Configuration Files

**Created `.env.example`** - Template for users
```bash
DATA_DIR=./data  # Default location
```

**Created `.env`** - Your local configuration (git-ignored)
```bash
DATA_DIR=/Users/johnreynolds/github/data
```

**Updated `.gitignore`** - Ignore local .env files
```
.env
.env.local
```

### 2. Makefile Updates

**Added environment variable loading:**
```makefile
# Load environment variables from .env file if it exists
-include .env
export
```

Now all `make` commands automatically use your `DATA_DIR` setting.

### 3. Docker Compose Updates

**Updated `docker-compose-backtest.yml`:**
```yaml
volumes:
  # Uses DATA_DIR from .env, falls back to ./data
  - ${DATA_DIR:-../data}:/app/data:ro
```

### 4. Flask API Updates

**Made `backtest_api.py` smart about finding data:**
```python
def find_data_directory():
    """Find the data directory by checking common locations."""
    possible_paths = [
        Path('/app/data/kline_aggregate'),
        Path('/app/data/aggregate_parquet'),
        Path('/app/data/klines'),
        # ... more fallbacks
    ]
    # Returns first path with .parquet files
```

### 5. Documentation

**Created comprehensive guide:** `docs/DATA_DIRECTORY_SETUP.md`
- Step-by-step setup for new users
- Troubleshooting guide
- Multiple workflow examples

**Updated README.md** - Added first-time setup section

## 🚀 How It Works Now

### For You (Existing Setup)

Your `.env` file points to `/Users/johnreynolds/github/data`:

```bash
# Just run the service
make run-backtest

# Docker automatically uses DATA_DIR=/Users/johnreynolds/github/data
# API finds parquet files in /app/data/klines
# ✅ Works!
```

### For New Users Cloning the Repo

```bash
# 1. Clone repo
git clone https://github.com/jrrpanix/cpp-crypto.git
cd cpp-crypto

# 2. Setup environment
cp .env.example .env
# Edit .env to set DATA_DIR

# 3. Create or point to data directory
mkdir -p ./data/klines
# or set DATA_DIR to existing location

# 4. Run backtest
make run-backtest
```

## 📊 Verification

### Check Environment
```bash
cat .env
# Shows: DATA_DIR=/Users/johnreynolds/github/data
```

### Check API Logs
```bash
docker logs backtest-api
# Shows: 📁 Using data directory: /app/data/klines
```

### Check Symbols
```bash
curl http://localhost:5001/api/symbols
# Returns: {"success": true, "symbols": ["1000BONKUSDT", ...]}
```

## 🎯 Benefits

### 1. **Flexibility**
- Data can be anywhere on your system
- Different users = different locations
- Easy to switch between datasets (test vs prod)

### 2. **Portability**
- New users don't need specific directory structure
- Works on macOS, Linux, Windows (with WSL)
- CI/CD can use test data

### 3. **Clean Git History**
- No data files in repo
- No conflicts from data changes
- .env is git-ignored

### 4. **Automatic Detection**
- API tries multiple common locations
- Finds parquet files automatically
- Helpful error messages if not found

## 📁 Supported Data Directory Structures

The API automatically detects these structures:

```
{DATA_DIR}/
├── kline_aggregate/          ✅ Primary (recommended)
│   └── BTCUSDT_1m_*.parquet
├── aggregate_parquet/        ✅ Alternative
│   └── BTCUSDT_1m_*.parquet
└── klines/                   ✅ Your current setup
    └── BTCUSDT_1m_*.parquet
```

## 🔄 Migration Path

### Before (Hardcoded)
```yaml
volumes:
  - ../data:/app/data:ro  # Only works if data is in ./data
```

### After (Configurable)
```yaml
volumes:
  - ${DATA_DIR:-../data}:/app/data:ro  # Uses DATA_DIR or defaults to ./data
```

## 📝 Quick Reference

| Task | Command |
|------|---------|
| Set data location | Edit `.env` file |
| Check current setting | `cat .env` |
| Restart after change | `make stop-backtest && make run-backtest` |
| View data path used | `docker logs backtest-api \| grep "Using data"` |
| Test API connection | `curl http://localhost:5001/api/symbols` |

## 🎓 For Team Members

When sharing this project, tell new users to:

1. **Copy the environment template**
   ```bash
   cp .env.example .env
   ```

2. **Set their data directory**
   ```bash
   echo "DATA_DIR=/path/to/their/data" >> .env
   ```

3. **Run the service**
   ```bash
   make run-backtest
   ```

That's it! No hardcoded paths, no manual docker-compose edits.

## 🐛 Common Issues & Solutions

### "No symbols available"
- Check `.env` has correct DATA_DIR
- Verify directory has .parquet files
- Check `docker logs backtest-api`

### DATA_DIR not working
- Make sure it's in `.env` (not `.env.example`)
- Restart services: `make stop-backtest && make run-backtest`
- Verify: `echo $DATA_DIR`

### Permission errors
- Make directory readable: `chmod -R +r $DATA_DIR`
- Docker user needs access to the path

## 🚀 Next Steps

This same pattern should be applied to:
- [ ] Other docker-compose files (websocket, live, test)
- [ ] Python scripts that read data
- [ ] C++ applications that need data paths
- [ ] Documentation for data acquisition scripts

Would you like me to update the other services too?
