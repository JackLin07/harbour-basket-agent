"""Command-line interface.

Subcommands `search`, `cart`, `orders`, and `issues` talk to the backend
directly so you can explore the synthetic data without an API key.

`chat` should call ShoppingAgent.run() once the loop is implemented.
"""

from __future__ import annotations

import argparse
import json
import sys

from shopping_agent.backend import ShoppingService
from shopping_agent.backend.service import error_payload
from shopping_agent.config import get_settings


def _dump(payload: dict) -> int:
    json.dump(payload, sys.stdout, indent=2, default=str)
    sys.stdout.write("\n")
    return 0 if payload.get("ok", True) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harbour-basket",
        description="Harbour Basket shopping assistant (synthetic AU supermarket demo).",
    )
    parser.add_argument(
        "--customer",
        default=None,
        help="Customer id (default: CUST-1001 / DEFAULT_CUSTOMER_ID).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="Search the catalogue (backend only, no LLM).")
    search.add_argument("query", nargs="?", default=None)
    search.add_argument("--category")
    search.add_argument("--max-price", type=float)
    search.add_argument("--dietary", nargs="*", default=None, help="Required dietary tags, e.g. vegan gluten-free")
    search.add_argument("--allergen-free", nargs="*", default=None, help="Exclude these allergens")
    search.add_argument("--limit", type=int, default=8)
    search.add_argument("--include-oos", action="store_true", help="Include out-of-stock items")

    sub.add_parser("cart", help="View the current cart.")
    add = sub.add_parser("add", help="Add a product id to the cart.")
    add.add_argument("product_id")
    add.add_argument("--qty", type=int, default=1)

    sub.add_parser("orders", help="List this customer's orders.")
    order = sub.add_parser("order", help="Show one order by id.")
    order.add_argument("order_id")

    issue = sub.add_parser("issue", help="Log an issue against an order.")
    issue.add_argument("description")
    issue.add_argument("--order-id")
    issue.add_argument("--type", dest="issue_type", default="other")

    chat = sub.add_parser("chat", help="Talk to the agent (not yet implemented).")
    chat.add_argument("message")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = get_settings()
    customer_id = args.customer or settings.default_customer_id
    service = ShoppingService.default()

    try:
        if args.command == "search":
            return _dump(
                service.search_products(
                    args.query,
                    category=args.category,
                    max_price=args.max_price,
                    dietary_tags=args.dietary,
                    allergen_free=args.allergen_free,
                    in_stock_only=not args.include_oos,
                    limit=args.limit,
                )
            )
        if args.command == "cart":
            return _dump(service.view_cart(customer_id))
        if args.command == "add":
            return _dump(service.add_to_cart(customer_id, args.product_id, args.qty))
        if args.command == "orders":
            return _dump(service.list_orders(customer_id))
        if args.command == "order":
            return _dump(service.get_order(args.order_id, customer_id=customer_id))
        if args.command == "issue":
            return _dump(
                service.report_issue(
                    customer_id,
                    args.description,
                    order_id=args.order_id,
                    issue_type=args.issue_type,
                )
            )
        if args.command == "chat":
            from shopping_agent.agent.loop import ShoppingAgent

            agent = ShoppingAgent(service=service, settings=settings, customer_id=customer_id)
            result = agent.run(args.message, customer_id=customer_id)
            payload = {
                "ok": True,
                "text": result.text,
                "tool_calls": result.tool_calls,
                "refused": result.refused,
            }
            return _dump(payload)
    except NotImplementedError as exc:
        print(f"TODO: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        return _dump(error_payload(exc))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
