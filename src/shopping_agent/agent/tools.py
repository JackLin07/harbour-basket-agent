"""Tool schemas and dispatch.

TODO (weekend, Saturday morning/afternoon):
  1. Fill TOOL_SCHEMAS with JSON Schema that matches an OpenAI/Anthropic function tool.
  2. Implement `execute_tool` so each tool name calls ShoppingService and returns JSON.
  3. Keep the schemas and the Python callables in sync.

Suggested tools (align with the job ad + the weekend plan):
  - search_products(query, category?, dietary_tags?, allergen_free?, max_price?, limit?)
  - add_to_cart(product_id, quantity=1)
  - view_cart()
  - check_order(order_id?)           # list recent orders if order_id omitted
  - report_issue(description, order_id?, issue_type?, product_ids?)
  - retrieve_knowledge(query)        # wrap your RAG retriever for policies + product blurbs

The service layer is already done, so a tool body should look like:

    def search_products(query: str, ...) -> str:
        result = service.search_products(query, ...)
        return json.dumps(result)

Official docs: https://developers.openai.com/api/docs/guides/function-calling
"""

from __future__ import annotations

import json
from typing import Any

from shopping_agent.backend import ShoppingService
from shopping_agent.backend.service import error_payload

# TODO: replace this empty list with real JSON-schema tool definitions, e.g.
# {
#   "type": "function",
#   "function": {
#       "name": "search_products",
#       "description": "Search the Harbour Basket catalogue by keywords and filters.",
#       "parameters": {
#           "type": "object",
#           "properties": {
#               "query": {"type": "string"},
#               "dietary_tags": {"type": "array", "items": {"type": "string"}},
#               "allergen_free": {"type": "array", "items": {"type": "string"}},
#               "max_price": {"type": "number"},
#               "limit": {"type": "integer"},
#           },
#           "required": [],
#       },
#   },
# }
TOOL_SCHEMAS: list[dict[str, Any]] = []


class ToolNotImplementedError(NotImplementedError):
    """Raised until the weekend tool dispatch is filled in."""


def execute_tool(name: str, arguments: dict[str, Any], *, service: ShoppingService, customer_id: str) -> str:
    """Run one tool and return a JSON string for the model.

    TODO: dispatch on `name` to the service methods. Always return a string
    (JSON) so the agent loop can append a tool-result message. Catch ShoppingError
    with error_payload() rather than letting exceptions break the loop.
    """
    raise ToolNotImplementedError(
        f"Tool {name!r} is not implemented yet. Wire it to ShoppingService in "
        "shopping_agent/agent/tools.py (see the docstring for the suggested set)."
    )
    # Example once you start:
    # try:
    #     if name == "search_products":
    #         return json.dumps(service.search_products(**arguments))
    #     if name == "add_to_cart":
    #         return json.dumps(service.add_to_cart(customer_id, **arguments))
    #     if name == "view_cart":
    #         return json.dumps(service.view_cart(customer_id))
    #     if name == "check_order":
    #         order_id = arguments.get("order_id")
    #         if order_id:
    #             return json.dumps(service.get_order(order_id, customer_id=customer_id))
    #         return json.dumps(service.list_orders(customer_id))
    #     if name == "report_issue":
    #         return json.dumps(service.report_issue(customer_id, **arguments))
    #     return json.dumps({"ok": False, "error": "unknown_tool", "message": name})
    # except Exception as exc:  # noqa: BLE001 - tool boundary
    #     return json.dumps(error_payload(exc))


# Silence unused-import warnings in the stub; both are used in the example above.
_ = (json, error_payload)
