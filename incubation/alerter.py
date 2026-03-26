"""Telegram alert system for trade events."""

import logging
import os
import time
import threading
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# Cooldown defaults (seconds)
DEFAULT_TRADE_COOLDOWN = 900   # 15 min between trade alerts
DEFAULT_DAILY_COOLDOWN = 3600  # 1h between daily PnL alerts
DEFAULT_SYSTEM_COOLDOWN = 0    # no cooldown for system alerts


class Alerter:
    """Send Telegram alerts on trade events with anti-spam cooldown."""

    def __init__(
        self,
        bot_token: str = "",
        chat_id: str = "",
        enabled: bool = True,
        loss_threshold: float = 5.0,
        gain_threshold: float = 10.0,
        daily_loss_threshold: float = 20.0,
        daily_gain_threshold: float = 50.0,
    ):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = enabled and bool(self.bot_token) and bool(self.chat_id)

        # Thresholds (in $)
        self.loss_threshold = loss_threshold
        self.gain_threshold = gain_threshold
        self.daily_loss_threshold = daily_loss_threshold
        self.daily_gain_threshold = daily_gain_threshold

        # Anti-spam: last send time per alert type
        self._last_sent: dict[str, float] = {}
        self._lock = threading.Lock()

        if self.enabled:
            logger.info("Telegram alerts enabled (chat_id: %s)", self.chat_id)
        else:
            logger.info("Telegram alerts disabled (missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID)")

    def _can_send(self, alert_type: str, cooldown: int) -> bool:
        """Check cooldown for an alert type."""
        now = time.time()
        with self._lock:
            last = self._last_sent.get(alert_type, 0)
            if now - last < cooldown:
                return False
            self._last_sent[alert_type] = now
            return True

    def _send(self, message: str) -> bool:
        """Send a message via Telegram Bot API."""
        if not self.enabled:
            return False
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            resp = requests.post(url, json={
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML",
            }, timeout=10)
            if resp.ok:
                logger.info("Telegram alert sent")
                return True
            logger.warning("Telegram API error: %s", resp.text)
            return False
        except Exception as e:
            logger.error("Telegram send failed: %s", e)
            return False

    # --- Public API ---

    def check_trade(self, strategy: str, side: str, price: float, size: float, pnl: float) -> None:
        """Check if a trade triggers an alert."""
        if not self.enabled or pnl == 0:
            return

        if pnl < 0 and abs(pnl) >= self.loss_threshold:
            if self._can_send("trade_loss", DEFAULT_TRADE_COOLDOWN):
                self._send(
                    f"<b>PERTE</b> -{abs(pnl):.2f}$\n"
                    f"Strategie: {strategy}\n"
                    f"Action: {side} @ {price:.4f}\n"
                    f"Taille: {size:.2f}$"
                )

        elif pnl > 0 and pnl >= self.gain_threshold:
            if self._can_send("trade_gain", DEFAULT_TRADE_COOLDOWN):
                self._send(
                    f"<b>GAIN</b> +{pnl:.2f}$\n"
                    f"Strategie: {strategy}\n"
                    f"Action: {side} @ {price:.4f}\n"
                    f"Taille: {size:.2f}$"
                )

    def check_daily_pnl(self, daily_pnl: float) -> None:
        """Check if daily PnL triggers an alert."""
        if not self.enabled:
            return

        if daily_pnl <= -self.daily_loss_threshold:
            if self._can_send("daily_loss", DEFAULT_DAILY_COOLDOWN):
                self._send(
                    f"<b>ALERTE PERTE JOURNALIERE</b>\n"
                    f"PnL du jour: {daily_pnl:.2f}$\n"
                    f"Seuil: -{self.daily_loss_threshold:.0f}$"
                )

        elif daily_pnl >= self.daily_gain_threshold:
            if self._can_send("daily_gain", DEFAULT_DAILY_COOLDOWN):
                self._send(
                    f"<b>OBJECTIF JOURNALIER ATTEINT</b>\n"
                    f"PnL du jour: +{daily_pnl:.2f}$\n"
                    f"Seuil: +{self.daily_gain_threshold:.0f}$"
                )

    def notify_level_change(self, direction: str, old_size: float, new_size: float, reason: str) -> None:
        """Alert on scaler level up/down."""
        if not self.enabled:
            return
        if self._can_send("level_change", DEFAULT_SYSTEM_COOLDOWN):
            emoji = "LEVEL UP" if direction == "up" else "LEVEL DOWN"
            self._send(
                f"<b>{emoji}</b>\n"
                f"{old_size:.0f}$ -> {new_size:.0f}$\n"
                f"Raison: {reason}"
            )

    def notify_bot_error(self, bot_name: str, error: str) -> None:
        """Alert on bot fatal error."""
        if not self.enabled:
            return
        if self._can_send(f"error_{bot_name}", DEFAULT_SYSTEM_COOLDOWN):
            self._send(
                f"<b>ERREUR BOT</b>\n"
                f"Bot: {bot_name}\n"
                f"Erreur: {error}"
            )

    def notify_kill_all(self, bots: list[str]) -> None:
        """Alert when kill-all is triggered."""
        if not self.enabled:
            return
        if self._can_send("kill_all", DEFAULT_SYSTEM_COOLDOWN):
            self._send(
                f"<b>ARRET D'URGENCE</b>\n"
                f"Bots arretes: {', '.join(bots) if bots else 'aucun'}"
            )

    def send_test(self) -> bool:
        """Send a test message to verify configuration."""
        return self._send("Test alerte Polymarket RBI Bot — configuration OK")
