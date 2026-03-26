"""Thin orchestrator shell for the cocoverify2 verification pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from cocoverify2.core.config import VerificationConfig
from cocoverify2.core.errors import PhaseNotImplementedError
from cocoverify2.core.models import VerificationReport
from cocoverify2.utils.logging import get_logger


class VerificationOrchestrator:
    """Coordinate stage execution without owning stage business logic."""

    def __init__(
        self,
        *,
        config: VerificationConfig | None = None,
        stages: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the orchestrator with optional dependency injection."""
        self.config = config or VerificationConfig()
        self.stages = stages or {}
        self.logger = get_logger(__name__, level=self.config.log_level)

    def verify(
        self,
        *,
        rtl: list[Path] | None = None,
        task_id: str = "",
        task_description: str = "",
        spec: Path | None = None,
        golden_tb: Path | None = None,
        out_dir: Path | None = None,
    ) -> VerificationReport:
        """Run the full verification pipeline.

        Phase 0 intentionally provides only the signature and dependency injection
        surface. Business logic is implemented in later phases.
        """
        _ = (rtl, task_id, task_description, spec, golden_tb, out_dir)
        raise PhaseNotImplementedError(
            "Phase 0 only defines the orchestrator shell; pipeline execution is not implemented yet."
        )
