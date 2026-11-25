"""In-memory retriever. Weekend TODO — signatures and algorithm notes only.

Algorithm to implement in InMemoryRetriever:

    1. load_corpus() from shopping_agent.rag.chunks (already done).
    2. embedder.encode([chunk.text for chunk in corpus]) -> (n, d) matrix.
    3. Store the matrix and the chunks.
    4. For a query: encode([query]), cosine_similarity(query, matrix),
       take the top_k indices, return those DocumentChunks plus scores.
    5. Optionally filter by source ("policy" vs "catalogue").

Do not pull in LangChain. A class with build() + retrieve() is enough.
"""

from __future__ import annotations

from dataclasses import dataclass

from shopping_agent.backend import ShoppingService
from shopping_agent.rag.chunks import DocumentChunk, load_corpus
from shopping_agent.rag.embeddings import EmbeddingClient, cosine_similarity


@dataclass
class RetrievalHit:
    chunk: DocumentChunk
    score: float


class InMemoryRetriever:
    """Numpy cosine retriever over the product + policy corpus."""

    def __init__(self, embedder: EmbeddingClient, service: ShoppingService | None = None) -> None:
        self.embedder = embedder
        self.service = service
        self.chunks: list[DocumentChunk] = []
        self._matrix = None  # set in build()

    def build(self) -> InMemoryRetriever:
        """TODO: load the corpus, embed every chunk, store the matrix.

        Suggested body:

            self.chunks = load_corpus(self.service)
            self._matrix = self.embedder.encode([c.text for c in self.chunks])
            return self
        """
        raise NotImplementedError(
            "Implement InMemoryRetriever.build() in shopping_agent/rag/retriever.py. "
            "See the docstring for the suggested body. load_corpus() and cosine_similarity() "
            "are already implemented."
        )

    def retrieve(self, query: str, *, top_k: int = 5, source: str | None = None) -> list[RetrievalHit]:
        """TODO: embed the query, score against the index, return top_k hits.

        Suggested body:

            if self._matrix is None:
                self.build()
            query_vec = self.embedder.encode([query])[0]
            scores = cosine_similarity(query_vec, self._matrix)
            order = scores.argsort()[::-1]
            hits = []
            for index in order:
                chunk = self.chunks[index]
                if source and chunk.source != source:
                    continue
                hits.append(RetrievalHit(chunk=chunk, score=float(scores[index])))
                if len(hits) >= top_k:
                    break
            return hits
        """
        raise NotImplementedError("Implement InMemoryRetriever.retrieve() in shopping_agent/rag/retriever.py.")


# Keep the already-written helpers imported so the TODO snippets are accurate.
_ = (load_corpus, cosine_similarity)
