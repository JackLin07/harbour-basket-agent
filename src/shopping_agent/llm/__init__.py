"""Provider-agnostic LLM client interface. Implementations are a weekend TODO."""

from shopping_agent.llm.client import LLMClient, LLMResponse, ToolCall, build_client

__all__ = ["LLMClient", "LLMResponse", "ToolCall", "build_client"]
