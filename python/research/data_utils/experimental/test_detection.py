"""
Test program for daily_loader + detection_filters.
Loads parquet daily data and computes all detection variants.

Run from repo root:
  uv run python src/research/data_utils/test_detection.py --dir /workspace/data/klines_daily --symbol BTCUSDT --window 5
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Support running as script
here = os.path.abspath(os.path.dirname(__file__))
src_root = os.path.abspath(os.path.join(here, "..", ".."))
if src_root not in sys.path:
    sys.path.insert(0, src_root)

import polars as pl

from research.data_utils.daily_loader import load_daily_concat
from research.signal_utils.detection_filters import apply_detection_filters


def main():
    parser = argparse.ArgumentParser(
        description="Test daily loader + detection filters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  uv run python src/research/data_utils/test_detection.py \\
    --dir /workspace/data/klines_daily --symbol BTCUSDT --window 5

  uv run python src/research/data_utils/test_detection.py \\
    --dir /workspace/data/klines_daily --symbol ETHUSDT --window 3 \\
    --target 0.03 --max-single 0.02
        """,
    )
    parser.add_argument("--dir", type=str, required=True, help="Path to daily parquet directory")
    parser.add_argument(
        "--symbol", type=str, default=None, help="Filter to single symbol (optional)"
    )
    parser.add_argument("--window", type=int, default=5, help="Detection window in days")
    parser.add_argument("--target", type=float, default=0.05, help="Target move (5% = 0.05)")
    parser.add_argument("--mid-offset", type=int, default=3, help="Mid-window checkpoint offset")
    parser.add_argument("--mid-threshold", type=float, default=0.02, help="Mid-window threshold")
    parser.add_argument("--max-single", type=float, default=0.03, help="Max single-day move")
    parser.add_argument("--up-days", type=int, default=3, help="Min up days required")
    parser.add_argument("--max-std", type=float, default=0.02, help="Max daily return std")
    parser.add_argument("--rows", type=int, default=30, help="Show last N rows")

    args = parser.parse_args()

    print(f"\n{'='*80}")
    print(f"Daily Detection Filter Test")
    print(f"{'='*80}")
    print(f"Directory: {args.dir}")
    print(f"Symbol: {args.symbol or 'all'}")
    print(f"Window: {args.window} days")
    print(f"Target move: {args.target*100:.1f}%")
    print(f"Mid-window threshold: {args.mid_threshold*100:.1f}% by day {args.mid_offset}")
    print(f"Max single-day: {args.max_single*100:.1f}%")
    print(f"Min up-days: {args.up_days}")
    print(f"Max daily std: {args.max_std*100:.1f}%")
    print(f"{'='*80}\n")

    try:
        # Load data
        print("Loading daily parquet data...")
        df = load_daily_concat(
            args.dir,
            symbol=args.symbol,
            use_latest=True,
        )
        print(f"Loaded {len(df)} rows, columns: {df.columns}")

        # Sort by date if present
        if "open_time" in df.columns:
            df = df.sort("open_time")
        elif "date" in df.columns:
            df = df.sort("date")

        # Ensure close column exists
        if "close" not in df.columns:
            print("ERROR: 'close' column not found")
            return

        # Apply detection filters
        print("\nApplying detection filters...")
        df_out = apply_detection_filters(
            df,
            window=args.window,
            target=args.target,
            mid_offset=args.mid_offset,
            mid_threshold=args.mid_threshold,
            max_single=args.max_single,
            up_days_required=args.up_days,
            max_std=args.max_std,
        )

        # Show last N rows with detection results
        date_col = "open_time" if "open_time" in df_out.columns else "date"
        show_cols = [
            date_col,
            "close",
            "ret_window",
            "ret_mid",
            "max_day_ret",
            "up_days",
            "spread_pass",
            "cap_pass",
            "updays_pass",
            "smooth_pass",
            "hybrid_pass",
        ]
        show_cols = [c for c in show_cols if c in df_out.columns]

        print(f"\nLast {args.rows} rows (detection flags):\n")
        print(df_out.select(show_cols).tail(args.rows))

        # Summary stats
        print(f"\n{'='*80}")
        print("Summary Statistics")
        print(f"{'='*80}")
        for variant in ["spread_pass", "cap_pass", "updays_pass", "smooth_pass", "hybrid_pass"]:
            if variant in df_out.columns:
                count = df_out.filter(pl.col(variant)).shape[0]
                pct = 100.0 * count / len(df_out) if len(df_out) > 0 else 0
                print(f"{variant:15s}: {count:5d} / {len(df_out):5d} ({pct:5.1f}%)")

        print(f"{'='*80}\n")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
