import numpy as np
import pytest

from shopping_agent.rag.chunks import load_corpus
from shopping_agent.rag.embeddings import HashingEmbedder, cosine_similarity, l2_normalize


def test_policy_documents_load(service):
    docs = service.load_policy_documents()
    titles = {doc["title"] for doc in docs}
    assert {"returns", "refunds", "delivery", "substitutions", "faq"}.issubset(titles)
    delivery = next(doc for doc in docs if doc["title"] == "delivery")
    assert "$9" in delivery["text"] or "$9.00" in delivery["text"]
    assert "$50" in delivery["text"]


def test_corpus_includes_products_and_policies(service):
    chunks = load_corpus(service)
    sources = {chunk.source for chunk in chunks}
    assert "catalogue" in sources
    assert "policy" in sources
    assert any("HB-1001" in chunk.id for chunk in chunks)
    assert any("return" in chunk.text.lower() for chunk in chunks)
    assert len(chunks) > 200  # 200 products plus policy sections


def test_cosine_similarity_identical_vectors():
    vector = l2_normalize(np.array([1.0, 2.0, 3.0], dtype=np.float32))
    scores = cosine_similarity(vector, np.stack([vector, -vector]))
    assert scores[0] == pytest.approx(1.0, abs=1e-5)
    assert scores[1] == pytest.approx(-1.0, abs=1e-5)


def test_hashing_embedder_is_deterministic():
    embedder = HashingEmbedder(dim=64)
    first = embedder.encode(["ripe hass avocado"])
    second = embedder.encode(["ripe hass avocado"])
    other = embedder.encode(["dishwasher tablets"])
    assert first.shape == (1, 64)
    assert np.allclose(first, second)
    score = float(cosine_similarity(first[0], other)[0])
    assert score < 0.9
