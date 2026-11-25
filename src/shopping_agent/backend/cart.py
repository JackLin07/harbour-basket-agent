"""In-memory per-customer shopping carts."""

from __future__ import annotations

from shopping_agent.backend.catalog import Catalog
from shopping_agent.backend.errors import NotFoundError, OutOfStockError, ValidationError
from shopping_agent.models import Cart, CartItem

FREE_DELIVERY_THRESHOLD = 50.0
DELIVERY_FEE = 9.0


class CartStore:
    def __init__(self, catalog: Catalog) -> None:
        self._catalog = catalog
        self._carts: dict[str, list[CartItem]] = {}

    def get(self, customer_id: str) -> Cart:
        items = [item.model_copy() for item in self._carts.get(customer_id, [])]
        return self._with_totals(customer_id, items)

    def add(self, customer_id: str, product_id: str, quantity: int = 1) -> Cart:
        if quantity < 1:
            raise ValidationError("quantity must be at least 1.")
        product = self._catalog.get(product_id)
        if not product.in_stock:
            raise OutOfStockError(f"{product.name} ({product.id}) is out of stock and cannot be added to the cart.")
        if quantity > product.stock:
            raise OutOfStockError(f"Only {product.stock} of {product.name} ({product.id}) available.")
        items = self._carts.setdefault(customer_id, [])
        for item in items:
            if item.product_id == product_id:
                new_qty = item.quantity + quantity
                if new_qty > product.stock:
                    raise OutOfStockError(f"Only {product.stock} of {product.name} ({product.id}) available.")
                item.quantity = new_qty
                item.line_total_aud = round(item.unit_price_aud * item.quantity, 2)
                return self.get(customer_id)
        items.append(
            CartItem(
                product_id=product.id,
                name=product.name,
                unit_price_aud=product.price_aud,
                quantity=quantity,
                line_total_aud=round(product.price_aud * quantity, 2),
                in_stock=True,
            )
        )
        return self.get(customer_id)

    def update(self, customer_id: str, product_id: str, quantity: int) -> Cart:
        if quantity < 0:
            raise ValidationError("quantity cannot be negative.")
        if quantity == 0:
            return self.remove(customer_id, product_id)
        items = self._carts.get(customer_id, [])
        for item in items:
            if item.product_id == product_id:
                product = self._catalog.get(product_id)
                if quantity > product.stock:
                    raise OutOfStockError(f"Only {product.stock} of {product.name} ({product.id}) available.")
                item.quantity = quantity
                item.line_total_aud = round(item.unit_price_aud * quantity, 2)
                return self.get(customer_id)
        raise NotFoundError(f"{product_id} is not in the cart.")

    def remove(self, customer_id: str, product_id: str) -> Cart:
        items = self._carts.get(customer_id, [])
        new_items = [item for item in items if item.product_id != product_id]
        if len(new_items) == len(items):
            raise NotFoundError(f"{product_id} is not in the cart.")
        self._carts[customer_id] = new_items
        return self.get(customer_id)

    def clear(self, customer_id: str) -> Cart:
        self._carts[customer_id] = []
        return self.get(customer_id)

    @staticmethod
    def _with_totals(customer_id: str, items: list[CartItem]) -> Cart:
        subtotal = round(sum(item.line_total_aud for item in items), 2)
        fee = 0.0 if subtotal >= FREE_DELIVERY_THRESHOLD or subtotal == 0 else DELIVERY_FEE
        return Cart(
            customer_id=customer_id,
            items=items,
            subtotal_aud=subtotal,
            delivery_fee_aud=fee,
            total_aud=round(subtotal + fee, 2),
            free_delivery_threshold_aud=FREE_DELIVERY_THRESHOLD,
        )
