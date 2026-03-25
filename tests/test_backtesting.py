"""Unit tests for the backtest engine."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from strategies.macd_strategy import MACDStrategy
from backtesting.engine import BacktestEngine
from backtesting.metrics import compute_metrics


def make_candles(n: int = 200) -> pd.DataFrame:
    np.random.seed(42)
    timestamps = pd.date_range("2024-01-01", periods=n, freq="5min")
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    open_ = close + np.random.randn(n) * 0.2
    volume = np.random.randint(100, 10000, n).astype(float)
    return pd.DataFrame({
        "timestamp": timestamps, "open": open_, "high": high,
        "low": low, "close": close, "volume": volume,
    })


class TestBacktestEngine:
    def test_run_produces_result(self):
        df = make_candles(200)
        engine = BacktestEngine(MACDStrategy(), position_size=1.0)
        result = engine.run(df)
        assert result.strategy == "macd"
        assert result.total_trades >= 0

    def test_result_has_valid_metrics(self):
        df = make_candles(200)
        engine = BacktestEngine(MACDStrategy(), position_size=1.0)
        result = engine.run(df)
        assert 0 <= result.win_rate <= 1
        assert result.max_drawdown >= 0

    def test_empty_data(self):
        df = pd.DataFrame(columns=["timestamp", "open", "high", "low", "close", "volume"])
        engine = BacktestEngine(MACDStrategy())
        result = engine.run(df)
        assert result.total_trades == 0


class TestMetrics:
    def test_compute_from_trades(self):
        trades = pd.DataFrame({
            "entry_price": [100, 105, 98],
            "exit_price": [105, 103, 102],
            "side": ["BUY", "BUY", "BUY"],
            "size": [1, 1, 1],
            "pnl": [0.05, -0.02, 0.04],
        })
        result = compute_metrics(trades, "test")
        assert result.total_trades == 3
        assert result.wins == 2
        assert result.losses == 1
        assert result.win_rate == pytest.approx(2 / 3)

    def test_empty_trades(self):
        trades = pd.DataFrame(columns=["entry_price", "exit_price", "side", "size", "pnl"])
        result = compute_metrics(trades, "test")
        assert result.total_trades == 0
        assert result.win_rate == 0
