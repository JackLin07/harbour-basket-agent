"""Helpers for locating the synthetic data files."""

from __future__ import annotations

from pathlib import Path

from shopping_agent.config import get_settings


def data_dir() -> Path:
    path = get_settings().data_dir
    if not path.exists():
        raise FileNotFoundError(f"Data directory not found: {path}")
    return path


def products_path() -> Path:
    return data_dir() / "products.json"


def customers_path() -> Path:
    return data_dir() / "customers.json"


def orders_path() -> Path:
    return data_dir() / "orders.json"


def issues_path() -> Path:
    return data_dir() / "issues.json"


def policies_dir() -> Path:
    return data_dir() / "policies"
