"""Runner abstraction for Phase 5 simulation execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from cocoverify2.core.models import RenderMetadata, RunnerSelection, SimulationConfig
from cocoverify2.utils.subprocess import CommandExecutionResult


@dataclass(slots=True)
class RunnerContext:
    """Filesystem context shared by execution backends."""

    render_metadata_path: Path
    render_dir: Path
    package_dir: Path
    run_dir: Path
    logs_dir: Path
    junit_dir: Path
    waves_dir: Path


class RunnerBase(ABC):
    """Abstract execution backend used by the simulation stage."""

    backend_name: str = "base"

    @abstractmethod
    def execute(
        self,
        *,
        metadata: RenderMetadata,
        config: SimulationConfig,
        selection: RunnerSelection,
        context: RunnerContext,
    ) -> CommandExecutionResult:
        """Execute one simulation command and return its structured subprocess result."""

    def resolve_top_module(self, metadata: RenderMetadata, config: SimulationConfig) -> str:
        """Resolve the HDL toplevel name for the runner invocation."""
        return config.top_module or config.toplevel or metadata.module_name

    def resolve_test_module(self, metadata: RenderMetadata, config: SimulationConfig) -> str:
        """Resolve the Python test module entry for the runner invocation."""
        if config.test_module:
            return config.test_module
        if metadata.test_modules:
            return metadata.test_modules[0]
        return f"test_{metadata.module_name}_basic"
