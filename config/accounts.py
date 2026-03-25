"""Multi-account configuration for running parallel bots."""

import os
from dotenv import load_dotenv

load_dotenv()


def get_account(name: str) -> dict:
    """Get account credentials by name.

    Accounts are configured via env vars:
        ACCOUNT_1_PRIVATE_KEY, ACCOUNT_1_FUNDER_ADDRESS
        ACCOUNT_2_PRIVATE_KEY, ACCOUNT_2_FUNDER_ADDRESS
        etc.

    Falls back to the default POLYMARKET_* vars for account_1.
    """
    prefix = name.upper().replace("-", "_")
    private_key = os.getenv(f"{prefix}_PRIVATE_KEY")
    funder = os.getenv(f"{prefix}_FUNDER_ADDRESS")

    if not private_key:
        # Fallback to default
        private_key = os.getenv("POLYMARKET_PRIVATE_KEY", "")
        funder = os.getenv("POLYMARKET_FUNDER_ADDRESS", "")

    return {
        "name": name,
        "private_key": private_key,
        "funder_address": funder,
    }


# Pre-defined accounts
ACCOUNTS = {
    "account_1": get_account("account_1"),
    "account_2": get_account("account_2"),
    "account_3": get_account("account_3"),
}
