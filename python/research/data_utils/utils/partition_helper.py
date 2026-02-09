"""
Helper for creating Hive-style partitioned parquet structure.
Makes data queryable by many tools and prepares for potential Iceberg migration.
"""

import polars as pl
from pathlib import Path
from typing import Optional


def write_partitioned_parquet(
    df: pl.DataFrame,
    base_dir: Path,
    partition_cols: list[str],
    filename_pattern: Optional[str] = None,
):
    """
    Write DataFrame to Hive-style partitioned parquet structure.

    Example:
        base_dir/
            symbol=BTCUSDT/
                year=2024/
                    month=07/
                        data_part_0.parquet

    Args:
        df: DataFrame to write
        base_dir: Root directory for partitioned data
        partition_cols: Columns to partition by (e.g., ['symbol', 'year', 'month'])
        filename_pattern: Optional pattern for data files (default: data.parquet)
    """
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    # Use Polars built-in partitioned write
    df.write_parquet(base_dir, use_pyarrow=True, partition_by=partition_cols, compression="zstd")
    print(f"✅ Wrote partitioned parquet to {base_dir}")


def read_partitioned_parquet(base_dir: Path, filters: Optional[dict] = None) -> pl.DataFrame:
    """
    Read from Hive-style partitioned parquet structure with optional filters.

    Args:
        base_dir: Root directory with partitioned data
        filters: Dict of partition filters (e.g., {'symbol': 'BTCUSDT', 'year': 2024})

    Returns:
        Polars DataFrame
    """
    base_dir = Path(base_dir)

    if filters:
        # Build path pattern based on filters
        # e.g., symbol=BTCUSDT/year=2024/**/*.parquet
        path_parts = [base_dir]
        for col, val in filters.items():
            path_parts.append(f"{col}={val}")
        path_pattern = str(Path(*path_parts) / "**" / "*.parquet")
    else:
        path_pattern = str(base_dir / "**" / "*.parquet")

    return pl.read_parquet(path_pattern)


def add_partition_columns(df: pl.DataFrame) -> pl.DataFrame:
    """
    Add year/month partition columns from open_time.

    Args:
        df: DataFrame with 'open_time' column

    Returns:
        DataFrame with added 'year' and 'month' columns
    """
    return df.with_columns(
        [pl.col("open_time").dt.year().alias("year"), pl.col("open_time").dt.month().alias("month")]
    )


# Example usage:
if __name__ == "__main__":
    # Example: Convert existing flat parquet to partitioned structure

    # Read existing data
    df = pl.read_parquet("data/klines/BTCUSDT.pq")

    # Add partition columns
    df = df.with_columns(
        [
            pl.lit("BTCUSDT").alias("symbol"),  # Add if not present
            pl.col("open_time").dt.year().alias("year"),
            pl.col("open_time").dt.month().alias("month"),
        ]
    )

    # Write partitioned
    write_partitioned_parquet(
        df, base_dir=Path("data/klines_partitioned"), partition_cols=["symbol", "year", "month"]
    )

    # Read with filters (only loads needed partitions!)
    filtered_df = read_partitioned_parquet(
        base_dir=Path("data/klines_partitioned"), filters={"symbol": "BTCUSDT", "year": 2024}
    )

    print(f"Filtered data shape: {filtered_df.shape}")
