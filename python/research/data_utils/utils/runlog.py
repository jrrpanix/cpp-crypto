import os
import sqlite3
import uuid
import json
import time
import datetime as dt
import subprocess
from typing import Any, Dict, Iterable, List, Optional

# --- SQLite-backed run logger ---
# Single-file DB with a simple "runs" table for metadata.
# Designed for local usage with lightweight setup.

DEFAULT_DB_PATH = os.path.join("data", "runlog.sqlite")


def _connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    conn = _connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                command TEXT,
                config_path TEXT,
                config_json TEXT,
                git_commit TEXT,
                status TEXT,
                duration_ms INTEGER,
                result_path TEXT,
                tags TEXT,
                notes TEXT
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def _git_commit_short() -> Optional[str]:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
        )
        return out.decode().strip()
    except Exception:
        return None


def log_run(
    db_path: str = DEFAULT_DB_PATH,
    *,
    run_id: Optional[str] = None,
    command: Optional[str] = None,
    config_path: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    status: str = "success",
    duration_ms: Optional[int] = None,
    result_path: Optional[str] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> str:
    """
    Insert a single run record. If duration_ms is None, measures duration of this call only.
    Returns the generated run id.
    """
    run_id = run_id or str(uuid.uuid4())
    t0 = time.perf_counter()

    config_json = json.dumps(config, ensure_ascii=False) if config is not None else None
    tags_csv = ",".join(tags) if tags else None
    created_at = dt.datetime.utcnow().isoformat(timespec="seconds")
    git_commit = _git_commit_short()

    conn = _connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO runs (
                id, created_at, command, config_path, config_json,
                git_commit, status, duration_ms, result_path, tags, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                created_at,
                command,
                config_path,
                config_json,
                git_commit,
                status,
                duration_ms,
                result_path,
                tags_csv,
                notes,
            ),
        )
        if duration_ms is None:
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            conn.execute("UPDATE runs SET duration_ms = ? WHERE id = ?", (elapsed_ms, run_id))
        conn.commit()
    finally:
        conn.close()

    return run_id


def list_runs(db_path: str = DEFAULT_DB_PATH, limit: int = 50) -> List[Dict[str, Any]]:
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "SELECT * FROM runs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def update_run(
    db_path: str = DEFAULT_DB_PATH,
    *,
    run_id: str,
    status: Optional[str] = None,
    duration_ms: Optional[int] = None,
    result_path: Optional[str] = None,
    tags: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> None:
    """Update selected fields of an existing run (id must already exist)."""
    fields = []
    params = []
    if status is not None:
        fields.append("status = ?")
        params.append(status)
    if duration_ms is not None:
        fields.append("duration_ms = ?")
        params.append(duration_ms)
    if result_path is not None:
        fields.append("result_path = ?")
        params.append(result_path)
    if tags is not None:
        fields.append("tags = ?")
        params.append(",".join(tags))
    if notes is not None:
        fields.append("notes = ?")
        params.append(notes)

    if not fields:
        return

    params.append(run_id)

    conn = _connect(db_path)
    try:
        conn.execute(f"UPDATE runs SET {', '.join(fields)} WHERE id = ?", params)
        conn.commit()
    finally:
        conn.close()


# --- Optional: write metrics to Parquet (fallback to JSON Lines) ---


def write_metrics(
    records: Iterable[Dict[str, Any]],
    output_path: str,
    run_id: Optional[str] = None,
) -> str:
    """
    Write metric records to Parquet if pyarrow is available, else write JSON Lines.
    Returns the actual path written.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Add run_id column if provided
    recs = list(records)
    if run_id is not None:
        recs = [dict(r, run_id=run_id) for r in recs]

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq

        table = pa.Table.from_pylist(recs)
        # Ensure .parquet extension
        if not output_path.endswith(".parquet"):
            output_path = output_path + ".parquet"
        pq.write_table(table, output_path)
        return output_path
    except Exception:
        # Fallback to JSON Lines
        if not output_path.endswith(".jsonl"):
            output_path = output_path + ".jsonl"
        with open(output_path, "w", encoding="utf-8") as f:
            for rec in recs:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return output_path
