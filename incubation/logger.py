"""Structured trade logging for incubation monitoring."""

import logging
import json
from datetime import datetime, timezone
from pathlib import Path

LOGS_DIR = Path(__file__).parent.parent / "logs"


def setup_logging(strategy_name: str, level: str = "INFO") -> logging.Logger:
    """Configure file + console logging for a bot instance."""
    LOGS_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger(strategy_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Console
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s — %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(console)

    # File
    log_file = LOGS_DIR / f"{strategy_name}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    ))
    logger.addHandler(file_handler)

    return logger


def log_trade_event(strategy: str, event: dict) -> None:
    """Append a structured JSON trade event to a JSONL file."""
    LOGS_DIR.mkdir(exist_ok=True)
    path = LOGS_DIR / f"{strategy}_trades.jsonl"
    event["timestamp"] = datetime.now(timezone.utc).isoformat()
    event["strategy"] = strategy
    with open(path, "a") as f:
        f.write(json.dumps(event) + "\n")
