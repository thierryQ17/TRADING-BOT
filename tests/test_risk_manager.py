"""Unit tests for the risk manager."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

from bot.risk_manager import RiskManager


class TestRiskManager:
    def test_allows_normal_trade(self):
        rm = RiskManager(max_position_size=10, max_daily_loss=50, max_open_positions=3)
        allowed, reason = rm.can_trade(5.0)
        assert allowed is True
        assert reason == "ok"

    def test_blocks_oversized_trade(self):
        rm = RiskManager(max_position_size=10)
        allowed, reason = rm.can_trade(15.0)
        assert allowed is False
        assert "exceeds" in reason

    def test_blocks_at_max_positions(self):
        rm = RiskManager(max_open_positions=2)
        rm.on_trade_opened()
        rm.on_trade_opened()
        allowed, reason = rm.can_trade(1.0)
        assert allowed is False
        assert "Max open positions" in reason

    def test_blocks_after_daily_loss_limit(self):
        rm = RiskManager(max_daily_loss=10)
        rm.on_trade_opened()
        rm.on_trade_closed(-10.0)
        allowed, reason = rm.can_trade(1.0)
        assert allowed is False
        assert "Daily loss" in reason

    def test_tracks_positions_correctly(self):
        rm = RiskManager()
        rm.on_trade_opened()
        rm.on_trade_opened()
        assert rm.open_positions == 2
        rm.on_trade_closed(5.0)
        assert rm.open_positions == 1
        assert rm.daily_pnl == 5.0

    def test_stop_loss_price(self):
        rm = RiskManager(stop_loss_pct=0.05)
        assert rm.get_stop_loss_price(100, "BUY") == pytest.approx(95.0)
        assert rm.get_stop_loss_price(100, "SELL") == pytest.approx(105.0)
