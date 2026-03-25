"""Order management — handles limit order lifecycle."""

import logging
from dataclasses import dataclass, field
from typing import Optional

from data.polymarket_client import PolymarketClient

logger = logging.getLogger(__name__)


@dataclass
class Order:
    token_id: str
    side: str
    price: float
    size: float
    order_id: Optional[str] = None
    status: str = "pending"


class OrderManager:
    """Manage limit orders with duplicate prevention."""

    def __init__(self, client: PolymarketClient):
        self.client = client
        self._active_orders: dict[str, Order] = {}  # key: token_id+side

    def _order_key(self, token_id: str, side: str) -> str:
        return f"{token_id}:{side}"

    def has_active_order(self, token_id: str, side: str) -> bool:
        key = self._order_key(token_id, side)
        return key in self._active_orders

    def place_order(self, token_id: str, side: str, price: float, size: float) -> Optional[Order]:
        """Place a limit order, cancelling any existing order on the same side first."""
        key = self._order_key(token_id, side)

        # Cancel existing order on same side to avoid duplicates
        if key in self._active_orders:
            self.cancel_order(token_id, side)

        response = self.client.place_limit_order(token_id, side, price, size)
        order = Order(
            token_id=token_id,
            side=side,
            price=price,
            size=size,
            order_id=response.get("orderID"),
            status="active",
        )
        self._active_orders[key] = order
        logger.info("Order placed: %s %s %.2f @ %.4f", side, token_id[:16], size, price)
        return order

    def cancel_order(self, token_id: str, side: str) -> None:
        """Cancel an active order."""
        key = self._order_key(token_id, side)
        order = self._active_orders.pop(key, None)
        if order and order.order_id:
            self.client.cancel_all_orders(token_id)
            logger.info("Order cancelled: %s %s", side, token_id[:16])

    def cancel_all(self, token_id: str) -> None:
        """Cancel all orders for a token."""
        self.client.cancel_all_orders(token_id)
        keys_to_remove = [k for k in self._active_orders if k.startswith(token_id)]
        for k in keys_to_remove:
            del self._active_orders[k]
        logger.info("All orders cancelled for %s", token_id[:16])

    @property
    def active_orders(self) -> list[Order]:
        return list(self._active_orders.values())
