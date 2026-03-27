"""Makefile-based execution backend for Phase 5."""

from __future__ import annotations

from pathlib import Path

from cocoverify2.cocotbgen.makefile import MAKEFILE_CONTRACT_MARKER
from cocoverify2.core.models import RenderMetadata, RunnerSelection, SimulationConfig
from cocoverify2.execution.runner_base import RunnerBase, RunnerContext
from cocoverify2.utils.subprocess import CommandExecutionResult, execute_command


class MakeRunner(RunnerBase):
    """Execute the rendered Makefile shell with explicit environment injection."""

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
        if not _makefile_has_execution_contract(makefile_path):
            return CommandExecutionResult(
                command=[],
                cwd=str(context.package_dir),
                return_code=None,
                error_type="configuration",
                error_message="Rendered Makefile exists but does not satisfy the executable-shell contract required by Phase 5.",
                stderr="Rendered Makefile exists but does not satisfy the executable-shell contract required by Phase 5.",
            )
        cocotb_makefiles_dir, preflight_error = _resolve_cocotb_makefiles_dir(context=context, config=config)
        if preflight_error is not None:
            return preflight_error

        rtl_sources = list(config.rtl_sources)
        if not rtl_sources:
            rtl_sources = [Path(path) for path in selection.resolved_rtl_sources]
        env = {
            "SIM": config.simulator,
            "TOPLEVEL": self.resolve_top_module(metadata, config),
            "MODULE": _qualified_test_module(self.resolve_test_module(metadata, config)),
            "COCOTB_MAKEFILES_DIR": str(cocotb_makefiles_dir),
            "VERILOG_SOURCES": " ".join(str(path) for path in rtl_sources),
            "INCLUDE_DIRS": " ".join(str(path) for path in config.include_dirs),
            "DEFINE_OVERRIDES": " ".join(_format_define_overrides(config.defines)),
            "PARAMETER_OVERRIDES": " ".join(_format_parameter_overrides(config.parameters)),
            "PLUSARGS": " ".join(config.plusargs),
            **config.extra_env,
        }
        if config.junit_enabled:
            env["COCOTB_RESULTS_FILE"] = str(context.junit_dir / "results.xml")
        if config.waves_enabled or config.waves:
            env["WAVES"] = "1"
        targets = list(config.make_targets) or []
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


def _format_define_overrides(defines: dict[str, str]) -> list[str]:
    items: list[str] = []
    for key, value in defines.items():
        items.append(f"{key}={value}" if value else key)
    return items


def _format_parameter_overrides(parameters: dict[str, object]) -> list[str]:
    return [f"{key}={value}" for key, value in parameters.items()]


def _makefile_has_execution_contract(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return (
        MAKEFILE_CONTRACT_MARKER in text
        and ".DEFAULT_GOAL := sim" in text
        and "COCOTB_MAKEFILES_DIR ?=" in text
        and "include $(COCOTB_MAKEFILES_DIR)/Makefile.sim" in text
    )


def _resolve_cocotb_makefiles_dir(
    *,
    context: RunnerContext,
    config: SimulationConfig,
) -> tuple[Path | None, CommandExecutionResult | None]:
    probe = execute_command(
        ["cocotb-config", "--makefiles"],
        cwd=config.working_dir or context.package_dir,
        extra_env=config.extra_env,
        timeout_seconds=config.timeout_seconds,
    )
    if probe.error_type == "missing_tool":
        message = (
            "Required tool 'cocotb-config' is unavailable; make-mode preflight could not resolve "
            "the cocotb makefiles directory."
        )
        return None, CommandExecutionResult(
            command=["cocotb-config", "--makefiles"],
            cwd=str(config.working_dir or context.package_dir),
            return_code=None,
            error_type="missing_tool",
            error_message=message,
            stderr=message,
            start_time=probe.start_time,
            end_time=probe.end_time,
            duration_seconds=probe.duration_seconds,
        )
    if probe.timed_out:
        message = "Timed out while probing 'cocotb-config --makefiles' during make-mode preflight."
        return None, CommandExecutionResult(
            command=["cocotb-config", "--makefiles"],
            cwd=str(config.working_dir or context.package_dir),
            return_code=None,
            error_type="timeout",
            error_message=message,
            stderr=message,
            timed_out=True,
            start_time=probe.start_time,
            end_time=probe.end_time,
            duration_seconds=probe.duration_seconds,
        )
    resolved = probe.stdout.strip()
    if probe.return_code not in (0, None) or not resolved:
        message = (
            "make-mode preflight failed to resolve the cocotb makefiles directory via "
            "'cocotb-config --makefiles'."
        )
        details = probe.stderr.strip() or probe.stdout.strip()
        if details:
            message = f"{message} Details: {details}"
        return None, CommandExecutionResult(
            command=["cocotb-config", "--makefiles"],
            cwd=str(config.working_dir or context.package_dir),
            return_code=probe.return_code,
            error_type="configuration",
            error_message=message,
            stderr=message,
            stdout=probe.stdout,
            start_time=probe.start_time,
            end_time=probe.end_time,
            duration_seconds=probe.duration_seconds,
        )
    path = Path(resolved)
    if not path.exists():
        message = (
            "make-mode preflight resolved a cocotb makefiles directory that does not exist: "
            f"{resolved}"
        )
        return None, CommandExecutionResult(
            command=["cocotb-config", "--makefiles"],
            cwd=str(config.working_dir or context.package_dir),
            return_code=probe.return_code,
            error_type="configuration",
            error_message=message,
            stderr=message,
            stdout=probe.stdout,
            start_time=probe.start_time,
            end_time=probe.end_time,
            duration_seconds=probe.duration_seconds,
        )
    return path, None
