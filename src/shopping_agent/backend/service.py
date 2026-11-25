"""Facade that agent tools should call.

All methods return plain JSON-serialisable dicts (or raise ShoppingError), so a
tool handler can be a thin wrapper.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from shopping_agent.backend.cart import CartStore
from shopping_agent.backend.catalog import Catalog
from shopping_agent.backend.customers import CustomerStore
from shopping_agent.backend.errors import ShoppingError
from shopping_agent.backend.issues import IssueStore
from shopping_agent.backend.orders import OrderStore
from shopping_agent.models import IssueType
from shopping_agent.paths import policies_dir


class ShoppingService:
    """In-memory Harbour Basket backend, loaded from the synthetic JSON data."""

    def __init__(
        self,
        catalog: Catalog | None = None,
        customers: CustomerStore | None = None,
        orders: OrderStore | None = None,
        issues: IssueStore | None = None,
        carts: CartStore | None = None,
    ) -> None:
        self.catalog = catalog or Catalog.from_json()
        self.customers = customers or CustomerStore.from_json()
        self.orders = orders or OrderStore.from_json()
        self.issues = issues or IssueStore.from_json()
        self.carts = carts or CartStore(self.catalog)

    @classmethod
    def default(cls) -> ShoppingService:
        return cls()

    # --- catalogue ---

    def search_products(
        self,
        query: str | None = None,
        *,
        category: str | None = None,
        subcategory: str | None = None,
        dietary_tags: Iterable[str] | None = None,
        allergen_free: Iterable[str] | None = None,
        max_price: float | None = None,
        in_stock_only: bool = True,
        brand: str | None = None,
        limit: int = 8,
    ) -> dict:
        products = self.catalog.search(
            query,
            category=category,
            subcategory=subcategory,
            dietary_tags=dietary_tags,
            allergen_free=allergen_free,
            max_price=max_price,
            in_stock_only=in_stock_only,
            brand=brand,
            limit=limit,
        )
        return {
            "ok": True,
            "count": len(products),
            "products": [product.model_dump(mode="json") for product in products],
        }

    def get_product(self, product_id: str) -> dict:
        product = self.catalog.get(product_id)
        return {"ok": True, "product": product.model_dump(mode="json")}

    # --- cart ---

    def add_to_cart(self, customer_id: str, product_id: str, quantity: int = 1) -> dict:
        self.customers.get(customer_id)  # ensure the customer exists
        cart = self.carts.add(customer_id, product_id, quantity)
        return {"ok": True, "cart": cart.model_dump(mode="json")}

    def view_cart(self, customer_id: str) -> dict:
        self.customers.get(customer_id)
        cart = self.carts.get(customer_id)
        return {"ok": True, "cart": cart.model_dump(mode="json")}

    def update_cart_item(self, customer_id: str, product_id: str, quantity: int) -> dict:
        self.customers.get(customer_id)
        cart = self.carts.update(customer_id, product_id, quantity)
        return {"ok": True, "cart": cart.model_dump(mode="json")}

    def remove_from_cart(self, customer_id: str, product_id: str) -> dict:
        self.customers.get(customer_id)
        cart = self.carts.remove(customer_id, product_id)
        return {"ok": True, "cart": cart.model_dump(mode="json")}

    def clear_cart(self, customer_id: str) -> dict:
        self.customers.get(customer_id)
        cart = self.carts.clear(customer_id)
        return {"ok": True, "cart": cart.model_dump(mode="json")}

    # --- orders ---

    def get_order(self, order_id: str, customer_id: str | None = None) -> dict:
        order = self.orders.get(order_id, customer_id=customer_id)
        return {"ok": True, "order": order.model_dump(mode="json")}

    def list_orders(self, customer_id: str) -> dict:
        self.customers.get(customer_id)
        orders = self.orders.list_for_customer(customer_id)
        return {
            "ok": True,
            "count": len(orders),
            "orders": [order.model_dump(mode="json") for order in orders],
        }

    # --- issues ---

    def report_issue(
        self,
        customer_id: str,
        description: str,
        *,
        order_id: str | None = None,
        issue_type: IssueType = "other",
        product_ids: list[str] | None = None,
    ) -> dict:
        self.customers.get(customer_id)
        if order_id:
            # Validates ownership when a customer id is supplied.
            self.orders.get(order_id, customer_id=customer_id)
        issue = self.issues.report(
            customer_id,
            description,
            order_id=order_id,
            issue_type=issue_type,
            product_ids=product_ids,
        )
        return {"ok": True, "issue": issue.model_dump(mode="json")}

    def list_issues(self, customer_id: str) -> dict:
        self.customers.get(customer_id)
        issues = self.issues.list_for_customer(customer_id)
        return {
            "ok": True,
            "count": len(issues),
            "issues": [issue.model_dump(mode="json") for issue in issues],
        }

    # --- policies (for RAG corpus loading; not a search) ---

    def load_policy_documents(self, directory: Path | None = None) -> list[dict[str, str]]:
        folder = directory or policies_dir()
        documents: list[dict[str, str]] = []
        for path in sorted(folder.glob("*.md")):
            documents.append(
                {
                    "id": f"policy:{path.stem}",
                    "title": path.stem,
                    "path": str(path),
                    "text": path.read_text(encoding="utf-8"),
                }
            )
        return documents


def error_payload(exc: Exception) -> dict:
    if isinstance(exc, ShoppingError):
        return exc.to_dict()
    return {"ok": False, "error": "internal_error", "message": str(exc)}
