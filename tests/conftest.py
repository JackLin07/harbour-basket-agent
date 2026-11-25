"""Shared fixtures. Each test gets a fresh ShoppingService loaded from the JSON data."""

from __future__ import annotations

import pytest

from shopping_agent.backend import ShoppingService


@pytest.fixture()
def service() -> ShoppingService:
    return ShoppingService.default()
