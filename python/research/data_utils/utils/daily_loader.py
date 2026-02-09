"""Utility helpers to load daily parquet bars by directory/glob without brittle filenames.

Key points:
- Point at a directory; we build a glob (default: "*_daily_*.parquet") so new monthly files auto-join.
- Picks latest file per symbol if multiple match, or loads all if you want a concat.
- Uses Polars scan_parquet for speed; optional DuckDB path is noted but not required.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

import polars as pl

DEFAULT_GLOB = "*_daily_*.parquet"


def _list_files(directory: Path, glob: str = DEFAULT_GLOB) -> List[Path]:
    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    return sorted(directory.glob(glob))


def _symbol_from_name(path: Path) -> Optional[str]:
    # Example accepted: BTCUSDT_daily_2024-01.parquet
    m = re.match(r"([A-Za-z0-9]+)_daily_", path.name)
    return m.group(1) if m else None


def latest_per_symbol(files: Iterable[Path]) -> List[Path]:
    latest = {}
    for f in files:
        sym = _symbol_from_name(f)
        if not sym:
            continue
        # Later names (lexicographic) assumed newer; adjust if needed
        if sym not in latest or f.name > latest[sym].name:
            latest[sym] = f
    return sorted(latest.values())


def load_daily_concat(
    directory: str | Path,
    *,
    symbol: Optional[str] = None,
    use_latest: bool = True,
    glob: str = DEFAULT_GLOB,
) -> pl.DataFrame:
    """
    Load daily bars from a directory of parquet files.
    - If symbol is provided, filters to files matching that symbol.
    - If use_latest is True, picks the latest file per symbol (by filename order).
    - Otherwise concatenates all matching files.
    """
    directory = Path(directory)
    files = _list_files(directory, glob)
    if symbol:
        files = [f for f in files if _symbol_from_name(f) == symbol]
    if use_latest:
        files = latest_per_symbol(files)
    if not files:
        raise FileNotFoundError(
            f"No parquet files found in {directory} matching glob {glob} (symbol={symbol})"
        )

    lf = pl.scan_parquet(files)
    return lf.collect()


def load_daily_lazy(
    directory: str | Path,
    *,
    symbol: Optional[str] = None,
    use_latest: bool = True,
    glob: str = DEFAULT_GLOB,
) -> pl.LazyFrame:
    directory = Path(directory)
    files = _list_files(directory, glob)
    if symbol:
        files = [f for f in files if _symbol_from_name(f) == symbol]
    if use_latest:
        files = latest_per_symbol(files)
    if not files:
        raise FileNotFoundError(
            f"No parquet files found in {directory} matching glob {glob} (symbol={symbol})"
        )
    return pl.scan_parquet(files)


__all__ = ["load_daily_concat", "load_daily_lazy", "latest_per_symbol"]
