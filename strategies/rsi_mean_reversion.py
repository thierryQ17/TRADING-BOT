"""RSI Mean Reversion + VWAP strategy — counter-trend.

Waits for extreme RSI readings (oversold/overbought) and bets
on a reversion to the mean (VWAP acts as the fair-value anchor).
"""

import pandas as pd
import ta

from config import settings
from strategies.base_strategy import BaseStrategy, Signal, TradeSignal


class RSIMeanReversionStrategy(BaseStrategy):
    name = "rsi_mean_reversion"

    def __init__(
        self,
        rsi_period: int = settings.RSI_PERIOD,
        oversold: int = settings.RSI_OVERSOLD,
        overbought: int = settings.RSI_OVERBOUGHT,
    ):
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought

    def compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df["rsi"] = ta.momentum.RSIIndicator(close=df["close"], window=self.rsi_period).rsi()

        # VWAP — cumulative (price * volume) / cumulative volume
        cum_vol = df["volume"].cumsum()
        cum_pv = (df["close"] * df["volume"]).cumsum()
        df["vwap"] = cum_pv / cum_vol.replace(0, float("nan"))

        return df

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if len(df) < self.rsi_period + 1:
            return TradeSignal(Signal.HOLD, df["close"].iloc[-1], 0.0, "not enough data")

        curr = df.iloc[-1]
        price = curr["close"]
        rsi = curr["rsi"]
        vwap = curr["vwap"]

        if pd.isna(rsi) or pd.isna(vwap):
            return TradeSignal(Signal.HOLD, price, 0.0, "indicators not ready")

        # Oversold + price below VWAP -> long (expect bounce)
        if rsi < self.oversold and price < vwap:
            confidence = (self.oversold - rsi) / self.oversold
            return TradeSignal(Signal.BUY, price, confidence, f"RSI oversold ({rsi:.1f}), price < VWAP")

        # Overbought + price above VWAP -> short / exit (expect pullback)
        if rsi > self.overbought and price > vwap:
            confidence = (rsi - self.overbought) / (100 - self.overbought)
            return TradeSignal(Signal.SELL, price, confidence, f"RSI overbought ({rsi:.1f}), price > VWAP")

        # Exit long when price reaches VWAP
        if rsi > 50 and price >= vwap:
            return TradeSignal(Signal.SELL, price, 0.3, "RSI normalized, price at VWAP — exit")

        return TradeSignal(Signal.HOLD, price, 0.0, f"RSI={rsi:.1f}, waiting")
