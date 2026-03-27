"""cocotb-tools based execution backend for Phase 5."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from cocoverify2.core.models import RenderMetadata, RunnerSelection, SimulationConfig
from cocoverify2.execution.runner_base import RunnerBase, RunnerContext
from cocoverify2.utils.subprocess import CommandExecutionResult, execute_command

_RUNNER_SCRIPT = r'''
import json
import sys
from pathlib import Path

payload = json.loads(sys.argv[1])
from cocotb_tools.runner import get_runner

runner = get_runner(payload["simulator"])
runner.build(
    verilog_sources=payload["rtl_sources"],
    includes=payload["include_dirs"],
    defines=payload["defines"],
    parameters=payload["parameters"],
    hdl_toplevel=payload["top_module"],
    clean=payload["clean_build"],
    waves=payload["waves_enabled"],
    always=True,
)
runner.test(
    hdl_toplevel=payload["top_module"],
    test_module=payload["test_module"],
    waves=payload["waves_enabled"],
    plusargs=payload["plusargs"],
    extra_env=payload["extra_env"],
    results_xml=payload["junit_path"],
)
'''


class CocotbRunner(RunnerBase):
    """Execute the rendered package through cocotb-tools when available."""

    backend_name = "cocotb_tools"

    def execute(
        self,
        *,
        metadata: RenderMetadata,
        config: SimulationConfig,
        selection: RunnerSelection,
        context: RunnerContext,
    ) -> CommandExecutionResult:
        """Run cocotb-tools via a small Python wrapper script."""
        rtl_sources = list(config.rtl_sources)
        if not rtl_sources:
            rtl_sources = [Path(path) for path in selection.resolved_rtl_sources]
        if not rtl_sources:
            return CommandExecutionResult(
                command=[],
                cwd=str(context.package_dir),
                return_code=None,
                error_type="configuration",
                error_message="No RTL sources were provided for cocotb-tools execution.",
                stderr="No RTL sources were provided for cocotb-tools execution.",
            )

        junit_path = context.junit_dir / "results.xml" if config.junit_enabled else None
        payload = {
            "simulator": config.simulator,
            "rtl_sources": [str(path) for path in rtl_sources],
            "include_dirs": [str(path) for path in config.include_dirs],
            "defines": dict(config.defines),
            "parameters": dict(config.parameters),
            "top_module": self.resolve_top_module(metadata, config),
            "test_module": _qualified_test_module(self.resolve_test_module(metadata, config)),
            "waves_enabled": config.waves_enabled or config.waves,
            "extra_env": dict(config.extra_env),
            "plusargs": list(config.plusargs),
            "junit_path": str(junit_path) if junit_path else None,
            "clean_build": config.clean_build,
        }
        command = [sys.executable, "-c", _RUNNER_SCRIPT, json.dumps(payload)]
        return execute_command(
            command,
            cwd=config.working_dir or context.render_dir,
            extra_env=config.extra_env,
            timeout_seconds=config.timeout_seconds,
        )


def _qualified_test_module(test_module: str) -> str:
    if "." in test_module:
        return test_module
    return f"cocotb_tests.{test_module}"
