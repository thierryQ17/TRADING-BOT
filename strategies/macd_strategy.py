"""MACD Histogram strategy — momentum / trend following.

Uses fast parameters (3/15/3) tuned for short-timeframe moves.
Entry: MACD line crosses above signal line (bullish) or below (bearish).
Exit: reverse crossover or stop-loss/take-profit.
"""

import pandas as pd
import ta

from config import settings
from strategies.base_strategy import BaseStrategy, Signal, TradeSignal


class MACDStrategy(BaseStrategy):
    name = "macd"

    def __init__(
        self,
        fast: int = settings.MACD_FAST,
        slow: int = settings.MACD_SLOW,
        signal: int = settings.MACD_SIGNAL,
    ):
        self.fast = fast
        self.slow = slow
        self.signal_period = signal

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        macd = ta.trend.MACD(
            close=df["close"],
            window_fast=self.fast,
            window_slow=self.slow,
            window_sign=self.signal_period,
        )
        df["macd_line"] = macd.macd()
        df["macd_signal"] = macd.macd_signal()
        df["macd_hist"] = macd.macd_diff()
        return df

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if len(df) < 2:
            return TradeSignal(Signal.HOLD, df["close"].iloc[-1], 0.0, "not enough data")

        curr = df.iloc[-1]
        prev = df.iloc[-2]
        price = curr["close"]

        # Bullish crossover: MACD crosses above signal
        if prev["macd_line"] <= prev["macd_signal"] and curr["macd_line"] > curr["macd_signal"]:
            confidence = min(abs(curr["macd_hist"]) / price * 100, 1.0)
            return TradeSignal(Signal.BUY, price, confidence, "MACD bullish crossover")

        # Bearish crossover: MACD crosses below signal
        if prev["macd_line"] >= prev["macd_signal"] and curr["macd_line"] < curr["macd_signal"]:
            confidence = min(abs(curr["macd_hist"]) / price * 100, 1.0)
            return TradeSignal(Signal.SELL, price, confidence, "MACD bearish crossover")

        return TradeSignal(Signal.HOLD, price, 0.0, "no crossover")
