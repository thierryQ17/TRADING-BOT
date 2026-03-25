"""Risk management — the last line of defense before any trade."""

import logging
from datetime import datetime, timezone

from config import settings

logger = logging.getLogger(__name__)


class RiskManager:
    """Enforces position limits, daily loss limits, and size caps."""

    def __init__(
        self,
        max_position_size: float = settings.MAX_POSITION_SIZE,
        max_daily_loss: float = settings.MAX_DAILY_LOSS,
        max_open_positions: int = settings.MAX_OPEN_POSITIONS,
        stop_loss_pct: float = settings.STOP_LOSS_PCT,
    ):
        self.max_position_size = max_position_size
        self.max_daily_loss = max_daily_loss
        self.max_open_positions = max_open_positions
        self.stop_loss_pct = stop_loss_pct

        self._daily_pnl = 0.0
        self._daily_reset_date = datetime.now(timezone.utc).date()
        self._open_positions = 0

    def _maybe_reset_daily(self) -> None:
        """Reset daily PnL counter at midnight UTC."""
        today = datetime.now(timezone.utc).date()
        if today != self._daily_reset_date:
            logger.info("New day — resetting daily PnL (was $%.2f)", self._daily_pnl)
            self._daily_pnl = 0.0
            self._daily_reset_date = today

    def can_trade(self, size: float) -> tuple[bool, str]:
        """Check if a new trade is allowed.

        Returns (allowed, reason).
        """
        self._maybe_reset_daily()

        if size > self.max_position_size:
            return False, f"Size ${size:.2f} exceeds max ${self.max_position_size:.2f}"

        if self._open_positions >= self.max_open_positions:
            return False, f"Max open positions reached ({self.max_open_positions})"

        if self._daily_pnl <= -self.max_daily_loss:
            return False, f"Daily loss limit hit (${self._daily_pnl:.2f})"

        return True, "ok"

    def on_trade_opened(self) -> None:
        """Track a newly opened position."""
        self._open_positions += 1
        logger.info("Position opened — %d open", self._open_positions)

    def on_trade_closed(self, pnl: float) -> None:
        """Track a closed position and update daily PnL."""
        self._maybe_reset_daily()
        self._open_positions = max(0, self._open_positions - 1)
        self._daily_pnl += pnl
        logger.info(
            "Position closed — PnL: $%.2f | Daily: $%.2f | Open: %d",
            pnl, self._daily_pnl, self._open_positions,
        )

    def get_stop_loss_price(self, entry_price: float, side: str) -> float:
        """Calculate stop-loss price for a given entry."""
        if side.upper() == "BUY":
            return entry_price * (1 - self.stop_loss_pct)
        return entry_price * (1 + self.stop_loss_pct)

    @property
    def daily_pnl(self) -> float:
        self._maybe_reset_daily()
        return self._daily_pnl

    @property
    def open_positions(self) -> int:
        return self._open_positions
