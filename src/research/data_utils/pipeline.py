"""
Monthly data pipeline orchestrator.
Runs download → parse → daily aggregation → index building in sequence.
Logs each step and tracks overall run in runlog.sqlite.

Usage:
  uv run python src/research/data_utils/pipeline.py --month 2025-01 --symbols BTCUSDT,ETHUSDT
  uv run python src/research/data_utils/pipeline.py --month 2025-01 --all-symbols --skip-download
  uv run python src/research/data_utils/pipeline.py --month 2025-01 --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Support running as script
here = os.path.abspath(os.path.dirname(__file__))
src_root = os.path.abspath(os.path.join(here, "..", ".."))
if src_root not in sys.path:
    sys.path.insert(0, src_root)

try:
    from research.data_utils.config import (
        DEFAULT_SYMBOLS, DOWNLOADS_DIR, KLINES_DIR, KLINES_DAILY_DIR,
        AGGREGATE_DIR, RUNLOG_DB, RUNLOG_METRICS, VERBOSE
    )
    from research.data_utils.runlog import init_db, log_run, update_run
    from research.data_utils.update_klines import update_klines
    from research.data_utils.make_daily import process_directory as make_daily_process
    from research.data_utils.make_aggregate import combine_daily_files
except ImportError:
    from config import (
        DEFAULT_SYMBOLS, DOWNLOADS_DIR, KLINES_DIR, KLINES_DAILY_DIR,
        AGGREGATE_DIR, RUNLOG_DB, RUNLOG_METRICS, VERBOSE
    )
    from runlog import init_db, log_run, update_run
    from update_klines import update_klines
    from make_daily import process_directory as make_daily_process
    from make_aggregate import combine_daily_files


class PipelineLogger:
    """Simple logger for pipeline steps."""
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.steps = []
    
    def info(self, msg: str) -> None:
        if self.verbose:
            print(f"ℹ️  {msg}")
        self.steps.append(("info", msg))
    
    def success(self, msg: str) -> None:
        if self.verbose:
            print(f"✅ {msg}")
        self.steps.append(("success", msg))
    
    def warn(self, msg: str) -> None:
        if self.verbose:
            print(f"⚠️  {msg}")
        self.steps.append(("warn", msg))
    
    def error(self, msg: str) -> None:
        if self.verbose:
            print(f"❌ {msg}")
        self.steps.append(("error", msg))


def step_download(logger: PipelineLogger, symbols: list[str], year_month: str, dry_run: bool = False) -> bool:
    """Step 1: Download latest klines from Binance."""
    logger.info(f"Step 1: Download klines for {year_month}")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would download {len(symbols)} symbols for {year_month}")
        return True
    
    # TODO: Import and call bootstrap_klines.download_all_last_year or get_latest_klines
    logger.warn("Download step not yet implemented; skipping. (Manual download recommended)")
    return True


def step_parse_update(logger: PipelineLogger, symbols: list[str], downloads_dir: Path, klines_dir: Path, dry_run: bool = False) -> bool:
    """Step 2: Parse downloaded zips and update parquet kline files."""
    logger.info(f"Step 2: Parse and update minute-bar klines")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would process {len(symbols)} symbols from {downloads_dir}")
        return True
    
    try:
        update_klines(str(klines_dir), str(downloads_dir))
        logger.success(f"Parsed and updated minute-bar klines")
        return True
    except Exception as e:
        logger.error(f"Parse/update step failed: {e}")
        return False


def step_make_daily(logger: PipelineLogger, klines_dir: Path, daily_dir: Path, dry_run: bool = False) -> bool:
    """Step 3: Aggregate minute bars to daily bars."""
    logger.info(f"Step 3: Aggregate minute bars → daily bars")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would aggregate files from {klines_dir} → {daily_dir}")
        return True
    
    try:
        make_daily_process(str(klines_dir), str(daily_dir))
        logger.success(f"Aggregated minute bars to daily bars")
        return True
    except Exception as e:
        logger.error(f"Daily aggregation step failed: {e}")
        return False


def step_make_aggregate(logger: PipelineLogger, daily_dir: Path, aggregate_dir: Path, dry_run: bool = False) -> bool:
    """Step 4: Combine all daily bars into single aggregate file."""
    logger.info(f"Step 4: Combine daily bars into aggregate")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would combine files from {daily_dir} → {aggregate_dir}")
        return True
    
    try:
        combine_daily_files(daily_dir, aggregate_dir)
        logger.success(f"Combined daily bars into aggregate")
        return True
    except Exception as e:
        logger.error(f"Aggregate step failed: {e}")
        return False


def step_build_indexes(logger: PipelineLogger, daily_dir: Path, indexes_dir: Path, dry_run: bool = False) -> bool:
    """Step 5 (optional): Build market indexes."""
    logger.info(f"Step 5: Build market indexes")
    
    if dry_run:
        logger.info(f"[DRY RUN] Would build indexes from {daily_dir} → {indexes_dir}")
        return True
    
    logger.warn("Index building step not yet implemented; skipping. (Optional; can run separately)")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Monthly data pipeline orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download and process January 2025 for default symbols
  uv run python src/research/data_utils/pipeline.py --month 2025-01
  
  # Process specific symbols
  uv run python src/research/data_utils/pipeline.py --month 2025-01 --symbols BTCUSDT,ETHUSDT
  
  # Skip download (use existing files)
  uv run python src/research/data_utils/pipeline.py --month 2025-01 --skip-download
  
  # Dry run to see what would happen
  uv run python src/research/data_utils/pipeline.py --month 2025-01 --dry-run
        """
    )
    parser.add_argument(
        "--month", type=str, required=True,
        help="Month to process (YYYY-MM, e.g., 2025-01)"
    )
    parser.add_argument(
        "--symbols", type=str, default=None,
        help="Comma-separated symbols (default: DEFAULT_SYMBOLS from config)"
    )
    parser.add_argument(
        "--all-symbols", action="store_true",
        help="Process all symbols (currently just DEFAULT_SYMBOLS)"
    )
    parser.add_argument(
        "--skip-download", action="store_true",
        help="Skip download step; use existing files"
    )
    parser.add_argument(
        "--skip-index", action="store_true",
        help="Skip index building step"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would happen without making changes"
    )
    
    args = parser.parse_args()
    
    # Parse symbols
    if args.symbols:
        symbols = args.symbols.split(",")
    elif args.all_symbols:
        symbols = DEFAULT_SYMBOLS
    else:
        symbols = DEFAULT_SYMBOLS
    
    # Setup logger and run tracking
    logger = PipelineLogger(verbose=VERBOSE)
    init_db(str(RUNLOG_DB))
    
    print("\n" + "="*80)
    print(f"Data Pipeline: {args.month}")
    print(f"Symbols: {len(symbols)} ({', '.join(symbols[:3])}{'...' if len(symbols) > 3 else ''})")
    print(f"Skip Download: {args.skip_download}")
    print(f"Skip Index: {args.skip_index}")
    print(f"Dry Run: {args.dry_run}")
    print("="*80 + "\n")
    
    start_time = time.time()
    run_id = None
    
    try:
        # Log the run start
        run_id = log_run(
            db_path=str(RUNLOG_DB),
            command=f"pipeline.py --month {args.month} --symbols {','.join(symbols[:3])}{'...' if len(symbols) > 3 else ''}",
            config={"month": args.month, "num_symbols": len(symbols), "dry_run": args.dry_run},
            status="running",
            tags=["data_pipeline", args.month],
            notes=f"Processing {args.month} for {len(symbols)} symbols"
        )
        logger.success(f"Run ID: {run_id}")
        
        # Step 1: Download
        if not args.skip_download:
            success = step_download(logger, symbols, args.month, dry_run=args.dry_run)
            if not success:
                logger.error("Download step failed")
                raise RuntimeError("Download step failed")
        else:
            logger.info("Skipping download step")
        
        # Step 2: Parse & Update
        success = step_parse_update(logger, symbols, DOWNLOADS_DIR, KLINES_DIR, dry_run=args.dry_run)
        if not success:
            logger.error("Parse/update step failed")
            raise RuntimeError("Parse/update step failed")
        
        # Step 3: Make Daily
        success = step_make_daily(logger, KLINES_DIR, KLINES_DAILY_DIR, dry_run=args.dry_run)
        if not success:
            logger.error("Daily aggregation step failed")
            raise RuntimeError("Daily aggregation step failed")
        
        # Step 4: Make Aggregate
        success = step_make_aggregate(logger, KLINES_DAILY_DIR, AGGREGATE_DIR, dry_run=args.dry_run)
        if not success:
            logger.error("Aggregate step failed")
            raise RuntimeError("Aggregate step failed")
        
        # Step 5: Build Indexes (optional)
        if not args.skip_index:
            success = step_build_indexes(logger, KLINES_DAILY_DIR, Path("data/indexes"), dry_run=args.dry_run)
            if not success:
                logger.warn("Index building step failed; continuing")
        else:
            logger.info("Skipping index building step")
        
        elapsed = time.time() - start_time
        logger.success(f"Pipeline completed in {elapsed:.1f}s")
        
        # Update run status
        if run_id:
            update_run(
                db_path=str(RUNLOG_DB),
                run_id=run_id,
                status="success",
                duration_ms=int(elapsed * 1000),
                notes=f"Completed {args.month}; {len(symbols)} symbols processed"
            )
        
        print("\n" + "="*80)
        print("✅ Pipeline completed successfully")
        print("="*80 + "\n")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        if run_id:
            update_run(
                db_path=str(RUNLOG_DB),
                run_id=run_id,
                status="failed",
                notes=str(e)
            )
        raise


if __name__ == "__main__":
    main()
