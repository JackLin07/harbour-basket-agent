"""In-memory backend used by agent tools.

Tools should call ShoppingService methods rather than touching JSON files directly.
"""

from shopping_agent.backend.service import ShoppingService

__all__ = ["ShoppingService"]
