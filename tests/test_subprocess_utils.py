"""Subprocess utility regression tests for Phase 5 execution."""

from __future__ import annotations

import subprocess
from pathlib import Path

from cocoverify2.utils.subprocess import CommandExecutionResult, execute_command


def test_command_execution_result_normalizes_bytes_payloads() -> None:
    result = CommandExecutionResult(
        command=["fake"],
        cwd=".",
        stdout=b"partial bytes",
        stderr=b"error bytes",
        error_message=b"error bytes",
    )

    assert result.stdout == "partial bytes"
    assert result.stderr == "error bytes"
    assert result.error_message == "error bytes"


def test_execute_command_timeout_normalizes_bytes_stdout_stderr(monkeypatch, tmp_path: Path) -> None:
    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=["fake"],
            timeout=kwargs["timeout"],
            output=b"partial output",
            stderr=b"partial error",
        )

    monkeypatch.setattr("cocoverify2.utils.subprocess.subprocess.run", fake_run)
    result = execute_command(["fake"], cwd=tmp_path, timeout_seconds=1)

    assert result.timed_out is True
    assert result.error_type == "timeout"
    assert isinstance(result.stdout, str)
    assert isinstance(result.stderr, str)
    assert result.stdout == "partial output"
    assert result.stderr == "partial error"
