"""Thin subprocess helpers for the execution stage."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class CommandExecutionResult:
    """Captured result for one subprocess execution."""

    command: list[str]
    cwd: str
    env: dict[str, str] = field(default_factory=dict)
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    error_type: str | None = None
    error_message: str | None = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_seconds: float = 0.0


def execute_command(
    command: list[str],
    *,
    cwd: Path,
    extra_env: dict[str, str] | None = None,
    timeout_seconds: int,
) -> CommandExecutionResult:
    """Execute a command with timeout and structured error capture."""
    start_time = datetime.now(timezone.utc)
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        end_time = datetime.now(timezone.utc)
        return CommandExecutionResult(
            command=list(command),
            cwd=str(cwd),
            env=dict(extra_env or {}),
            return_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
        )
    except subprocess.TimeoutExpired as exc:
        end_time = datetime.now(timezone.utc)
        return CommandExecutionResult(
            command=list(command),
            cwd=str(cwd),
            env=dict(extra_env or {}),
            return_code=None,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            timed_out=True,
            error_type="timeout",
            error_message=str(exc),
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
        )
    except FileNotFoundError as exc:
        end_time = datetime.now(timezone.utc)
        return CommandExecutionResult(
            command=list(command),
            cwd=str(cwd),
            env=dict(extra_env or {}),
            return_code=None,
            stdout="",
            stderr=str(exc),
            error_type="missing_tool",
            error_message=str(exc),
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
        )
