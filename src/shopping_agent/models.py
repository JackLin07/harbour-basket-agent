"""Shared domain models. These are the shapes tools should return."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

OrderStatus = Literal[
    "processing",
    "in_transit",
    "delivered",
    "cancelled",
    "missing_item",
    "ready_for_pickup",
]
IssueType = Literal[
    "missing_item",
    "damaged",
    "wrong_item",
    "quality",
    "late_delivery",
    "refund_request",
    "other",
]
IssueStatus = Literal["open", "refund_issued", "replaced", "closed"]


class Product(BaseModel):
    id: str
    name: str
    brand: str
    category: str
    subcategory: str
    price_aud: float
    unit: str
    dietary_tags: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    description: str
    stock: int
    currency: str = "AUD"

    @property
    def in_stock(self) -> bool:
        return self.stock > 0


class Customer(BaseModel):
    id: str
    name: str
    email: str
    suburb: str
    state: str
    postcode: str
    dietary_preferences: list[str] = Field(default_factory=list)
    allergens_to_avoid: list[str] = Field(default_factory=list)
    default_address: str


class OrderItem(BaseModel):
    product_id: str
    name: str
    unit_price_aud: float
    quantity: int
    line_total_aud: float


class Order(BaseModel):
    id: str
    customer_id: str
    status: OrderStatus
    placed_at: datetime
    delivered_at: datetime | None = None
    cancelled_at: datetime | None = None
    delivery_window: str
    address: str
    items: list[OrderItem]
    notes: str | None = None
    substitution_preference: str | None = None
    missing_product_ids: list[str] = Field(default_factory=list)
    subtotal_aud: float
    delivery_fee_aud: float
    total_aud: float


class CartItem(BaseModel):
    product_id: str
    name: str
    unit_price_aud: float
    quantity: int
    line_total_aud: float
    in_stock: bool = True


class Cart(BaseModel):
    customer_id: str
    items: list[CartItem] = Field(default_factory=list)
    subtotal_aud: float = 0.0
    delivery_fee_aud: float = 9.0
    total_aud: float = 0.0
    free_delivery_threshold_aud: float = 50.0


class Issue(BaseModel):
    id: str
    customer_id: str
    order_id: str | None = None
    issue_type: IssueType
    product_ids: list[str] = Field(default_factory=list)
    description: str
    status: IssueStatus = "open"
    created_at: datetime
    resolution: str | None = None
