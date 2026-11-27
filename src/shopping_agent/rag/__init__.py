"""RAG helpers. Chunk loading is done; the retriever is not yet implemented."""

from shopping_agent.rag.chunks import DocumentChunk, load_corpus
from shopping_agent.rag.embeddings import cosine_similarity, l2_normalize

__all__ = ["DocumentChunk", "load_corpus", "cosine_similarity", "l2_normalize"]
