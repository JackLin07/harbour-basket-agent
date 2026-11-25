"""Runtime configuration, loaded from environment / optional .env file."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

# shopping_agent/config.py -> src/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data"


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
    openai_model: str = Field(default_factory=lambda: _env("OPENAI_MODEL", "gpt-4.1-mini") or "gpt-4.1-mini")
    openai_embedding_model: str = Field(
        default_factory=lambda: _env("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small") or "text-embedding-3-small"
    )
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
    def has_llm_credentials(self) -> bool:
        if self.llm_provider == "azure":
            return bool(self.azure_openai_api_key and self.azure_openai_endpoint and self.azure_openai_deployment)
        if self.llm_provider == "anthropic":
            return bool(self.anthropic_api_key)
        return bool(self.openai_api_key)


def get_settings() -> Settings:
    return Settings()
