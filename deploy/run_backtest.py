"""Launch backtests for all three strategies."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.downloader import OHLCVDownloader
from strategies.macd_strategy import MACDStrategy
from strategies.rsi_mean_reversion import RSIMeanReversionStrategy
from strategies.cvd_strategy import CVDStrategy
from backtesting.runner import run_all
from incubation.logger import setup_logging


def main():
    logger = setup_logging("backtest")
    logger.info("Starting backtest run...")

    # Download data
    logger.info("Downloading historical data...")
    downloader = OHLCVDownloader(exchange_id="binance")
    df = downloader.fetch(symbol="BTC/USDT", timeframe="5m", days_back=30)

    if df.empty:
        logger.error("No data downloaded — check your internet connection")
        sys.exit(1)

    logger.info("Data: %d candles from %s to %s", len(df), df["timestamp"].iloc[0], df["timestamp"].iloc[-1])

    # Run all strategies
    strategies = [
        MACDStrategy(),
        RSIMeanReversionStrategy(),
        CVDStrategy(),
    ]

    results = run_all(
        strategies=strategies,
        df=df,
        parallel=True,
        position_size=1.0,
        stop_loss_pct=0.05,
        take_profit_pct=0.10,
    )

    # Summary
    print("\n" + "=" * 60)
    print("  BACKTEST SUMMARY — RANKING")
    print("=" * 60)
    for i, r in enumerate(sorted(results, key=lambda x: x.total_pnl, reverse=True), 1):
        status = "PASS" if r.win_rate > 0.55 and r.profit_factor > 1.5 else "FAIL"
        print(f"  #{i} {r.strategy:<20} PnL: ${r.total_pnl:>8.2f}  WR: {r.win_rate:.0%}  PF: {r.profit_factor:.2f}  [{status}]")
    print("=" * 60)


if __name__ == "__main__":
    main()
