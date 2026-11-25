"""LLM client wrapper interface.

TODO (weekend): implement one real provider, then keep this interface so swapping
OpenAI / Azure OpenAI / Anthropic is a factory change, not an agent-loop change.

Official docs:
- OpenAI tool use: https://developers.openai.com/api/docs/guides/function-calling
- Anthropic tool use: https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/overview
- OpenAI embeddings: https://developers.openai.com/api/docs/guides/embeddings
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from shopping_agent.config import Settings, get_settings


@dataclass
class ToolCall:
    """A single tool/function call requested by the model."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Normalised result of one model turn."""

    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    raw: Any = None
    usage: dict[str, int] = field(default_factory=dict)

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)


@runtime_checkable
class LLMClient(Protocol):
    """Minimal chat interface the agent loop should depend on."""

    def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = "auto",
        temperature: float = 0.2,
    ) -> LLMResponse:
        """Send a chat-style request and return a normalised response.

        `messages` should already be in a provider-neutral shape, for example:
        ``{"role": "system"|"user"|"assistant"|"tool", "content": "...", "tool_call_id": "..."}``.
        Translate to the provider's schema inside the implementation.
        """
        ...


class UnconfiguredLLMClient:
    """Placeholder so the rest of the scaffolding imports cleanly without a key."""

    def complete(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str | dict[str, Any] | None = "auto",
        temperature: float = 0.2,
    ) -> LLMResponse:
        raise NotImplementedError(
            "No LLM provider is configured. Copy .env.example to .env, add an API key, "
            "and implement OpenAILLMClient / AzureOpenAILLMClient / AnthropicLLMClient "
            "in shopping_agent/llm/client.py. See the TODO block below and WEEKEND_PLAN.md."
        )


# ---------------------------------------------------------------------------
# TODO (weekend): implement one of these and return it from build_client().
#
# class OpenAILLMClient:
#     def __init__(self, settings: Settings) -> None:
#         from openai import OpenAI
#         self._client = OpenAI(api_key=settings.openai_api_key)
#         self._model = settings.openai_model
#     def complete(...) -> LLMResponse:
#         # Map tools to the Responses or Chat Completions "tools" parameter.
#         # If the model returns function/tool calls, parse name + JSON arguments
#         # into ToolCall objects. If it returns text, set response.text.
#         ...
#
# class AzureOpenAILLMClient:
#     # Use the official Azure OpenAI client with endpoint + deployment.
#     # This is the stack mentioned in the Coles AI Engineer listing (AI Foundry).
#     ...
#
# class AnthropicLLMClient:
#     # tools=[{ "name", "description", "input_schema" }]
#     # Look for content blocks with type == "tool_use".
#     ...
# ---------------------------------------------------------------------------


def build_client(settings: Settings | None = None) -> LLMClient:
    """Factory. Returns a real client once you implement one; otherwise a stub."""
    settings = settings or get_settings()
    # TODO: if settings.llm_provider == "openai" and settings.openai_api_key:
    #     return OpenAILLMClient(settings)
    # TODO: if settings.llm_provider == "azure" and settings.has_llm_credentials:
    #     return AzureOpenAILLMClient(settings)
    # TODO: if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
    #     return AnthropicLLMClient(settings)
    _ = settings  # reserved for the implementation above
    return UnconfiguredLLMClient()
