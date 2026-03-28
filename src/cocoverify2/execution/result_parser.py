"""Structured parsing helpers for simulation execution outputs."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

from cocoverify2.core.models import SimulationResult
from cocoverify2.core.types import ExecutionStatus, SimulationMode
from cocoverify2.utils.subprocess import CommandExecutionResult

_ELLIPSIS_STATUS_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z0-9_./:-]+)\s+\.\.\.\s+(?P<status>PASSED|FAILED|SKIPPED)$",
    re.IGNORECASE,
)

_PREFIX_STATUS_PATTERN = re.compile(
    r"^(?P<status>PASSED|FAILED|SKIPPED)\s+(?P<name>[A-Za-z0-9_./:-]+)$",
    re.IGNORECASE,
)


def build_simulation_result(
    *,
    module_name: str,
    based_on_render_metadata: str,
    selected_mode: SimulationMode,
    selected_simulator: str,
    command_result: CommandExecutionResult,
    log_paths: dict[str, str],
    junit_path: Path | None,
    waveform_paths: list[Path],
    runner_warnings: list[str],
    execution_notes: list[str],
) -> SimulationResult:
    """Build a structured ``SimulationResult`` from command outputs and optional JUnit."""
    junit_summary = parse_junit_xml(junit_path)
    log_summary = parse_test_names_from_logs("\n".join([command_result.stdout, command_result.stderr]))
    discovered_tests = junit_summary["discovered_tests"] or log_summary["discovered_tests"]
    executed_tests = junit_summary["executed_tests"] or log_summary["executed_tests"]
    passed_tests = junit_summary["passed_tests"] or log_summary["passed_tests"]
    failed_tests = junit_summary["failed_tests"] or log_summary["failed_tests"]
    skipped_tests = junit_summary["skipped_tests"] or log_summary["skipped_tests"]
    notes = list(execution_notes) + junit_summary["notes"] + log_summary["notes"]
    status = infer_execution_status(command_result=command_result, failed_tests=failed_tests)
    return SimulationResult(
        module_name=module_name,
        based_on_render_metadata=based_on_render_metadata,
        selected_mode=selected_mode,
        selected_simulator=selected_simulator,
        command=list(command_result.command),
        return_code=command_result.return_code,
        status=status,
        start_time=command_result.start_time.isoformat(),
        end_time=command_result.end_time.isoformat(),
        duration_seconds=command_result.duration_seconds,
        discovered_tests=discovered_tests,
        executed_tests=executed_tests,
        passed_tests=passed_tests,
        failed_tests=failed_tests,
        skipped_tests=skipped_tests,
        log_paths=dict(log_paths),
        junit_path=str(junit_path) if junit_path and junit_path.exists() else None,
        waveform_paths=[str(path) for path in waveform_paths if path.exists()],
        runner_warnings=list(runner_warnings),
        execution_notes=notes,
    )


def parse_junit_xml(path: Path | None) -> dict[str, list[str]]:
    """Parse a JUnit XML file into stable test-name buckets."""
    empty = {
        "discovered_tests": [],
        "executed_tests": [],
        "passed_tests": [],
        "failed_tests": [],
        "skipped_tests": [],
        "notes": [],
    }
    if path is None or not path.exists():
        return empty
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        empty["notes"].append(f"JUnit parse error: {exc}")
        return empty

    discovered: list[str] = []
    executed: list[str] = []
    passed: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []
    for testcase in root.iter("testcase"):
        name = _junit_test_name(testcase)
        discovered.append(name)
        executed.append(name)
        if testcase.find("failure") is not None or testcase.find("error") is not None:
            failed.append(name)
        elif testcase.find("skipped") is not None:
            skipped.append(name)
        else:
            passed.append(name)
    return {
        "discovered_tests": _deduped(discovered),
        "executed_tests": _deduped(executed),
        "passed_tests": _deduped(passed),
        "failed_tests": _deduped(failed),
        "skipped_tests": _deduped(skipped),
        "notes": [],
    }


def parse_test_names_from_logs(text: str) -> dict[str, list[str]]:
    """Best-effort test-name parsing from stdout/stderr text."""
    discovered: list[str] = []
    passed: list[str] = []
    failed: list[str] = []
    skipped: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        match = _ELLIPSIS_STATUS_PATTERN.match(line) or _PREFIX_STATUS_PATTERN.match(line)
        if match is None:
            continue
        name = match.group("name")
        status = match.group("status").lower()
        discovered.append(name)
        if status == "passed":
            passed.append(name)
        elif status == "failed":
            failed.append(name)
        else:
            skipped.append(name)
    executed = list(discovered)
    notes = []
    if not discovered and text.strip():
        notes.append("No explicit per-test results were found in logs; relying on return code and JUnit when available.")
    return {
        "discovered_tests": _deduped(discovered),
        "executed_tests": _deduped(executed),
        "passed_tests": _deduped(passed),
        "failed_tests": _deduped(failed),
        "skipped_tests": _deduped(skipped),
        "notes": notes,
    }


def infer_execution_status(
    *,
    command_result: CommandExecutionResult,
    failed_tests: list[str],
) -> ExecutionStatus:
    """Infer the coarse execution-layer status from command outputs."""
    if command_result.timed_out or command_result.error_type == "timeout":
        return ExecutionStatus.TIMEOUT
    if command_result.error_type in {"missing_tool", "configuration"}:
        return ExecutionStatus.ENVIRONMENT_ERROR

    haystack = "\n".join([command_result.stdout, command_result.stderr]).lower()
    if any(keyword in haystack for keyword in _INTERNAL_PACKAGE_IMPORT_KEYWORDS):
        return ExecutionStatus.RUNTIME_ERROR
    if any(keyword in haystack for keyword in _ENVIRONMENT_KEYWORDS):
        return ExecutionStatus.ENVIRONMENT_ERROR
    if any(keyword in haystack for keyword in _COMPILE_KEYWORDS):
        return ExecutionStatus.COMPILE_ERROR
    if any(keyword in haystack for keyword in _ELABORATION_KEYWORDS):
        return ExecutionStatus.ELABORATION_ERROR
    if failed_tests:
        return ExecutionStatus.RUNTIME_ERROR
    if command_result.return_code == 0:
        return ExecutionStatus.SUCCESS
    if command_result.return_code not in (None, 0):
        return ExecutionStatus.RUNTIME_ERROR
    return ExecutionStatus.UNKNOWN_FAILURE


_ENVIRONMENT_KEYWORDS = (
    "no module named",
    "modulenotfounderror",
    "command not found",
    "no such file or directory",
    "permission denied",
)

_INTERNAL_PACKAGE_IMPORT_KEYWORDS = (
    "no module named 'cocotb_tests'",
    'no module named "cocotb_tests"',
    "modulenotfounderror: no module named 'cocotb_tests'",
    'modulenotfounderror: no module named "cocotb_tests"',
)

_COMPILE_KEYWORDS = (
    "syntax error",
    "compile error",
    "parser error",
    "lexical error",
)

_ELABORATION_KEYWORDS = (
    "elaboration",
    "unable to bind",
    "unresolved module",
    "can't resolve",
    "cannot find top module",
)


def _junit_test_name(testcase: ET.Element) -> str:
    classname = testcase.attrib.get("classname", "")
    name = testcase.attrib.get("name", "unnamed_test")
    return f"{classname}.{name}" if classname else name


def _deduped(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items
