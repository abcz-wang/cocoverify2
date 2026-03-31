"""Configuration models for cocoverify2."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from cocoverify2.core.types import StageName


class LLMConfig(BaseModel):
    """Runtime configuration for the LLM client."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(default_factory=lambda: os.getenv("COCOVERIFY_LLM_PROVIDER", "openai"))
    model: str = Field(default_factory=lambda: os.getenv("COCOVERIFY_LLM_MODEL", "oss"))
    base_url: str | None = Field(
        default_factory=lambda: os.getenv("COCOVERIFY_LLM_BASE_URL", "http://10.200.108.4:8001/v1")
    )
    api_key: str = Field(default_factory=lambda: os.getenv("COCOVERIFY_LLM_API_KEY", "token-abc123"))
    temperature: float = Field(default_factory=lambda: float(os.getenv("COCOVERIFY_LLM_TEMPERATURE", "0.0")))
    timeout_seconds: int = Field(default_factory=lambda: int(os.getenv("COCOVERIFY_LLM_TIMEOUT_SECONDS", "60")), ge=1)
    plan_timeout_seconds: int | None = Field(
        default_factory=lambda: _env_int_optional("COCOVERIFY_PLAN_LLM_TIMEOUT_SECONDS"),
    )
    max_retries: int = Field(default_factory=lambda: int(os.getenv("COCOVERIFY_LLM_MAX_RETRIES", "2")), ge=0)
    trust_env: bool = Field(default_factory=lambda: _env_bool("COCOVERIFY_LLM_TRUST_ENV", False))
    disable_proxies: bool = Field(default_factory=lambda: _env_bool("COCOVERIFY_LLM_DISABLE_PROXIES", False))


class ArtifactConfig(BaseModel):
    """Controls artifact output locations and retention behavior."""

    model_config = ConfigDict(extra="forbid")

    out_dir: Path = Field(default=Path("out"))
    keep_intermediate: bool = Field(default=True)
    dump_json_indent: int = Field(default=2)


class VerificationConfig(BaseModel):
    """Top-level framework configuration for orchestration."""

    model_config = ConfigDict(extra="forbid")

    llm: LLMConfig = Field(default_factory=LLMConfig)
    artifacts: ArtifactConfig = Field(default_factory=ArtifactConfig)
    enabled_stages: list[StageName] = Field(
        default_factory=lambda: [
            StageName.CONTRACT,
            StageName.PLAN,
            StageName.ORACLE,
            StageName.RENDER,
            StageName.FILL,
            StageName.RUN,
            StageName.TRIAGE,
            StageName.REPAIR,
            StageName.REPORT,
        ]
    )
    max_repair_rounds: int = Field(default=1, ge=0)
    log_level: str = Field(default="INFO")


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int_optional(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return None
    return int(raw)
