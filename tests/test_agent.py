"""Placeholder tests for the agent implementation."""

import pytest

from shopping_agent.agent.loop import ShoppingAgent
from shopping_agent.agent.tools import TOOL_SCHEMAS, execute_tool
from shopping_agent.backend import ShoppingService
from shopping_agent.mcp_server.server import build_server
from shopping_agent.rag.embeddings import HashingEmbedder
from shopping_agent.rag.retriever import InMemoryRetriever


@pytest.mark.agent
@pytest.mark.xfail(reason="not yet implemented", strict=False)
def test_agent_can_answer_a_simple_search(service):
    agent = ShoppingAgent(service=service, customer_id="CUST-1001")
    result = agent.run("I want some ripe avocados.")
    assert result.text
    names = [call["name"] for call in result.tool_calls]
    assert "search_products" in names


@pytest.mark.agent
@pytest.mark.skip(reason="not yet implemented")
def test_tool_schemas_are_registered():
    assert len(TOOL_SCHEMAS) >= 3
    names = []
    for schema in TOOL_SCHEMAS:
        # Support both OpenAI function-wrapped and flat shapes.
        name = schema.get("name") or schema.get("function", {}).get("name")
        names.append(name)
    assert "search_products" in names
    assert "add_to_cart" in names


@pytest.mark.agent
@pytest.mark.skip(reason="not yet implemented")
def test_execute_search_tool(service):
    raw = execute_tool(
        "search_products",
        {"query": "avocado"},
        service=service,
        customer_id="CUST-1001",
    )
    assert "HB-1001" in raw


@pytest.mark.agent
@pytest.mark.skip(reason="not yet implemented")
def test_retriever_finds_delivery_policy(service):
    retriever = InMemoryRetriever(HashingEmbedder(), service=service).build()
    hits = retriever.retrieve("when is delivery free?", top_k=3, source="policy")
    assert hits
    assert any("50" in hit.chunk.text or "free" in hit.chunk.text.lower() for hit in hits)


@pytest.mark.agent
@pytest.mark.skip(reason="not yet implemented")
def test_mcp_server_builds():
    server = build_server(ShoppingService.default())
    assert server is not None
