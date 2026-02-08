"""Utilities to rank runs and summarize Sharpe distributions across many trials."""

from __future__ import annotations

import argparse
import glob
import sqlite3
from pathlib import Path
from typing import List, Optional, Tuple

import polars as pl

DEFAULT_DB_PATH = Path("data/runlog.sqlite")
DEFAULT_METRICS_GLOB = "data/run_metrics/*.parquet"


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def load_runs(db_path: Path = DEFAULT_DB_PATH) -> pl.DataFrame:
    if not db_path.exists():
        return pl.DataFrame()
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM runs").fetchall()
    return pl.DataFrame(rows)


def load_metrics(metrics_glob: str = DEFAULT_METRICS_GLOB) -> pl.DataFrame:
    files = glob.glob(metrics_glob)
    if not files:
        return pl.DataFrame()
    return pl.scan_parquet(files).collect()


def sharpe_ranking(metrics_df: pl.DataFrame, top_n: int = 20) -> pl.DataFrame:
    if metrics_df.is_empty() or "metric" not in metrics_df.columns:
        return pl.DataFrame()
    if "run_id" not in metrics_df.columns:
        return pl.DataFrame()
    sharpe_df = metrics_df.filter(pl.col("metric") == "sharpe")
    if sharpe_df.is_empty():
        return pl.DataFrame()
    return (
        sharpe_df.sort(pl.col("value").desc())
        .select("run_id", pl.col("value").alias("sharpe"))
        .head(top_n)
    )


def sharpe_summary(metrics_df: pl.DataFrame) -> pl.DataFrame:
    if metrics_df.is_empty() or "metric" not in metrics_df.columns:
        return pl.DataFrame()
    sharpe_df = metrics_df.filter(pl.col("metric") == "sharpe")
    if sharpe_df.is_empty():
        return pl.DataFrame()
    return sharpe_df.select(
        pl.col("value").mean().alias("mean"),
        pl.col("value").median().alias("median"),
        pl.col("value").quantile(0.9).alias("p90"),
        pl.col("value").quantile(0.99).alias("p99"),
        pl.col("value").max().alias("max"),
        pl.count().alias("n"),
    )


def attach_metadata(top_df: pl.DataFrame, runs_df: pl.DataFrame) -> pl.DataFrame:
    if top_df.is_empty() or runs_df.is_empty():
        return top_df
    return top_df.join(runs_df, on="run_id", how="left")


def cli(db_path: Path, metrics_glob: str, top_n: int) -> None:
    runs_df = load_runs(db_path)
    metrics_df = load_metrics(metrics_glob)

    summary = sharpe_summary(metrics_df)
    top = sharpe_ranking(metrics_df, top_n=top_n)
    top_with_meta = attach_metadata(top, runs_df)

    print("Sharpe summary:")
    print(summary if not summary.is_empty() else "(no sharpe metrics found)")
    print()
    print(f"Top {top_n} runs by Sharpe:")
    print(top_with_meta if not top_with_meta.is_empty() else "(no sharpe metrics found)")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Rank runs by Sharpe and summarize distribution.")
    p.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to runlog.sqlite")
    p.add_argument(
        "--metrics-glob",
        type=str,
        default=DEFAULT_METRICS_GLOB,
        help="Glob for metrics parquet files",
    )
    p.add_argument("--top", type=int, default=20, help="Number of top runs to show")
    return p


def main() -> None:
    args = build_parser().parse_args()
    cli(db_path=args.db, metrics_glob=args.metrics_glob, top_n=args.top)


if __name__ == "__main__":
    main()
