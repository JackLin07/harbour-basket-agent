"""In-memory product catalogue with keyword and filter search."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable

from shopping_agent.backend.errors import NotFoundError
from shopping_agent.models import Product
from shopping_agent.paths import products_path

_TOKEN = re.compile(r"[a-z0-9]+")

# Very small synonym map so "gumboots" is not needed, but "avocado" / "avo" still works,
# and dietary phrasing like "gf" matches gluten-free tags.
_SYNONYMS: dict[str, set[str]] = {
    "avo": {"avocado", "avocados"},
    "avocado": {"avocado", "avocados", "hass"},
    "gf": {"gluten", "free"},
    "glutenfree": {"gluten", "free"},
    "veggie": {"vegetarian", "vegetable", "vegetables"},
    "soda": {"soft", "drink", "cola"},
    "soft": {"soft", "drink"},
    "crisps": {"crisps", "chips"},
    "chips": {"chips", "crisps"},
    "mince": {"mince", "minced"},
    "nappies": {"nappies", "nappy", "diapers"},
    "diapers": {"nappies", "nappy", "diapers"},
    "coriander": {"coriander", "cilantro"},
    "capsicum": {"capsicum", "pepper"},
}


def tokenize(text: str, *, expand: bool = False) -> set[str]:
    tokens = set(_TOKEN.findall(text.lower()))
    if not expand:
        return tokens
    expanded: set[str] = set(tokens)
    for token in tokens:
        expanded.update(_SYNONYMS.get(token, set()))
    return expanded


class Catalog:
    def __init__(self, products: list[Product]) -> None:
        self._products = {product.id: product for product in products}
        self._index = {product.id: self._haystack(product) for product in products}

    @classmethod
    def from_json(cls, path=None) -> Catalog:
        path = path or products_path()
        payload = json.loads(path.read_text(encoding="utf-8"))
        products = [Product.model_validate(row) for row in payload["products"]]
        return cls(products)

    def all(self) -> list[Product]:
        return list(self._products.values())

    def get(self, product_id: str) -> Product:
        try:
            return self._products[product_id]
        except KeyError as exc:
            raise NotFoundError(f"No product with id {product_id!r}.") from exc

    def search(
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
        limit: int = 10,
    ) -> list[Product]:
        """Search the catalogue.

        Keyword search is a simple token overlap over name, brand, category,
        tags, allergens, and description. This is *not* RAG; the retriever
        (weekend TODO) should sit in front when the query is semantic.
        """
        required_tags = {tag.lower() for tag in (dietary_tags or [])}
        banned_allergens = {tag.lower() for tag in (allergen_free or [])}
        query_tokens = tokenize(query, expand=True) if query else set()

        scored: list[tuple[float, Product]] = []
        for product in self._products.values():
            if category and product.category.lower() != category.lower():
                continue
            if subcategory and product.subcategory.lower() != subcategory.lower():
                continue
            if brand and product.brand.lower() != brand.lower():
                continue
            if in_stock_only and not product.in_stock:
                continue
            if max_price is not None and product.price_aud > max_price:
                continue
            tags = {tag.lower() for tag in product.dietary_tags}
            if required_tags and not required_tags.issubset(tags):
                continue
            allergens = {tag.lower() for tag in product.allergens}
            if banned_allergens and allergens.intersection(banned_allergens):
                continue
            if query_tokens:
                overlap = len(query_tokens & self._index[product.id])
                if overlap == 0:
                    # allow substring hits on the raw name for things like "HB-1001"
                    blob = f"{product.id} {product.name}".lower()
                    if query.lower() not in blob:
                        continue
                    overlap = 1
                # Slight boost if the name itself matches.
                name_tokens = tokenize(product.name)
                score = overlap + 0.5 * len(query_tokens & name_tokens)
            else:
                score = 1.0
            scored.append((score, product))

        scored.sort(key=lambda pair: (-pair[0], pair[1].name.lower()))
        return [product for _, product in scored[: max(limit, 0)]]

    @staticmethod
    def _haystack(product: Product) -> set[str]:
        parts = [
            product.id,
            product.name,
            product.brand,
            product.category,
            product.subcategory,
            product.unit,
            product.description,
            *product.dietary_tags,
            *product.allergens,
        ]
        return tokenize(" ".join(parts))
