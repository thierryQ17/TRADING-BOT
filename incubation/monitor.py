"""Live monitoring dashboard for running bots."""

import logging
from datetime import datetime, timezone

from data.storage import get_trades

logger = logging.getLogger(__name__)


class Monitor:
    """Query trade database and print live performance stats."""

    def __init__(self, strategies: list[str] = None, accounts: list[str] = None):
        self.strategies = strategies or []
        self.accounts = accounts or []

    def snapshot(self) -> dict:
        """Get current performance snapshot across all bots."""
        report = {}
        filters = self.strategies if self.strategies else [""]

        for strat in filters:
            df = get_trades(strategy=strat)
            if df.empty:
                report[strat or "all"] = {"trades": 0, "pnl": 0, "win_rate": 0}
                continue

            total = len(df)
            wins = len(df[df["pnl"] > 0])
            pnl = df["pnl"].sum()
            report[strat or "all"] = {
                "trades": total,
                "wins": wins,
                "losses": total - wins,
                "win_rate": wins / total if total > 0 else 0,
                "total_pnl": round(pnl, 4),
                "avg_pnl": round(pnl / total, 4) if total > 0 else 0,
            }

        return report

    def print_dashboard(self) -> None:
        """Print a formatted performance dashboard."""
        snap = self.snapshot()
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        print(f"\n{'='*60}")
        print(f"  TRADING BOT MONITOR — {now}")
        print(f"{'='*60}")

        for name, stats in snap.items():
            print(f"\n  [{name.upper() or 'ALL'}]")
            print(f"    Trades:    {stats['trades']}")
            if stats["trades"] > 0:
                print(f"    Win rate:  {stats['win_rate']:.1%}")
                print(f"    Total PnL: ${stats['total_pnl']:.2f}")
                print(f"    Avg PnL:   ${stats['avg_pnl']:.4f}")

        print(f"\n{'='*60}\n")
