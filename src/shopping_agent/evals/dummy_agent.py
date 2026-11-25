"""Deterministic stand-in so the eval harness runs before the real agent exists.

This is a keyword router over the real backend — *not* an LLM agent. It exists
so `make eval` produces a report on day one. Replace it with ShoppingAgent
once you implement the loop (`--agent real`).
"""

from __future__ import annotations

import re
from typing import Any

from shopping_agent.agent.loop import AgentResult
from shopping_agent.backend import ShoppingService
from shopping_agent.backend.service import error_payload

_ORDER_RE = re.compile(r"\bORD-\d+\b", re.I)
_INJECTION = re.compile(
    r"ignore (all )?(previous|prior|above) (instructions|prompts)|"
    r"reveal (your )?(system )?prompt|you are now |jailbreak|dan mode",
    re.I,
)
_OUT_OF_SCOPE = re.compile(
    r"\b(write (me )?(a )?python virus|hack (into|the)|build a bomb|"
    r"medical (dosage|dose|advice)|diagnose my|stock tip|legal advice)\b",
    re.I,
)


class DummyAgent:
    def __init__(self, service: ShoppingService | None = None, customer_id: str = "CUST-1001") -> None:
        self.service = service or ShoppingService.default()
        self.customer_id = customer_id

    def run(self, user_message: str, *, customer_id: str | None = None) -> AgentResult:
        customer = customer_id or self.customer_id
        text = user_message.strip()
        calls: list[dict[str, Any]] = []

        if _INJECTION.search(text):
            return AgentResult(
                text=(
                    "I can't change my instructions or reveal a hidden prompt. "
                    "I can help you find products, manage a basket, or look up an order."
                ),
                tool_calls=calls,
                refused=True,
            )
        if _OUT_OF_SCOPE.search(text):
            return AgentResult(
                text=(
                    "That's outside what I can help with. I'm a grocery shopping assistant — "
                    "I can search products, build a basket, check an order, or log an issue."
                ),
                tool_calls=calls,
                refused=True,
            )

        lowered = text.lower()
        try:
            issue_hints = (
                "refund",
                "missing",
                "damaged",
                "wrong item",
                "complaint",
                "report an issue",
                "log an issue",
            )
            if any(word in lowered for word in issue_hints):
                order_match = _ORDER_RE.search(text)
                oid = order_match.group(0).upper() if order_match else None
                issue_type = (
                    "missing_item"
                    if "missing" in lowered
                    else ("damaged" if "damaged" in lowered else ("refund_request" if "refund" in lowered else "other"))
                )
                result = self.service.report_issue(customer, text, order_id=oid, issue_type=issue_type)
                calls.append(
                    {
                        "name": "report_issue",
                        "arguments": {"order_id": oid, "issue_type": issue_type},
                        "result": result,
                    }
                )
                issue = result["issue"]
                return AgentResult(
                    text=(
                        f"I've logged issue {issue['id']} ({issue['issue_type']}) for you. "
                        "A teammate can follow up on a refund if it's needed."
                    ),
                    tool_calls=calls,
                )

            if "order" in lowered or _ORDER_RE.search(text):
                order_match = _ORDER_RE.search(text)
                if order_match:
                    oid = order_match.group(0).upper()
                    result = self.service.get_order(oid, customer_id=customer)
                    calls.append({"name": "check_order", "arguments": {"order_id": oid}, "result": result})
                    order = result["order"]
                    return AgentResult(
                        text=(
                            f"Order {order['id']} is {order['status'].replace('_', ' ')}. "
                            f"Delivery window: {order['delivery_window']}. "
                            f"Total ${order['total_aud']:.2f}."
                        ),
                        tool_calls=calls,
                    )
                result = self.service.list_orders(customer)
                calls.append({"name": "check_order", "arguments": {}, "result": result})
                if not result["orders"]:
                    return AgentResult(text="I couldn't find any orders for this account.", tool_calls=calls)
                latest = result["orders"][0]
                return AgentResult(
                    text=f"Your most recent order is {latest['id']}, status {latest['status'].replace('_', ' ')}.",
                    tool_calls=calls,
                )

            add_hints = (
                "add to cart",
                "add to my cart",
                "add to basket",
                "put in my cart",
                "buy ",
                "add ",
            )
            if any(word in lowered for word in add_hints):
                # Search first, then add the top hit when the user names a product-ish phrase.
                query = re.sub(
                    r"(please )?(add|put|buy)\s+(to (my )?(cart|basket)\s*)?",
                    " ",
                    text,
                    flags=re.I,
                ).strip()
                search = self.service.search_products(query or text, limit=3)
                calls.append({"name": "search_products", "arguments": {"query": query or text}, "result": search})
                if not search["products"]:
                    return AgentResult(
                        text="I couldn't find a matching product to add.",
                        tool_calls=calls,
                    )
                product = search["products"][0]
                added = self.service.add_to_cart(customer, product["id"], 1)
                calls.append(
                    {
                        "name": "add_to_cart",
                        "arguments": {"product_id": product["id"], "quantity": 1},
                        "result": added,
                    }
                )
                cart = added["cart"]
                return AgentResult(
                    text=(
                        f"Added {product['name']} ({product['id']}) to your cart. "
                        f"Cart total is ${cart['total_aud']:.2f}."
                    ),
                    tool_calls=calls,
                )

            cart_hints = (
                "what's in my cart",
                "what is in my cart",
                "view cart",
                "show cart",
                "show my basket",
                "what's in my basket",
            )
            if any(word in lowered for word in cart_hints):
                result = self.service.view_cart(customer)
                calls.append({"name": "view_cart", "arguments": {}, "result": result})
                cart = result["cart"]
                if not cart["items"]:
                    return AgentResult(text="Your cart is empty.", tool_calls=calls)
                names = ", ".join(f"{i['quantity']} x {i['name']}" for i in cart["items"])
                return AgentResult(
                    text=(
                        f"Your cart: {names}. Total ${cart['total_aud']:.2f} "
                        f"(delivery ${cart['delivery_fee_aud']:.2f})."
                    ),
                    tool_calls=calls,
                )

            # Default: catalogue search. Extract a few common filters.
            dietary = []
            if "vegan" in lowered:
                dietary.append("vegan")
            if "gluten-free" in lowered or "gluten free" in lowered or re.search(r"\bgf\b", lowered):
                dietary.append("gluten-free")
            if "organic" in lowered:
                dietary.append("organic")
            if "vegetarian" in lowered:
                dietary.append("vegetarian")
            allergen_free = []
            if "nut-free" in lowered or "nut free" in lowered or "no nuts" in lowered or "without nuts" in lowered:
                allergen_free.extend(["peanuts", "tree-nuts"])
            if "no peanut" in lowered or "peanut-free" in lowered or "peanut free" in lowered:
                allergen_free.append("peanuts")
            if "dairy-free" in lowered or "dairy free" in lowered or "no dairy" in lowered:
                allergen_free.append("milk")
            price_match = re.search(r"under \$?(\d+(?:\.\d+)?)", lowered)
            max_price = float(price_match.group(1)) if price_match else None
            result = self.service.search_products(
                text,
                dietary_tags=dietary or None,
                allergen_free=allergen_free or None,
                max_price=max_price,
                limit=5,
            )
            calls.append(
                {
                    "name": "search_products",
                    "arguments": {
                        "query": text,
                        "dietary_tags": dietary,
                        "allergen_free": allergen_free,
                        "max_price": max_price,
                    },
                    "result": result,
                }
            )
            if not result["products"]:
                return AgentResult(
                    text="I couldn't find products matching that. Try a different keyword or filter.",
                    tool_calls=calls,
                )
            lines = [
                f"- {p['name']} ({p['id']}) by {p['brand']}, ${p['price_aud']:.2f} / {p['unit']}"
                for p in result["products"]
            ]
            return AgentResult(
                text="Here's what I found:\n" + "\n".join(lines),
                tool_calls=calls,
            )
        except Exception as exc:  # noqa: BLE001 - dummy agent boundary
            payload = error_payload(exc)
            return AgentResult(text=payload["message"], tool_calls=calls)
