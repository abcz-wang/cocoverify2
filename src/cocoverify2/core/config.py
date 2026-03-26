"""Configuration models for cocoverify2."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from cocoverify2.core.types import StageName


class LLMConfig(BaseModel):
    """Runtime configuration for the LLM client."""

    model_config = ConfigDict(extra="forbid")

    provider: str = Field(default="openai")
    model: str = Field(default="oss")
    base_url: str | None = Field(default=None)
    temperature: float = Field(default=0.0)


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
            StageName.RUN,
            StageName.TRIAGE,
            StageName.REPAIR,
            StageName.REPORT,
        ]
    )
    log_level: str = Field(default="INFO")
