"""Embedding helpers and notes on which backend to pick.

Already implemented:
  - l2_normalize and cosine_similarity (numpy)
  - EmbeddingClient protocol
  - HashingEmbedder: a *toy* offline baseline so the retriever can be wired
    without downloading a model or paying for an API. Do not present this as
    the RAG solution in the README — swap it for a real embedder.

Choose one real backend (notes below) and implement encode().

1) sentence-transformers (local, free, no key)
   Official quickstart: https://sbert.net/docs/quickstart.html
   Good default for a laptop demo: "sentence-transformers/all-MiniLM-L6-v2"
   (384-d, fast). Better quality: "sentence-transformers/all-mpnet-base-v2".
   pip install 'harbour-basket-agent[rag]'  or  pip install sentence-transformers
   Then: SentenceTransformer(model).encode(texts, normalize_embeddings=True)

2) OpenAI embeddings API
   Official guide: https://developers.openai.com/api/docs/guides/embeddings
   Model: text-embedding-3-small (cheap, strong).
   client.embeddings.create(model=..., input=texts)

3) Azure OpenAI embeddings (relevant to the Coles listing: AI Foundry)
   Same API shape, but you point the client at AZURE_OPENAI_ENDPOINT and an
   embedding deployment name. Nice to mention in the README even if you demo
   with (1) or (2) in the local demo.

Cosine search over ~200 short chunks does not need a vector database. A numpy
matrix is enough at this scale. In production, use Azure AI Search
or Cosmos DB vector index — leave that for the "what I would do in production"
README section.
"""

from __future__ import annotations

import hashlib
from typing import Protocol, runtime_checkable

import numpy as np

Vector = np.ndarray


def l2_normalize(matrix: Vector) -> Vector:
    """Normalize vectors along the last axis. Zero rows stay zero."""
    array = np.asarray(matrix, dtype=np.float32)
    if array.ndim == 1:
        denom = np.linalg.norm(array)
        return array if denom == 0 else array / denom
    denom = np.linalg.norm(array, axis=1, keepdims=True)
    denom = np.where(denom == 0, 1.0, denom)
    return array / denom


def cosine_similarity(query: Vector, documents: Vector) -> Vector:
    """Return a 1-D array of cosine similarities between query and each document row.

    Inputs are L2-normalized if they are not already.
    """
    query_vec = l2_normalize(np.asarray(query, dtype=np.float32).reshape(-1))
    docs = np.asarray(documents, dtype=np.float32)
    if docs.ndim == 1:
        docs = docs.reshape(1, -1)
    docs = l2_normalize(docs)
    return docs @ query_vec


@runtime_checkable
class EmbeddingClient(Protocol):
    def encode(self, texts: list[str]) -> Vector:
        """Return an (n, d) float32 array, ideally already L2-normalized."""
        ...


class HashingEmbedder:
    """Toy hashed bag-of-words embedder. Deterministic, no network, weak quality.

    Use this only to prove your retriever wiring, then replace it.
    """

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def encode(self, texts: list[str]) -> Vector:
        matrix = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for token in text.lower().split():
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                index = int.from_bytes(digest[:4], "little") % self.dim
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                matrix[row, index] += sign
        return l2_normalize(matrix)


# TODO: implement SentenceTransformerEmbedder and/or OpenAIEmbedder
# and a factory build_embedder(settings) similar to shopping_agent.llm.build_client.
