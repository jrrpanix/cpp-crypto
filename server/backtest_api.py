"""
Backtesting API Server for window_sim trading strategy.
Simple Flask API that runs backtests and returns results.
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import sys
import io
import os
from pathlib import Path
import base64
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import polars as pl
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import multiprocessing

# Add paths for module imports
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, '/app/data_utils')  # Docker path for data_utils
sys.path.insert(0, str(Path(__file__).parent / 'data_utils'))  # Local fallback

# Add parent directory to path to import window_sim
try:
    from signal_utils import window_sim
except ImportError:
    # Fallback for local development
    sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'research'))
    from signal_utils import window_sim

# Import calc_adv - should work now with paths set
calc_adv_module = None
try:
    # Try direct import (should work with paths above)
    import calc_adv as calc_adv_module
    print("✅ calc_adv module loaded successfully")
except ImportError as e:
    print(f"⚠️  Warning: calc_adv module not found: {e}")
    print(f"   Python path: {sys.path[:5]}")
    calc_adv_module = None

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Configure data directory - support both Docker and local paths
# Check multiple common locations in order of preference
def find_data_directory():
    """Find the data directory by checking common locations."""
    possible_paths = [
        Path(os.getenv('DATA_PATH', '')),  # Explicitly set path
        Path('/app/data/kline_aggregate'),  # Docker mount - new structure
        Path('/app/data/aggregate_parquet'),  # Docker mount - old structure
        Path('/app/data/klines'),  # Docker mount - alternative
        Path('/workspace/data/klines'),  # Container workspace
        Path(__file__).parent.parent / 'data' / 'kline_aggregate',  # Local - new
        Path(__file__).parent.parent / 'data' / 'aggregate_parquet',  # Local - old
        Path(__file__).parent.parent / 'data' / 'klines',  # Local - alternative
    ]
    
    for path in possible_paths:
        if path.exists() and path.is_dir():
            # Check if it has parquet files
            if list(path.glob('*.parquet')):
                print(f"📁 Using data directory: {path}")
                return path
    
    # Default fallback
    default = Path('/app/data/kline_aggregate')
    print(f"⚠️  No data directory found, using default: {default}")
    return default

DATA_DIR = find_data_directory()

@app.route('/api/symbols', methods=['GET'])
def get_symbols():
    """Get list of available symbols from parquet files."""
    try:
        # Find all parquet files
        parquet_files = list(DATA_DIR.glob("*_1m_*.parquet"))
        
        # Extract unique symbols
        symbols = set()
        for file in parquet_files:
            # Extract symbol from filename (e.g., BTCUSDT_1m_2024-01-01_2025-01-01.parquet)
            filename = file.stem
            symbol = filename.split('_1m_')[0]
            symbols.add(symbol)
        
        return jsonify({
            "success": True,
            "symbols": sorted(list(symbols))
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/symbol-info/<symbol>', methods=['GET'])
def get_symbol_info(symbol):
    """Get date range and row count for a symbol."""
    try:
        # Find matching parquet file
        matching_files = list(DATA_DIR.glob(f"{symbol}_1m_*.parquet"))
        
        if not matching_files:
            return jsonify({
                "success": False,
                "error": f"No data found for symbol {symbol}"
            }), 404
        
        # Use most recent file
        parquet_file = sorted(matching_files)[-1]
        
        # Read metadata
        df = pl.read_parquet(parquet_file)
        
        return jsonify({
            "success": True,
            "symbol": symbol,
            "file": str(parquet_file.name),
            "start_date": str(df["open_time"].min()),
            "end_date": str(df["open_time"].max()),
            "rows": len(df),
            "data_points": len(df)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/backtest', methods=['POST'])
def run_backtest():
    """
    Run backtest with provided parameters.
    
    Expected JSON body:
    {
        "symbol": "BTCUSDT",
        "up_threshold": 0.01,
        "up_direction": "B",
        "down_threshold": -0.02,
        "down_direction": "S",
        "detection_window": 30,
        "hold_window": 30,
        "position_size": 1000,
        "position_limit": 1,
        "fee_rate": 0.0003,
        "num_accounts": 1,
        "start_date": "2024-01-01" (optional),
        "include_plot": false (optional, default false),
        "include_trades": false (optional, default false)
    }
    """
    try:
        # Get parameters from request
        params = request.json
        
        print(f"DEBUG: Received backtest request for symbol: {params.get('symbol')}")
        print(f"DEBUG: start_date value: {repr(params.get('start_date'))}")
        
        symbol = params.get('symbol')
        up_threshold = float(params.get('up_threshold'))
        up_direction = params.get('up_direction', 'B')
        down_threshold = float(params.get('down_threshold'))
        down_direction = params.get('down_direction', 'S')
        detection_window = int(params.get('detection_window'))
        hold_window = int(params.get('hold_window'))
        position_size = float(params.get('position_size'))
        position_limit = int(params.get('position_limit', 1))
        fee_rate = float(params.get('fee_rate', 0.0003))
        num_accounts = int(params.get('num_accounts', 1))
        start_date = params.get('start_date')
        
        # Performance optimizations: allow skipping expensive operations
        include_plot = params.get('include_plot', False)
        include_trades = params.get('include_trades', False)
        
        print(f"DEBUG: Parsed start_date: {repr(start_date)}")
        
        # Validate inputs
        if up_threshold <= 0:
            return jsonify({"success": False, "error": "Up threshold must be positive"}), 400
        if down_threshold >= 0:
            return jsonify({"success": False, "error": "Down threshold must be negative"}), 400
        
        # Find parquet file
        matching_files = list(DATA_DIR.glob(f"{symbol}_1m_*.parquet"))
        
        if not matching_files:
            return jsonify({
                "success": False,
                "error": f"No data found for symbol {symbol}"
            }), 404
        
        # Use most recent file
        parquet_file = str(sorted(matching_files)[-1])
        
        # Run simulation (suppress verbose output)
        # Run the simulation using window_sim module
        trades_df, summary = window_sim.run_simulation_from_file(
            parquet_file,
            start_date,
            up_threshold,
            up_direction,
            down_threshold,
            down_direction,
            detection_window,
            hold_window,
            position_size,
            position_limit,
            fee_rate,
            num_accounts,
            verbose=False
        )
        
        # Generate cumulative PnL plot as base64 (OPTIONAL - expensive)
        plot_base64 = None
        if include_plot and len(trades_df) > 0:
            plot_base64 = generate_plot_base64(trades_df, symbol)
        # Generate cumulative PnL plot as base64 (OPTIONAL - expensive)
        plot_base64 = None
        if include_plot and len(trades_df) > 0:
            plot_base64 = generate_plot_base64(trades_df, symbol)
        
        # Extract cumulative PnL time series for aggregation
        cumulative_pnl_series = []
        if len(trades_df) > 0:
            trades_sorted = trades_df.sort("exit_time")
            trades_sorted = trades_sorted.with_columns(
                [pl.col("net_profit_dollars").cum_sum().alias("cumulative_pnl")]
            )
            cumulative_pnl_series = [
                {"time": row["exit_time"].isoformat() if hasattr(row["exit_time"], 'isoformat') else str(row["exit_time"]), 
                 "pnl": row["cumulative_pnl"]}
                for row in trades_sorted.select(["exit_time", "cumulative_pnl"]).to_dicts()
            ]
        
        # Prepare response
        response = {
            "success": True,
            "summary": summary,
            "num_trades": len(trades_df),
            "cumulative_pnl_series": cumulative_pnl_series  # Time series for aggregation
        }
        
        # Add optional expensive data only if requested
        if include_plot:
            response["plot"] = plot_base64
        if include_trades:
            response["trades"] = trades_df.head(100).to_dicts() if len(trades_df) > 0 else []
        
        return jsonify(response)
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


def process_single_symbol(symbol: str, data_dir: Path, params: dict) -> dict:
    """
    Worker function to process a single symbol backtest.
    Designed to be called by ProcessPoolExecutor for parallel execution.
    
    Args:
        symbol: Trading symbol (e.g., 'BTCUSDT')
        data_dir: Path to data directory
        params: Dictionary with backtest parameters
        
    Returns:
        Dictionary with result or error information
    """
    try:
        # Import here to avoid issues with multiprocessing
        import polars as pl
        import sys
        from pathlib import Path
        
        # Re-import window_sim in worker process
        sys.path.insert(0, str(Path(__file__).parent))
        try:
            from signal_utils import window_sim
        except ImportError:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'research'))
            from signal_utils import window_sim
        
        # Find parquet file
        matching_files = list(data_dir.glob(f"{symbol}_1m_*.parquet"))
        
        if not matching_files:
            return {
                "symbol": symbol,
                "success": False,
                "error": f"No data found for symbol {symbol}"
            }
        
        # Use most recent file
        parquet_file = str(sorted(matching_files)[-1])
        
        # Extract parameters
        start_date = params.get('start_date')
        up_threshold = params['up_threshold']
        up_direction = params['up_direction']
        down_threshold = params['down_threshold']
        down_direction = params['down_direction']
        detection_window = params['detection_window']
        hold_window = params['hold_window']
        position_size = params['position_size']
        position_limit = params['position_limit']
        fee_rate = params['fee_rate']
        num_accounts = params['num_accounts']
        
        # Run simulation
        trades_df, summary = window_sim.run_simulation_from_file(
            parquet_file,
            start_date,
            up_threshold,
            up_direction,
            down_threshold,
            down_direction,
            detection_window,
            hold_window,
            position_size,
            position_limit,
            fee_rate,
            num_accounts,
            verbose=False
        )
        
        # Extract cumulative PnL time series
        cumulative_pnl_series = []
        if len(trades_df) > 0:
            trades_sorted = trades_df.sort("exit_time")
            trades_sorted = trades_sorted.with_columns(
                [pl.col("net_profit_dollars").cum_sum().alias("cumulative_pnl")]
            )
            cumulative_pnl_series = [
                {"time": row["exit_time"].isoformat() if hasattr(row["exit_time"], 'isoformat') else str(row["exit_time"]), 
                 "pnl": row["cumulative_pnl"]}
                for row in trades_sorted.select(["exit_time", "cumulative_pnl"]).to_dicts()
            ]
        
        return {
            "symbol": symbol,
            "success": True,
            "summary": summary,
            "num_trades": len(trades_df),
            "cumulative_pnl_series": cumulative_pnl_series
        }
        
    except Exception as e:
        import traceback
        return {
            "symbol": symbol,
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


@app.route('/api/backtest/batch', methods=['POST'])
def run_batch_backtest():
    """
    Run backtests for multiple symbols with same parameters.
    More efficient than calling /api/backtest multiple times.
    
    Expected JSON body:
    {
        "symbols": ["BTCUSDT", "ETHUSDT", ...],
        "params": {
            "up_threshold": 0.01,
            "up_direction": "B",
            "down_threshold": -0.02,
            "down_direction": "S",
            "detection_window": 30,
            "hold_window": 30,
            "position_size": 1000,
            "position_limit": 1,
            "fee_rate": 0.0003,
            "num_accounts": 1,
            "start_date": "2024-01-01" (optional)
        }
    }
    """
    try:
        data = request.json
        symbols = data.get('symbols', [])
        params = data.get('params', {})
        
        if not symbols:
            return jsonify({"success": False, "error": "No symbols provided"}), 400
        
        print(f"DEBUG: Batch backtest for {len(symbols)} symbols using parallel processing")
        
        # Extract and validate parameters
        up_threshold = float(params.get('up_threshold'))
        up_direction = params.get('up_direction', 'B')
        down_threshold = float(params.get('down_threshold'))
        down_direction = params.get('down_direction', 'S')
        detection_window = int(params.get('detection_window'))
        hold_window = int(params.get('hold_window'))
        position_size = float(params.get('position_size'))
        position_limit = int(params.get('position_limit', 1))
        fee_rate = float(params.get('fee_rate', 0.0003))
        num_accounts = int(params.get('num_accounts', 1))
        start_date = params.get('start_date')
        
        # Validate inputs
        if up_threshold <= 0:
            return jsonify({"success": False, "error": "Up threshold must be positive"}), 400
        if down_threshold >= 0:
            return jsonify({"success": False, "error": "Down threshold must be negative"}), 400
        
        # Prepare parameters dict for worker function
        worker_params = {
            'up_threshold': up_threshold,
            'up_direction': up_direction,
            'down_threshold': down_threshold,
            'down_direction': down_direction,
            'detection_window': detection_window,
            'hold_window': hold_window,
            'position_size': position_size,
            'position_limit': position_limit,
            'fee_rate': fee_rate,
            'num_accounts': num_accounts,
            'start_date': start_date
        }
        
        # Use ThreadPoolExecutor for compatibility with Flask
        # (ProcessPoolExecutor has issues with spawn and Flask's request context)
        max_workers = min(len(symbols), multiprocessing.cpu_count())
        print(f"DEBUG: Using {max_workers} parallel workers (ThreadPool)", flush=True)
        
        results = []
        executor = None
        
        try:
            print(f"DEBUG: Creating ThreadPoolExecutor...", flush=True)
            executor = ThreadPoolExecutor(max_workers=max_workers)
            print(f"DEBUG: Executor created, submitting {len(symbols)} jobs...", flush=True)
            
            # Submit all jobs
            future_to_symbol = {
                executor.submit(process_single_symbol, symbol, DATA_DIR, worker_params): symbol
                for symbol in symbols
            }
            print(f"DEBUG: All {len(future_to_symbol)} jobs submitted, waiting for completion...", flush=True)
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                print(f"DEBUG: Future completed for {symbol}, getting result...", flush=True)
                try:
                    result = future.result(timeout=120)  # 2 minute timeout per symbol
                    results.append(result)
                    completed += 1
                    print(f"DEBUG: Completed {completed}/{len(symbols)}: {symbol} - {result.get('num_trades', 0)} trades", flush=True)
                except Exception as e:
                    import traceback
                    print(f"ERROR: Exception processing {symbol}: {str(e)}", flush=True)
                    print(f"ERROR: Traceback: {traceback.format_exc()}", flush=True)
                    results.append({
                        "symbol": symbol,
                        "success": False,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    })
        finally:
            # Explicitly shutdown and cleanup the executor
            if executor is not None:
                print(f"DEBUG: Shutting down executor with {max_workers} workers", flush=True)
                executor.shutdown(wait=True, cancel_futures=False)
                print(f"DEBUG: Executor shutdown complete", flush=True)
        
        return jsonify({
            "success": True,
            "results": results,
            "total_symbols": len(symbols),
            "successful": sum(1 for r in results if r.get("success", False))
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


def generate_plot_base64(trades_df: pl.DataFrame, symbol: str) -> str:
    """Generate cumulative PnL plot and return as base64 string."""
    # Sort by exit time
    trades_df = trades_df.sort("exit_time")
    
    # Calculate cumulative PnL
    trades_df = trades_df.with_columns(
        [pl.col("net_profit_dollars").cum_sum().alias("cumulative_pnl")]
    )
    
    # Create plot
    plt.figure(figsize=(12, 6))
    
    exit_times = trades_df["exit_time"].to_list()
    cum_pnl = trades_df["cumulative_pnl"].to_list()
    
    plt.plot(exit_times, cum_pnl, linewidth=2, color="steelblue")
    plt.axhline(y=0, color="red", linestyle="--", alpha=0.5, linewidth=1)
    
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Cumulative PnL ($)", fontsize=12)
    plt.title(f"Cumulative PnL - {symbol}", fontsize=14, fontweight="bold")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    # Save to BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    # Encode as base64 (return just the base64 string, JS will add the data URI prefix)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64


@app.route('/api/daily-data', methods=['POST'])
def get_daily_data():
    """
    Get daily OHLCV data for selected symbols from aggregate file.
    
    Expected JSON body:
    {
        "symbols": ["BTCUSDT", "ETHUSDT", ...],
        "start_date": "2024-07-01" (optional),
        "end_date": "2025-09-30" (optional)
    }
    
    Returns:
    {
        "success": true,
        "data": {
            "BTCUSDT": [
                {
                    "date": "2024-07-01T00:00:00",
                    "open": 63000.5,
                    "high": 64000.0,
                    "low": 62500.0,
                    "close": 63500.0,
                    "volume": 1234.56
                },
                ...
            ],
            ...
        },
        "date_range": {"start": "2024-07-01", "end": "2025-09-30"}
    }
    """
    try:
        data = request.json
        symbols = data.get('symbols', [])
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if not symbols:
            return jsonify({"success": False, "error": "No symbols provided"}), 400
        
        # Find aggregate parquet file
        agg_dir = Path('/app/data/klines_aggregate') if Path('/app/data/klines_aggregate').exists() else Path(__file__).parent.parent / 'data' / 'klines_aggregate'
        
        # Look for AGG_*.pq file
        agg_files = list(agg_dir.glob('AGG_*.pq'))
        
        if not agg_files:
            return jsonify({"success": False, "error": "No aggregate data file found"}), 404
        
        # Use most recent file (sort by filename which includes date)
        agg_file = sorted(agg_files)[-1]
        print(f"DEBUG: Using aggregate file: {agg_file}")
        
        # Read aggregate data
        df = pl.read_parquet(agg_file)
        
        # Filter by symbols
        df = df.filter(pl.col('symbol').is_in(symbols))
        
        # Filter by date range if provided
        if start_date:
            start_dt = pl.datetime(year=int(start_date[:4]), month=int(start_date[5:7]), day=int(start_date[8:10]))
            df = df.filter(pl.col('open_time') >= start_dt)
        
        if end_date:
            end_dt = pl.datetime(year=int(end_date[:4]), month=int(end_date[5:7]), day=int(end_date[8:10]))
            df = df.filter(pl.col('open_time') <= end_dt)
        
        # Sort by symbol and time
        df = df.sort(['symbol', 'open_time'])
        
        # Group by symbol and prepare response
        result_data = {}
        for symbol in symbols:
            symbol_df = df.filter(pl.col('symbol') == symbol)
            
            if len(symbol_df) == 0:
                result_data[symbol] = []
                continue
            
            # Convert to list of dictionaries
            symbol_data = [
                {
                    "date": row["open_time"].isoformat() if hasattr(row["open_time"], 'isoformat') else str(row["open_time"]),
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"],
                    "volume": row["volume"]
                }
                for row in symbol_df.select(["open_time", "open", "high", "low", "close", "volume"]).to_dicts()
            ]
            result_data[symbol] = symbol_data
        
        # Get actual date range from data
        actual_start = df["open_time"].min()
        actual_end = df["open_time"].max()
        
        return jsonify({
            "success": True,
            "data": result_data,
            "date_range": {
                "start": actual_start.isoformat() if hasattr(actual_start, 'isoformat') else str(actual_start),
                "end": actual_end.isoformat() if hasattr(actual_end, 'isoformat') else str(actual_end)
            },
            "total_symbols": len(symbols),
            "file": agg_file.name
        })
        
    except Exception as e:
        import traceback
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/api/calculate-adv', methods=['POST'])
def calculate_adv():
    """
    Calculate Average Daily Volume (ADV) for top symbols.
    
    Expected JSON body:
    {
        "units": "months" or "weeks",
        "interval": 1-12,
        "top_n": 1-100,
        "drop_n": 0-99 (optional, default 0)
    }
    
    Returns:
    {
        "success": true,
        "data": [
            {
                "begin_date": "2024-07-01",
                "end_date": "2024-07-31",
                "symbol": "BTCUSDT",
                "adv": 1234567890.50,
                "rank": 11,
                "weight": 0.45
            },
            ...
        ]
    }
    """
    try:
        data = request.json
        units = data.get('units', 'months')
        interval = int(data.get('interval', 1))
        top_n = int(data.get('top_n', 10))
        drop_n = int(data.get('drop_n', 0))
        
        # Validate inputs
        if units not in ['months', 'weeks']:
            return jsonify({"success": False, "error": "units must be 'months' or 'weeks'"}), 400
        
        if interval < 1 or interval > 12:
            return jsonify({"success": False, "error": "interval must be between 1 and 12"}), 400
        
        if top_n < 1 or top_n > 500:
            return jsonify({"success": False, "error": "top_n must be between 1 and 500"}), 400
        
        if drop_n < 0 or drop_n >= top_n:
            return jsonify({"success": False, "error": f"drop_n must be between 0 and {top_n - 1}"}), 400
        
        # Find aggregate parquet file
        agg_dir = Path('/workspace/data/klines_aggregate') if Path('/workspace/data/klines_aggregate').exists() else Path('/app/data/klines_aggregate') if Path('/app/data/klines_aggregate').exists() else Path(__file__).parent.parent / 'data' / 'klines_aggregate'
        
        # Look for AGG_*.pq file
        agg_files = list(agg_dir.glob('AGG_*.pq'))
        
        if not agg_files:
            return jsonify({"success": False, "error": "No aggregate data file found"}), 404
        
        # Use most recent file (sort by filename which includes date)
        agg_file = sorted(agg_files)[-1]
        print(f"DEBUG: Using aggregate file for ADV: {agg_file}")
        
        # Read aggregate data
        df = pl.read_parquet(agg_file)
        
        # Filter to USDT symbols (default behavior)
        df = df.filter(pl.col('symbol').str.ends_with('USDT'))
        
        if drop_n > 0:
            remaining = top_n - drop_n
            print(f"DEBUG: Calculating {interval}-{units} ADV for top {top_n}, dropping top {drop_n}, keeping ranks {drop_n + 1}-{top_n} ({remaining} symbols)...")
        else:
            print(f"DEBUG: Calculating {interval}-{units} ADV for top {top_n} symbols...")
        print(f"DEBUG: Input data: {len(df)} rows, {df['symbol'].n_unique()} unique symbols")
        
        # Check if calc_adv module is available
        if calc_adv_module is None:
            return jsonify({
                "success": False,
                "error": "calc_adv module not available. Please check server logs."
            }), 500
        
        # Calculate ADV using calc_adv module
        result_df = calc_adv_module.calculate_adv(
            df=df,
            interval=interval,
            units=units,
            top_n=top_n,
            drop_n=drop_n
        )
        
        print(f"DEBUG: Result: {len(result_df)} rows")
        
        # Convert to list of dictionaries for JSON response
        result_data = []
        for row in result_df.to_dicts():
            item = {
                "begin_date": row["begin_date"].isoformat() if hasattr(row["begin_date"], 'isoformat') else str(row["begin_date"]),
                "end_date": row["end_date"].isoformat() if hasattr(row["end_date"], 'isoformat') else str(row["end_date"]),
                "symbol": row["symbol"],
                "adv": float(row["adv"]),
                "weight": float(row["weight"])
            }
            # Add rank if present (will be present when top_n is specified)
            if "rank" in row:
                item["rank"] = int(row["rank"])
            result_data.append(item)
        
        return jsonify({
            "success": True,
            "data": result_data,
            "total_periods": len(set(r["begin_date"] for r in result_data)),
            "total_symbols": len(set(r["symbol"] for r in result_data)),
            "file": agg_file.name,
            "drop_n": drop_n
        })
        
    except Exception as e:
        import traceback
        print(f"ERROR: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "backtest-api"})


# ============================================================================
# Static file serving routes (replaces nginx)
# ============================================================================

# Determine frontend directory based on environment
# In Docker: /app/frontend/backtest (mounted from ../frontend/backtest)
# Locally: ../frontend/backtest relative to this file
FRONTEND_DIR = Path('/app/frontend/backtest') if Path('/app/frontend/backtest').exists() else Path(__file__).parent.parent / 'frontend' / 'backtest'

@app.route('/')
def landing():
    """Serve the landing page (index.html)."""
    return send_file(FRONTEND_DIR / 'index.html')


@app.route('/multisymbol.html')
def multisymbol_page():
    """Serve the multi-symbol backtest page."""
    return send_file(FRONTEND_DIR / 'multisymbol.html')


@app.route('/single-symbol.html')
def single_symbol_page():
    """Serve the single-symbol backtest page."""
    return send_file(FRONTEND_DIR / 'single-symbol.html')


@app.route('/multisymbol.js')
def multisymbol_js():
    """Serve the multi-symbol JavaScript."""
    return send_file(FRONTEND_DIR / 'multisymbol.js', mimetype='application/javascript')


@app.route('/single-symbol.js')
def single_symbol_js():
    """Serve the single-symbol JavaScript."""
    return send_file(FRONTEND_DIR / 'single-symbol.js', mimetype='application/javascript')


@app.route('/daily.html')
def daily_page():
    """Serve the daily data visualization page."""
    return send_file(FRONTEND_DIR / 'daily.html')


@app.route('/daily.js')
def daily_js():
    """Serve the daily data JavaScript."""
    return send_file(FRONTEND_DIR / 'daily.js', mimetype='application/javascript')


@app.route('/adv.html')
def adv_page():
    """Serve the ADV analysis page."""
    return send_file(FRONTEND_DIR / 'adv.html')


@app.route('/adv.js')
def adv_js():
    """Serve the ADV analysis JavaScript."""
    return send_file(FRONTEND_DIR / 'adv.js', mimetype='application/javascript')


if __name__ == '__main__':
    # For development
    app.run(host='0.0.0.0', port=5000, debug=True)
