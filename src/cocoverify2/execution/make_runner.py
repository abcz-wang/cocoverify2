"""Makefile-based execution backend for Phase 5."""

from __future__ import annotations

from pathlib import Path

from cocoverify2.core.models import RenderMetadata, RunnerSelection, SimulationConfig
from cocoverify2.execution.runner_base import RunnerBase, RunnerContext
from cocoverify2.utils.subprocess import CommandExecutionResult, execute_command


class MakeRunner(RunnerBase):
    """Execute the rendered Makefile scaffold with explicit environment injection."""

    backend_name = "make"

    def execute(
        self,
        *,
        metadata: RenderMetadata,
        config: SimulationConfig,
        selection: RunnerSelection,
        context: RunnerContext,
    ) -> CommandExecutionResult:
        """Run `make` inside the rendered cocotb package directory."""
        makefile_path = context.package_dir / "Makefile"
        if not makefile_path.exists():
            return CommandExecutionResult(
                command=[],
                cwd=str(context.package_dir),
                return_code=None,
                error_type="configuration",
                error_message="Rendered Makefile is missing.",
                stderr="Rendered Makefile is missing.",
            )

        rtl_sources = list(config.rtl_sources)
        if not rtl_sources:
            rtl_sources = [Path(path) for path in selection.resolved_rtl_sources]
        env = {
            "SIM": config.simulator,
            "TOPLEVEL": self.resolve_top_module(metadata, config),
            "MODULE": _qualified_test_module(self.resolve_test_module(metadata, config)),
            "VERILOG_SOURCES": " ".join(str(path) for path in rtl_sources),
            "PLUSARGS": " ".join(config.plusargs),
            **config.extra_env,
        }
        if config.junit_enabled:
            env["COCOTB_RESULTS_FILE"] = str(context.junit_dir / "results.xml")
        if config.waves_enabled or config.waves:
            env["WAVES"] = "1"
        targets = list(config.make_targets) or ["all"]
        command = ["make", *targets]
        return execute_command(
            command,
            cwd=config.working_dir or context.package_dir,
            extra_env=env,
            timeout_seconds=config.timeout_seconds,
        )


def _qualified_test_module(test_module: str) -> str:
    if "." in test_module:
        return test_module
    return f"cocotb_tests.{test_module}"
