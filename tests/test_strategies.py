"""Unit tests for trading strategies."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
import pytest

from strategies.macd_strategy import MACDStrategy
from strategies.rsi_mean_reversion import RSIMeanReversionStrategy
from strategies.cvd_strategy import CVDStrategy
from strategies.base_strategy import Signal


def make_candles(n: int = 100, trend: str = "up") -> pd.DataFrame:
    """Generate synthetic OHLCV data."""
    np.random.seed(42)
    timestamps = pd.date_range("2024-01-01", periods=n, freq="5min")

    if trend == "up":
        close = 100 + np.cumsum(np.random.randn(n) * 0.5 + 0.1)
    elif trend == "down":
        close = 100 + np.cumsum(np.random.randn(n) * 0.5 - 0.1)
    else:
        close = 100 + np.cumsum(np.random.randn(n) * 0.5)

    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    open_ = close + np.random.randn(n) * 0.2
    volume = np.random.randint(100, 10000, n).astype(float)

    return pd.DataFrame({
        "timestamp": timestamps,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


class TestMACDStrategy:
    def test_compute_indicators(self):
        df = make_candles(50)
        strategy = MACDStrategy()
        result = strategy.compute_indicators(df)
        assert "macd_line" in result.columns
        assert "macd_signal" in result.columns
        assert "macd_hist" in result.columns

    def test_generate_signal_returns_valid(self):
        df = make_candles(50)
        strategy = MACDStrategy()
        df = strategy.compute_indicators(df)
        signal = strategy.generate_signal(df)
        assert signal.signal in (Signal.BUY, Signal.SELL, Signal.HOLD)
        assert 0 <= signal.confidence <= 1.0

    def test_not_enough_data(self):
        df = make_candles(1)
        strategy = MACDStrategy()
        df = strategy.compute_indicators(df)
        signal = strategy.generate_signal(df)
        assert signal.signal == Signal.HOLD


class TestRSIStrategy:
    def test_compute_indicators(self):
        df = make_candles(50)
        strategy = RSIMeanReversionStrategy()
        result = strategy.compute_indicators(df)
        assert "rsi" in result.columns
        assert "vwap" in result.columns

    def test_generate_signal_returns_valid(self):
        df = make_candles(50)
        strategy = RSIMeanReversionStrategy()
        df = strategy.compute_indicators(df)
        signal = strategy.generate_signal(df)
        assert signal.signal in (Signal.BUY, Signal.SELL, Signal.HOLD)


class TestCVDStrategy:
    def test_compute_indicators(self):
        df = make_candles(50)
        strategy = CVDStrategy()
        result = strategy.compute_indicators(df)
        assert "cvd" in result.columns
        assert "volume_delta" in result.columns
        assert "price_slope" in result.columns
        assert "cvd_slope" in result.columns

    def test_generate_signal_returns_valid(self):
        df = make_candles(50)
        strategy = CVDStrategy()
        df = strategy.compute_indicators(df)
        signal = strategy.generate_signal(df)
        assert signal.signal in (Signal.BUY, Signal.SELL, Signal.HOLD)
