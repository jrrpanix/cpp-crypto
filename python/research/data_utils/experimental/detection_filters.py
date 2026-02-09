"""
Detection variants to distinguish smooth multi-day moves from single-bar spikes.
Provides multiple boolean pass flags to compare in backtests.
"""

from __future__ import annotations

import polars as pl


def apply_detection_filters(
    df: pl.DataFrame,
    *,
    window: int = 5,
    target: float = 0.05,  # e.g., 5% over window
    mid_offset: int = 3,  # mid-window checkpoint offset (days)
    mid_threshold: float = 0.02,  # e.g., 2% by mid_offset
    max_single: float = 0.03,  # cap any 1-day move to avoid single-bar spikes
    up_days_required: int = 3,  # min positive days inside window
    max_std: float = 0.02,  # max std of daily returns to consider it smooth
) -> pl.DataFrame:
    """
    Adds detection boolean columns:
      - spread_pass: requires total move and mid-window move
      - cap_pass: total move and max 1-day move below cap
      - updays_pass: total move and min count of up days
      - smooth_pass: avg daily >= target/window and std <= max_std
      - hybrid_pass: combines spread + cap + updays + smooth
    """
    if window < 2:
        raise ValueError("window must be >= 2")
    if mid_offset <= 0 or mid_offset >= window:
        raise ValueError("mid_offset must be in (0, window)")

    # Daily returns and cumulative moves
    ret1 = pl.col("close").pct_change().alias("ret1")
    ret_window = (pl.col("close") / pl.col("close").shift(window) - 1).alias("ret_window")
    ret_mid = (pl.col("close") / pl.col("close").shift(mid_offset) - 1).alias("ret_mid")

    # Rolling stats over the window
    roll_max_day = pl.col("ret1").rolling_max(window_size=window).alias("max_day_ret")
    roll_up_days = (
        (pl.col("ret1") > 0).cast(pl.Int8).rolling_sum(window_size=window).alias("up_days")
    )
    roll_mean = pl.col("ret1").rolling_mean(window_size=window).alias("mean_ret")
    roll_std = pl.col("ret1").rolling_std(window_size=window, ddof=0).alias("std_ret")

    df2 = df.with_columns(
        [ret1, ret_window, ret_mid, roll_max_day, roll_up_days, roll_mean, roll_std]
    )

    spread_pass = ((pl.col("ret_window") >= target) & (pl.col("ret_mid") >= mid_threshold)).alias(
        "spread_pass"
    )

    cap_pass = ((pl.col("ret_window") >= target) & (pl.col("max_day_ret") <= max_single)).alias(
        "cap_pass"
    )

    updays_pass = (
        (pl.col("ret_window") >= target) & (pl.col("up_days") >= up_days_required)
    ).alias("updays_pass")

    smooth_pass = ((pl.col("mean_ret") >= target / window) & (pl.col("std_ret") <= max_std)).alias(
        "smooth_pass"
    )

    hybrid_pass = (
        pl.col("spread_pass") & pl.col("cap_pass") & pl.col("updays_pass") & pl.col("smooth_pass")
    ).alias("hybrid_pass")

    return df2.with_columns([spread_pass, cap_pass, updays_pass, smooth_pass]).with_columns(
        [hybrid_pass]
    )


__all__ = ["apply_detection_filters"]
