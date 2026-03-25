"""Abstract base class for all trading strategies."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import pandas as pd


class Signal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TradeSignal:
    signal: Signal
    price: float
    confidence: float  # 0.0 - 1.0
    reason: str


class BaseStrategy(ABC):
    """All strategies must implement this interface."""

    name: str = "base"

    @abstractmethod
    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add strategy-specific indicator columns to the DataFrame."""
        ...

    @abstractmethod
    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        """Analyze the latest data and return a trade signal.

        The DataFrame should already have indicators computed.
        Returns a TradeSignal with BUY, SELL, or HOLD.
        """
        ...

    def backtest_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate signals for every row (used by the backtest engine).

        Returns the DataFrame with an added 'signal' column.
        """
        df = self.compute_indicators(df.copy())
        signals = []
        for i in range(len(df)):
            chunk = df.iloc[: i + 1]
            if len(chunk) < 2:
                signals.append(Signal.HOLD.value)
                continue
            sig = self.generate_signal(chunk)
            signals.append(sig.signal.value)
        df["signal"] = signals
        return df
