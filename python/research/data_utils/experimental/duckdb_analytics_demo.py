"""
Demo: DuckDB analytics for runs and metrics.
Assumes runlog.sqlite and run_metrics/*.parquet exist.

Run from repo root:
  uv add duckdb  # if not already installed
  uv run python src/research/data_utils/duckdb_analytics_demo.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

here = os.path.abspath(os.path.dirname(__file__))
src_root = os.path.abspath(os.path.join(here, "..", ".."))
if src_root not in sys.path:
    sys.path.insert(0, src_root)

from research.data_utils.duckdb_analytics import (
    HAS_DUCKDB,
    build_con,
    query_parquet,
    top_runs_by_sharpe,
    universe_performance,
)


def demo():
    if not HAS_DUCKDB:
        print("❌ DuckDB not installed. Install with: uv add duckdb")
        return

    print("\n" + "=" * 80)
    print("DuckDB Analytics Demo")
    print("=" * 80)

    db_path = "data/runlog.sqlite"
    metrics_glob = "data/run_metrics/*.parquet"

    if not Path(db_path).exists():
        print(f"⚠️  {db_path} not found. Run src/research/data_utils/runlog_demo.py first.")
        return

    # 1. Top runs by Sharpe
    print("\n1️⃣  Top 5 runs by Sharpe ratio:")
    try:
        top = top_runs_by_sharpe(metrics_glob, top_n=5)
        for row in top:
            print(f"   {row}")
    except Exception as e:
        print(f"   Error: {e}")

    # 2. Custom query
    print("\n2️⃣  Custom query: count metrics by type")
    try:
        rows = query_parquet(
            metrics_glob,
            """
            SELECT metric, COUNT(*) as count
            FROM read_parquet(...)
            GROUP BY metric
            """,
        )
        for row in rows:
            print(f"   {row}")
    except Exception as e:
        print(f"   Error: {e}")

    # 3. Join runs + metrics
    print("\n3️⃣  Join runs table with metrics (if available):")
    try:
        con = build_con(runs_db=db_path, attach_sqlite=True)
        result = (
            con.execute(
                f"""
            SELECT 
                r.id,
                r.created_at,
                r.status,
                COUNT(m.run_id) as metric_count
            FROM runlog_db.runs r
            LEFT JOIN read_parquet('{metrics_glob}') m
                ON m.run_id = r.id
            GROUP BY r.id, r.created_at, r.status
            LIMIT 5
            """
            )
            .df()
            .to_dict("records")
        )
        con.close()
        for row in result:
            print(f"   {row}")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 80)
    print("✅ Demo complete")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    demo()
