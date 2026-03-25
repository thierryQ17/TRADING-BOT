"""Data storage for candles and trades."""

import logging
import os
import sqlite3
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent
DB_PATH = DATA_DIR / "trades.db"


def save_candles_csv(df: pd.DataFrame, filename: str) -> Path:
    """Save candle DataFrame to CSV."""
    path = DATA_DIR / filename
    df.to_csv(path, index=False)
    logger.info("Saved %d candles to %s", len(df), path)
    return path


def load_candles_csv(filename: str) -> pd.DataFrame:
    """Load candle DataFrame from CSV."""
    path = DATA_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"No data file: {path}")
    df = pd.read_csv(path, parse_dates=["timestamp"])
    return df


def init_db() -> None:
    """Create trades table if it doesn't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            strategy TEXT NOT NULL,
            side TEXT NOT NULL,
            price REAL NOT NULL,
            size REAL NOT NULL,
            token_id TEXT NOT NULL,
            pnl REAL DEFAULT 0,
            account TEXT DEFAULT ''
        )
    """)
    conn.commit()
    conn.close()


def log_trade(
    strategy: str,
    side: str,
    price: float,
    size: float,
    token_id: str,
    pnl: float = 0,
    account: str = "",
) -> None:
    """Insert a trade record into the database."""
    from datetime import datetime, timezone

    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO trades (timestamp, strategy, side, price, size, token_id, pnl, account) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), strategy, side, price, size, token_id, pnl, account),
    )
    conn.commit()
    conn.close()


def get_trades(strategy: str = "", account: str = "") -> pd.DataFrame:
    """Query trades from the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM trades WHERE 1=1"
    params: list = []
    if strategy:
        query += " AND strategy = ?"
        params.append(strategy)
    if account:
        query += " AND account = ?"
        params.append(account)
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df
