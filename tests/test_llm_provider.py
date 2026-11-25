"""Provider selection for OpenAI vs xAI. No network calls."""

from __future__ import annotations

import pytest

from shopping_agent.config import (
    DEFAULT_OPENAI_MODEL,
    DEFAULT_XAI_JUDGE_MODEL,
    DEFAULT_XAI_MODEL,
    XAI_API_BASE_URL,
    Settings,
)
from shopping_agent.llm.client import get_provider_endpoint


def test_openai_defaults():
    settings = Settings(llm_provider="openai", openai_api_key="sk-test")
    endpoint = get_provider_endpoint(settings)
    assert endpoint.provider == "openai"
    assert endpoint.api_key == "sk-test"
    assert endpoint.base_url is None
    assert endpoint.model == DEFAULT_OPENAI_MODEL
    assert endpoint.judge_model == DEFAULT_OPENAI_MODEL
    assert settings.has_llm_credentials is True


def test_openai_without_key_is_unconfigured():
    settings = Settings(llm_provider="openai", openai_api_key=None)
    endpoint = get_provider_endpoint(settings)
    assert endpoint.api_key is None
    assert settings.has_llm_credentials is False


def test_xai_defaults():
    settings = Settings(llm_provider="xai", xai_api_key="xai-test")
    endpoint = get_provider_endpoint(settings)
    assert endpoint.provider == "xai"
    assert endpoint.api_key == "xai-test"
    assert endpoint.base_url == XAI_API_BASE_URL
    assert endpoint.base_url == "https://api.x.ai/v1"
    assert endpoint.model == DEFAULT_XAI_MODEL
    assert endpoint.model == "grok-4.20-non-reasoning"
    assert endpoint.judge_model == DEFAULT_XAI_JUDGE_MODEL
    assert endpoint.judge_model == "grok-4.7"
    assert settings.has_llm_credentials is True


def test_xai_without_key_is_unconfigured():
    settings = Settings(llm_provider="xai", xai_api_key=None)
    endpoint = get_provider_endpoint(settings)
    assert endpoint.api_key is None
    assert endpoint.base_url == "https://api.x.ai/v1"
    assert settings.has_llm_credentials is False


def test_llm_model_and_judge_model_overrides():
    settings = Settings(
        llm_provider="xai",
        xai_api_key="xai-test",
        llm_model="grok-4.3",
        judge_model="grok-4.6",
    )
    endpoint = get_provider_endpoint(settings)
    assert endpoint.model == "grok-4.3"
    assert endpoint.judge_model == "grok-4.6"


def test_eval_judge_model_used_when_judge_model_unset():
    settings = Settings(
        llm_provider="xai",
        xai_api_key="xai-test",
        eval_judge_model="grok-4.5",
    )
    assert get_provider_endpoint(settings).judge_model == "grok-4.5"


def test_provider_name_is_case_insensitive():
    settings = Settings(llm_provider="XAI", xai_api_key="xai-test")
    assert settings.normalized_provider == "xai"
    assert get_provider_endpoint(settings).provider == "xai"


def test_openai_compatible_helper_rejects_other_providers():
    with pytest.raises(ValueError, match="openai, xai"):
        get_provider_endpoint(Settings(llm_provider="anthropic", anthropic_api_key="ak-test"))


def test_env_selects_xai_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "xai")
    monkeypatch.setenv("XAI_API_KEY", "xai-from-env")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("JUDGE_MODEL", raising=False)
    monkeypatch.delenv("EVAL_JUDGE_MODEL", raising=False)
    settings = Settings()
    endpoint = get_provider_endpoint(settings)
    assert endpoint.provider == "xai"
    assert endpoint.api_key == "xai-from-env"
    assert endpoint.base_url == "https://api.x.ai/v1"
    assert endpoint.model == "grok-4.20-non-reasoning"
    assert endpoint.judge_model == "grok-4.7"


def test_env_model_overrides(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "xai")
    monkeypatch.setenv("XAI_API_KEY", "xai-from-env")
    monkeypatch.setenv("LLM_MODEL", "grok-4.3")
    monkeypatch.setenv("JUDGE_MODEL", "grok-4.7")
    settings = Settings()
    endpoint = get_provider_endpoint(settings)
    assert endpoint.model == "grok-4.3"
    assert endpoint.judge_model == "grok-4.7"
