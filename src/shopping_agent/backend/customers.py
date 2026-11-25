"""Customer lookup."""

from __future__ import annotations

import json

from shopping_agent.backend.errors import NotFoundError
from shopping_agent.models import Customer
from shopping_agent.paths import customers_path


class CustomerStore:
    def __init__(self, customers: list[Customer]) -> None:
        self._customers = {customer.id: customer for customer in customers}

    @classmethod
    def from_json(cls, path=None) -> CustomerStore:
        path = path or customers_path()
        payload = json.loads(path.read_text(encoding="utf-8"))
        customers = [Customer.model_validate(row) for row in payload["customers"]]
        return cls(customers)

    def get(self, customer_id: str) -> Customer:
        try:
            return self._customers[customer_id]
        except KeyError as exc:
            raise NotFoundError(f"No customer with id {customer_id!r}.") from exc

    def all(self) -> list[Customer]:
        return list(self._customers.values())
