"""Launch the monitoring dashboard."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from incubation.monitor import Monitor
from incubation.logger import setup_logging


def main():
    logger = setup_logging("monitor")
    monitor = Monitor(strategies=["macd", "rsi_mean_reversion", "cvd"])

    logger.info("Monitor started — refreshing every 60s (Ctrl+C to stop)")

    while True:
        monitor.print_dashboard()
        time.sleep(60)


if __name__ == "__main__":
    main()
