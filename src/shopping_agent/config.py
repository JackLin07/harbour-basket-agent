"""Runtime configuration, loaded from environment / optional .env file."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

# shopping_agent/config.py -> src/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data"

# OpenAI-compatible xAI (Grok) endpoint. See https://docs.x.ai/docs/overview
XAI_API_BASE_URL = "https://api.x.ai/v1"
# Cheap, fast default for the agent loop: same $1.25/$2.50 per 1M as grok-4.3,
# but the non-reasoning alias skips thinking tokens and is documented as the
# high-speed variant. Alias from https://docs.x.ai/developers/models/grok-4.20-non-reasoning
# (resolves to grok-4.20-0309-non-reasoning). Pricing: https://docs.x.ai/docs/models
DEFAULT_XAI_MODEL = "grok-4.20-non-reasoning"
# Stronger default for the LLM-as-judge. Flagship model on
# https://docs.x.ai/docs/models and https://docs.x.ai/developers/models/grok-4.7
DEFAULT_XAI_JUDGE_MODEL = "grok-4.7"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:  # pragma: no cover - dependency is declared, but be defensive
        return
    load_dotenv(REPO_ROOT / ".env")


_load_dotenv()


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    return value if value not in {"", None} else default


class Settings(BaseModel):
    """Provider-agnostic settings. Fill a .env from .env.example."""

    data_dir: Path = Field(default_factory=lambda: Path(_env("HARBOUR_BASKET_DATA_DIR", str(DEFAULT_DATA_DIR))))
    llm_provider: str = Field(default_factory=lambda: _env("LLM_PROVIDER", "openai") or "openai")
    openai_api_key: str | None = Field(default_factory=lambda: _env("OPENAI_API_KEY"))
    openai_model: str = Field(
        default_factory=lambda: _env("OPENAI_MODEL", DEFAULT_OPENAI_MODEL) or DEFAULT_OPENAI_MODEL
    )
    openai_embedding_model: str = Field(
        default_factory=lambda: _env("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small") or "text-embedding-3-small"
    )
    xai_api_key: str | None = Field(default_factory=lambda: _env("XAI_API_KEY"))
    azure_openai_api_key: str | None = Field(default_factory=lambda: _env("AZURE_OPENAI_API_KEY"))
    azure_openai_endpoint: str | None = Field(default_factory=lambda: _env("AZURE_OPENAI_ENDPOINT"))
    azure_openai_api_version: str = Field(
        default_factory=lambda: _env("AZURE_OPENAI_API_VERSION", "2024-10-21") or "2024-10-21"
    )
    azure_openai_deployment: str | None = Field(default_factory=lambda: _env("AZURE_OPENAI_DEPLOYMENT"))
    azure_openai_embedding_deployment: str | None = Field(
        default_factory=lambda: _env("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")
    )
    anthropic_api_key: str | None = Field(default_factory=lambda: _env("ANTHROPIC_API_KEY"))
    anthropic_model: str = Field(
        default_factory=lambda: _env("ANTHROPIC_MODEL", "claude-sonnet-4-5") or "claude-sonnet-4-5"
    )
    # Generic overrides used by OpenAI and xAI. LLM_MODEL / JUDGE_MODEL win over
    # provider-specific model env vars when set.
    llm_model: str | None = Field(default_factory=lambda: _env("LLM_MODEL"))
    judge_model: str | None = Field(default_factory=lambda: _env("JUDGE_MODEL"))
    embedding_provider: str = Field(
        default_factory=lambda: _env("EMBEDDING_PROVIDER", "sentence-transformers") or "sentence-transformers"
    )
    sentence_transformers_model: str = Field(
        default_factory=lambda: (
            _env("SENTENCE_TRANSFORMERS_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
            or "sentence-transformers/all-MiniLM-L6-v2"
        )
    )
    max_tool_iters: int = Field(default_factory=lambda: int(_env("MAX_TOOL_ITERS", "6") or "6"))
    eval_judge_model: str | None = Field(default_factory=lambda: _env("EVAL_JUDGE_MODEL"))
    trace_dir: Path = Field(
        default_factory=lambda: Path(_env("TRACE_DIR", "evals/results/traces") or "evals/results/traces")
    )
    default_customer_id: str = Field(default_factory=lambda: _env("DEFAULT_CUSTOMER_ID", "CUST-1001") or "CUST-1001")

    @property
    def normalized_provider(self) -> str:
        return self.llm_provider.strip().lower()

    def resolved_llm_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        provider = self.normalized_provider
        if provider == "xai":
            return DEFAULT_XAI_MODEL
        if provider == "anthropic":
            return self.anthropic_model
        if provider == "azure":
            return self.azure_openai_deployment or self.openai_model
        return self.openai_model

    def resolved_judge_model(self) -> str:
        if self.judge_model:
            return self.judge_model
        if self.eval_judge_model:
            return self.eval_judge_model
        if self.normalized_provider == "xai":
            return DEFAULT_XAI_JUDGE_MODEL
        return self.resolved_llm_model()

    @property
    def has_llm_credentials(self) -> bool:
        provider = self.normalized_provider
        if provider == "azure":
            return bool(self.azure_openai_api_key and self.azure_openai_endpoint and self.azure_openai_deployment)
        if provider == "anthropic":
            return bool(self.anthropic_api_key)
        if provider == "xai":
            return bool(self.xai_api_key)
        return bool(self.openai_api_key)


def get_settings() -> Settings:
    return Settings()
