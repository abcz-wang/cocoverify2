"""Structured exceptions for cocoverify2."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cocoverify2.core.types import StageName


class CocoverifyError(Exception):
    """Base exception for framework-level failures."""


@dataclass(slots=True)
class StageExecutionError(CocoverifyError):
    """Error raised when a specific stage fails to execute."""

    stage: StageName
    message: str
    evidence: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"[{self.stage.value}] {self.message}"


@dataclass(slots=True)
class ParserError(CocoverifyError):
    """Structured parser failure with optional path and source snippet."""

    parser_name: str
    message: str
    path: Path | None = None
    snippet: str | None = None

    def __str__(self) -> str:
        location = f" ({self.path})" if self.path is not None else ""
        return f"[{self.parser_name}]{location} {self.message}"


class ConfigurationError(CocoverifyError):
    """Raised when runtime configuration is invalid."""


class ArtifactError(CocoverifyError):
    """Raised when required artifacts are missing or malformed."""


class PhaseNotImplementedError(CocoverifyError, NotImplementedError):
    """Raised for placeholders that are intentionally unimplemented."""
