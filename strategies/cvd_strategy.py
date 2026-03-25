"""Cumulative Volume Delta (CVD) divergence strategy.

Detects divergences between price direction and net buying/selling pressure.
When price drops but CVD rises -> hidden buying -> long.
When price rises but CVD drops -> hidden selling -> short.
"""

import pandas as pd
import numpy as np

from config import settings
from strategies.base_strategy import BaseStrategy, Signal, TradeSignal


class CVDStrategy(BaseStrategy):
    name = "cvd"

    def __init__(self, lookback: int = settings.CVD_LOOKBACK):
        self.lookback = lookback

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        # Approximate volume delta from candle shape:
        # delta = volume * (close - open) / (high - low)
        # Positive delta = more buying, negative = more selling
        spread = df["high"] - df["low"]
        spread = spread.replace(0, float("nan"))
        df["volume_delta"] = df["volume"] * (df["close"] - df["open"]) / spread
        df["volume_delta"] = df["volume_delta"].fillna(0)

        # Cumulative Volume Delta
        df["cvd"] = df["volume_delta"].cumsum()

        # Rolling slope (trend direction) over lookback window
        df["price_slope"] = df["close"].rolling(self.lookback).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == self.lookback else 0,
            raw=False,
        )
        df["cvd_slope"] = df["cvd"].rolling(self.lookback).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] if len(x) == self.lookback else 0,
            raw=False,
        )

        return df

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if len(df) < self.lookback + 1:
            return TradeSignal(Signal.HOLD, df["close"].iloc[-1], 0.0, "not enough data")

        curr = df.iloc[-1]
        price = curr["close"]
        price_slope = curr["price_slope"]
        cvd_slope = curr["cvd_slope"]

        if pd.isna(price_slope) or pd.isna(cvd_slope):
            return TradeSignal(Signal.HOLD, price, 0.0, "indicators not ready")

        # Bullish divergence: price falling but CVD rising -> hidden buying
        if price_slope < 0 and cvd_slope > 0:
            confidence = min(abs(cvd_slope) / (abs(price_slope) + 1e-9), 1.0)
            return TradeSignal(
                Signal.BUY, price, confidence,
                f"Bullish CVD divergence (price↓ cvd↑)"
            )

        # Bearish divergence: price rising but CVD falling -> hidden selling
        if price_slope > 0 and cvd_slope < 0:
            confidence = min(abs(cvd_slope) / (abs(price_slope) + 1e-9), 1.0)
            return TradeSignal(
                Signal.SELL, price, confidence,
                f"Bearish CVD divergence (price↑ cvd↓)"
            )

        return TradeSignal(Signal.HOLD, price, 0.0, "no divergence detected")
