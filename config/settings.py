"""Global bot configuration."""

import os
from dotenv import load_dotenv

load_dotenv()

# --- Polymarket ---
POLYMARKET_HOST = "https://clob.polymarket.com"
CHAIN_ID = 137  # Polygon mainnet
SIGNATURE_TYPE = 2  # EIP-1271

PRIVATE_KEY = os.getenv("POLYMARKET_PRIVATE_KEY", "")
FUNDER_ADDRESS = os.getenv("POLYMARKET_FUNDER_ADDRESS", "")

# --- Trading ---
DEFAULT_TIMEFRAME = "5m"
DEFAULT_POSITION_SIZE = 1.0  # USD
ORDER_TYPE = "limit"  # always limit — market orders have fees on Polymarket

# --- Risk ---
MAX_POSITION_SIZE = float(os.getenv("MAX_POSITION_SIZE", "10"))
MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "50"))
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "3"))
STOP_LOSS_PCT = 0.05  # 5%
TAKE_PROFIT_PCT = 0.10  # 10%

# --- Strategy defaults ---
MACD_FAST = 3
MACD_SLOW = 15
MACD_SIGNAL = 3

RSI_PERIOD = 14
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70

CVD_LOOKBACK = 20

# --- Operational ---
DRY_RUN = os.getenv("DRY_RUN", "true").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
