"""Build a retrieval corpus from product descriptions and store policies."""

from __future__ import annotations

from dataclasses import dataclass, field

from shopping_agent.backend import ShoppingService


@dataclass
class DocumentChunk:
    id: str
    text: str
    source: str
    metadata: dict = field(default_factory=dict)


def load_corpus(service: ShoppingService | None = None) -> list[DocumentChunk]:
    """Return chunks you can embed and index.

    Each product becomes one chunk (name + brand + tags + description).
    Each policy markdown file is split on level-2 headings so retrieval can
    return a focused section (returns, fees, substitutions, ...).
    """
    service = service or ShoppingService.default()
    chunks: list[DocumentChunk] = []
    for product in service.catalog.all():
        tags = ", ".join(product.dietary_tags) or "none"
        allergens = ", ".join(product.allergens) or "none listed"
        text = (
            f"{product.name} ({product.brand}). "
            f"Category: {product.category}/{product.subcategory}. "
            f"Price: ${product.price_aud:.2f} AUD per {product.unit}. "
            f"Dietary tags: {tags}. Allergens: {allergens}. "
            f"{product.description} Stock: {product.stock}."
        )
        chunks.append(
            DocumentChunk(
                id=f"product:{product.id}",
                text=text,
                source="catalogue",
                metadata={
                    "product_id": product.id,
                    "name": product.name,
                    "category": product.category,
                    "price_aud": product.price_aud,
                },
            )
        )
    for document in service.load_policy_documents():
        chunks.extend(_split_markdown(document["id"], document["text"], source="policy"))
    return chunks


def _split_markdown(doc_id: str, text: str, *, source: str) -> list[DocumentChunk]:
    sections: list[tuple[str, list[str]]] = [("intro", [])]
    for line in text.splitlines():
        if line.startswith("## "):
            sections.append((line[3:].strip() or "section", []))
        else:
            sections[-1][1].append(line)
    chunks: list[DocumentChunk] = []
    for index, (title, lines) in enumerate(sections):
        body = "\n".join(lines).strip()
        if not body:
            continue
        chunk_text = f"{title}\n\n{body}" if title != "intro" else body
        chunks.append(
            DocumentChunk(
                id=f"{doc_id}:{index}",
                text=chunk_text,
                source=source,
                metadata={"title": title, "document": doc_id},
            )
        )
    return chunks
