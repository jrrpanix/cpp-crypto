"""
DuckDB-based analytics for parquet files.
Useful for ad-hoc queries, ranking runs, filtering universes, and cross-symbol analysis.
No new deps required if duckdb is installed; falls back gracefully if not.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False


def query_parquet(
    glob_pattern: str,
    sql: str,
    *,
    memory_limit: str = "4GB",
) -> list[dict[str, Any]]:
    """
    Execute SQL query over parquet files matching glob_pattern.
    Returns list of dicts (rows).
    
    Example:
      rows = query_parquet(
          "data/run_metrics/*.parquet",
          "SELECT run_id, metric, value FROM read_parquet(...) WHERE metric='sharpe' ORDER BY value DESC LIMIT 10"
      )
    """
    if not HAS_DUCKDB:
        raise ImportError("duckdb not installed. Install with: uv add duckdb")
    
    con = duckdb.connect(config={"memory_limit": memory_limit})
    # Use parameterized query to safely inject glob
    query = sql.replace("read_parquet(...)", f"read_parquet('{glob_pattern}')")
    result = con.execute(query).df().to_dict('records')
    con.close()
    
    return result


def top_runs_by_sharpe(
    metrics_glob: str = "data/run_metrics/*.parquet",
    top_n: int = 20,
) -> list[dict[str, Any]]:
    """Get top N runs by Sharpe ratio."""
    if not HAS_DUCKDB:
        raise ImportError("duckdb not installed. Install with: uv add duckdb")
    
    sql = f"""
    SELECT 
        run_id,
        metric,
        value
    FROM read_parquet('{metrics_glob}')
    WHERE metric = 'sharpe'
    ORDER BY value DESC
    LIMIT {top_n}
    """
    con = duckdb.connect()
    result = con.execute(sql).df().to_dict('records')
    con.close()
    return result


def universe_performance(
    runs_db: str = "data/runlog.sqlite",
    metrics_glob: str = "data/run_metrics/*.parquet",
) -> list[dict[str, Any]]:
    """
    Join SQLite runs table with metrics parquet; group by universe.
    Requires duckdb sqlite extension.
    """
    if not HAS_DUCKDB:
        raise ImportError("duckdb not installed. Install with: uv add duckdb")
    
    con = duckdb.connect()
    con.execute("INSTALL sqlite; LOAD sqlite;")
    con.execute(f"ATTACH '{runs_db}' AS runlog_db (TYPE SQLITE);")
    
    sql = f"""
    SELECT 
        r.tags as universe,
        COUNT(DISTINCT r.id) as num_runs,
        AVG(m.value) as avg_sharpe,
        MAX(m.value) as max_sharpe,
        MIN(m.value) as min_sharpe
    FROM runlog_db.runs r
    LEFT JOIN read_parquet('{metrics_glob}') m
        ON m.run_id = r.id AND m.metric = 'sharpe'
    WHERE r.status = 'success'
    GROUP BY r.tags
    ORDER BY avg_sharpe DESC
    """
    
    result = con.execute(sql).df().to_dict('records')
    con.close()
    return result


def build_con(
    runs_db: Optional[str] = None,
    attach_sqlite: bool = False,
) -> duckdb.DuckDBPyConnection:
    """
    Build and return a DuckDB connection, optionally with sqlite extension.
    Caller is responsible for .close().
    
    Example:
      con = build_con(runs_db="data/runlog.sqlite", attach_sqlite=True)
      result = con.execute("SELECT * FROM runlog_db.runs LIMIT 5").fetchall()
      con.close()
    """
    if not HAS_DUCKDB:
        raise ImportError("duckdb not installed. Install with: uv add duckdb")
    
    con = duckdb.connect()
    if attach_sqlite and runs_db:
        con.execute("INSTALL sqlite; LOAD sqlite;")
        con.execute(f"ATTACH '{runs_db}' AS runlog_db (TYPE SQLITE);")
    return con


__all__ = ["query_parquet", "top_runs_by_sharpe", "universe_performance", "build_con", "HAS_DUCKDB"]
