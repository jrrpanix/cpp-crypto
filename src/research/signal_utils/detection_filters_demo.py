"""Quick demo to compare detection variants on a CSV of daily bars.
Usage:
  uv run python src/research/signal_utils/detection_filters_demo.py --csv path/to/daily.csv
Columns expected: date, close (others ignored)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import os
import sys

import polars as pl

# Support running as script from repo root or within package
try:
    from signal_utils.detection_filters import apply_detection_filters  # type: ignore
except ImportError:
    here = os.path.abspath(os.path.dirname(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))  # points to src/
    if root not in sys.path:
        sys.path.insert(0, root)
    from research.signal_utils.detection_filters import apply_detection_filters  # type: ignore


def run(csv_path: Path, window: int = 5) -> None:
    df = pl.read_csv(csv_path).with_columns(pl.col("date").strptime(pl.Date, "%Y-%m-%d"))
    df = df.sort("date")

    out = apply_detection_filters(df, window=window)
    print(out.select("date", "close", "ret_window", "ret_mid", "max_day_ret", "up_days", "spread_pass", "cap_pass", "updays_pass", "smooth_pass", "hybrid_pass").tail(20))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True, help="CSV with columns date, close")
    parser.add_argument("--window", type=int, default=5)
    args = parser.parse_args()
    run(args.csv, window=args.window)


if __name__ == "__main__":
    main()
