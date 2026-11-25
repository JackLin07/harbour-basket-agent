"""Order lookup over the synthetic order history."""

from __future__ import annotations

import json

from shopping_agent.backend.errors import NotFoundError, PermissionError_
from shopping_agent.models import Order
from shopping_agent.paths import orders_path


class OrderStore:
    def __init__(self, orders: list[Order]) -> None:
        self._orders = {order.id: order for order in orders}

    @classmethod
    def from_json(cls, path=None) -> OrderStore:
        path = path or orders_path()
        payload = json.loads(path.read_text(encoding="utf-8"))
        orders = [Order.model_validate(row) for row in payload["orders"]]
        return cls(orders)

    def get(self, order_id: str, customer_id: str | None = None) -> Order:
        try:
            order = self._orders[order_id]
        except KeyError as exc:
            raise NotFoundError(f"No order with id {order_id!r}.") from exc
        if customer_id is not None and order.customer_id != customer_id:
            raise PermissionError_(f"Order {order_id} does not belong to this customer.")
        return order

    def list_for_customer(self, customer_id: str) -> list[Order]:
        orders = [order for order in self._orders.values() if order.customer_id == customer_id]
        return sorted(orders, key=lambda order: order.placed_at, reverse=True)
