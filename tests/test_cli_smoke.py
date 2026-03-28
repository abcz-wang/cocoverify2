"""CLI smoke tests for cocoverify2."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import os


_SRC = Path(__file__).resolve().parents[1] / "src"


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cocoverify2.cli", *args],
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": str(_SRC) if not os.environ.get("PYTHONPATH") else f"{_SRC}{os.pathsep}{os.environ['PYTHONPATH']}",
        },
    )


def test_top_level_help() -> None:
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "verify" in result.stdout
    assert "stage" in result.stdout
    assert "repair" in result.stdout


def test_subcommand_help() -> None:
    for subcommand in ("verify", "stage", "repair"):
        result = _run_cli(subcommand, "--help")
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()


def test_stage_help_mentions_contract_inputs() -> None:
    result = _run_cli("stage", "contract", "--help")
    assert result.returncode == 0
    assert "--rtl" in result.stdout
    assert "--golden-interface" in result.stdout
    assert "--generation-mode" in result.stdout
    assert "--contract" in result.stdout
    assert "--plan" in result.stdout
    assert "--oracle" in result.stdout
    assert "--render" in result.stdout
    assert "--mode" in result.stdout
