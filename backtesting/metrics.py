"""Backtest performance metrics."""

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    strategy: str
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_pnl: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    avg_trade_pnl: float
    trades: pd.DataFrame


def compute_metrics(trades: pd.DataFrame, strategy_name: str) -> BacktestResult:
    """Compute performance metrics from a DataFrame of trades.

    Expected columns: entry_price, exit_price, side, size, pnl
    """
    if trades.empty:
        return BacktestResult(
            strategy=strategy_name, total_trades=0, wins=0, losses=0,
            win_rate=0, total_pnl=0, profit_factor=0, max_drawdown=0,
            sharpe_ratio=0, avg_trade_pnl=0, trades=trades,
        )

    total = len(trades)
    wins = len(trades[trades["pnl"] > 0])
    losses = len(trades[trades["pnl"] <= 0])
    win_rate = wins / total if total > 0 else 0

    total_pnl = trades["pnl"].sum()
    avg_pnl = trades["pnl"].mean()

    gross_profit = trades[trades["pnl"] > 0]["pnl"].sum()
    gross_loss = abs(trades[trades["pnl"] <= 0]["pnl"].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

    # Max drawdown from cumulative PnL
    cum_pnl = trades["pnl"].cumsum()
    running_max = cum_pnl.cummax()
    drawdown = running_max - cum_pnl
    max_drawdown = drawdown.max() if len(drawdown) > 0 else 0

    # Sharpe ratio (annualized assuming ~252 trading days)
    if trades["pnl"].std() > 0:
        sharpe = (trades["pnl"].mean() / trades["pnl"].std()) * np.sqrt(252)
    else:
        sharpe = 0.0

    return BacktestResult(
        strategy=strategy_name,
        total_trades=total,
        wins=wins,
        losses=losses,
        win_rate=win_rate,
        total_pnl=total_pnl,
        profit_factor=profit_factor,
        max_drawdown=max_drawdown,
        sharpe_ratio=sharpe,
        avg_trade_pnl=avg_pnl,
        trades=trades,
    )


def print_report(result: BacktestResult) -> None:
    """Pretty-print backtest results."""
    print(f"\n{'='*50}")
    print(f"  Strategy: {result.strategy}")
    print(f"{'='*50}")
    print(f"  Total trades:   {result.total_trades}")
    print(f"  Wins / Losses:  {result.wins} / {result.losses}")
    print(f"  Win rate:       {result.win_rate:.1%}")
    print(f"  Total PnL:      ${result.total_pnl:.2f}")
    print(f"  Avg trade PnL:  ${result.avg_trade_pnl:.2f}")
    print(f"  Profit factor:  {result.profit_factor:.2f}")
    print(f"  Max drawdown:   ${result.max_drawdown:.2f}")
    print(f"  Sharpe ratio:   {result.sharpe_ratio:.2f}")
    print(f"{'='*50}\n")
