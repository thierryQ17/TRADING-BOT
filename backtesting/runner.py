"""Run backtests in parallel across multiple strategies."""

import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd

from backtesting.engine import BacktestEngine
from backtesting.metrics import BacktestResult, print_report
from strategies.base_strategy import BaseStrategy

logger = logging.getLogger(__name__)


def _run_single(args: tuple) -> BacktestResult:
    """Worker function for parallel execution."""
    strategy, df_dict, kwargs = args
    df = pd.DataFrame(df_dict)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    engine = BacktestEngine(strategy, **kwargs)
    return engine.run(df)


def run_all(
    strategies: list[BaseStrategy],
    df: pd.DataFrame,
    parallel: bool = True,
    **engine_kwargs,
) -> list[BacktestResult]:
    """Backtest multiple strategies on the same data.

    Args:
        strategies: List of strategy instances
        df: OHLCV DataFrame
        parallel: Run in parallel processes
        **engine_kwargs: Passed to BacktestEngine (position_size, stop_loss_pct, etc.)
    """
    results = []
    df_dict = df.to_dict(orient="list")

    if parallel and len(strategies) > 1:
        tasks = [(s, df_dict, engine_kwargs) for s in strategies]
        with ProcessPoolExecutor(max_workers=len(strategies)) as pool:
            futures = {pool.submit(_run_single, t): t[0].name for t in tasks}
            for future in as_completed(futures):
                name = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info("Backtest complete: %s", name)
                except Exception:
                    logger.exception("Backtest failed: %s", name)
    else:
        for strategy in strategies:
            engine = BacktestEngine(strategy, **engine_kwargs)
            result = engine.run(df)
            results.append(result)
            logger.info("Backtest complete: %s", strategy.name)

    # Print all reports
    for r in sorted(results, key=lambda x: x.total_pnl, reverse=True):
        print_report(r)

    return results
