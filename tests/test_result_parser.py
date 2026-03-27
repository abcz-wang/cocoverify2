"""Execution result parsing tests for Phase 5."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from cocoverify2.execution.result_parser import build_simulation_result, infer_execution_status, parse_junit_xml, parse_test_names_from_logs
from cocoverify2.utils.subprocess import CommandExecutionResult


def test_parse_junit_xml_extracts_pass_fail_skip(tmp_path: Path) -> None:
    junit_path = tmp_path / "results.xml"
    junit_path.write_text(
        """
<testsuite name="demo" tests="3" failures="1" skipped="1">
  <testcase classname="demo" name="test_pass" />
  <testcase classname="demo" name="test_fail"><failure>boom</failure></testcase>
  <testcase classname="demo" name="test_skip"><skipped /></testcase>
</testsuite>
""".strip(),
        encoding="utf-8",
    )

    summary = parse_junit_xml(junit_path)

    assert summary["discovered_tests"] == ["demo.test_pass", "demo.test_fail", "demo.test_skip"]
    assert summary["passed_tests"] == ["demo.test_pass"]
    assert summary["failed_tests"] == ["demo.test_fail"]
    assert summary["skipped_tests"] == ["demo.test_skip"]


def test_parse_test_names_from_logs_extracts_status_lines() -> None:
    summary = parse_test_names_from_logs(
        "test_alpha ... PASSED\n"
        "test_beta ... FAILED\n"
        "test_gamma ... SKIPPED\n"
    )

    assert summary["executed_tests"] == ["test_alpha", "test_beta", "test_gamma"]
    assert summary["passed_tests"] == ["test_alpha"]
    assert summary["failed_tests"] == ["test_beta"]
    assert summary["skipped_tests"] == ["test_gamma"]


def test_infer_execution_status_prefers_timeout_and_environment_errors() -> None:
    timeout_result = CommandExecutionResult(command=["fake"], cwd=".", timed_out=True)
    env_result = CommandExecutionResult(command=["fake"], cwd=".", error_type="missing_tool", stderr="make not found")
    compile_result = CommandExecutionResult(command=["fake"], cwd=".", return_code=1, stderr="syntax error near token")

    assert infer_execution_status(command_result=timeout_result, failed_tests=[]) == "timeout"
    assert infer_execution_status(command_result=env_result, failed_tests=[]) == "environment_error"
    assert infer_execution_status(command_result=compile_result, failed_tests=[]) == "compile_error"


def test_build_simulation_result_prefers_junit_counts_when_available(tmp_path: Path) -> None:
    junit_path = tmp_path / "results.xml"
    junit_path.write_text(
        """
<testsuite name="demo" tests="2" failures="1">
  <testcase classname="demo" name="test_pass" />
  <testcase classname="demo" name="test_fail"><failure>boom</failure></testcase>
</testsuite>
""".strip(),
        encoding="utf-8",
    )
    command_result = CommandExecutionResult(
        command=["fake"],
        cwd=str(tmp_path),
        return_code=1,
        stdout="test_pass ... PASSED\ntest_fail ... FAILED\n",
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        duration_seconds=0.1,
    )

    result = build_simulation_result(
        module_name="demo",
        based_on_render_metadata="render/metadata.json",
        selected_mode="make",
        selected_simulator="icarus",
        command_result=command_result,
        log_paths={"stdout": "run/logs/stdout.txt"},
        junit_path=junit_path,
        waveform_paths=[],
        runner_warnings=["demo warning"],
        execution_notes=["demo note"],
    )

    assert result.module_name == "demo"
    assert result.failed_tests == ["demo.test_fail"]
    assert result.passed_tests == ["demo.test_pass"]
    assert result.status == "runtime_error"
    assert result.runner_warnings == ["demo warning"]
