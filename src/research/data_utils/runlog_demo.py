"""Demo for the run logger; supports direct execution without -m."""

# Flexible imports so this works both as a module and a script.
try:  # When run via `python -m src.research.data_utils.runlog_demo`
    from .runlog import init_db, log_run, list_runs, write_metrics, update_run
except Exception:  # When run directly: `python src/research/data_utils/runlog_demo.py`
    try:
        from runlog import init_db, log_run, list_runs, write_metrics, update_run
    except Exception:
        import os
        import sys

        here = os.path.dirname(__file__)
        if here not in sys.path:
            sys.path.append(here)
        from runlog import init_db, log_run, list_runs, write_metrics, update_run

import time


def main():
    db_path = "data/runlog.sqlite"
    init_db(db_path)

    # Simulate metrics
    metrics = [
        {"metric": "sharpe", "value": 1.23},
        {"metric": "max_drawdown", "value": -0.07},
        {"metric": "trades", "value": 152},
    ]
    # Log metadata first to obtain run_id
    run_id = log_run(
        db_path=db_path,
        command="python your_script.py --symbol BTCUSDT --window 60",
        config={"symbol": "BTCUSDT", "window": 60},
        status="running",
        duration_ms=1234,
        result_path=None,
        tags=["backtest", "demo"],
        notes="First demo run",
    )

    metrics_path = write_metrics(metrics, "data/run_metrics/demo_run", run_id=run_id)

    # Update the run with final status and result path
    update_run(
        db_path=db_path,
        run_id=run_id,
        status="success",
        result_path=metrics_path,
        notes="Updated with metrics path",
    )

    print(f"Logged run_id={run_id} with metrics_path={metrics_path}")
    for row in list_runs(db_path, limit=5):
        print(row)


if __name__ == "__main__":
    main()
