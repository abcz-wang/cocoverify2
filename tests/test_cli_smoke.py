"""CLI smoke tests for cocoverify2."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
import os

from cocoverify2.core.models import DUTContract, FinalVerdict, VerificationReport
from cocoverify2.core.types import VerdictKind
import cocoverify2.cli as cli


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


def test_verify_command_invokes_orchestrator(monkeypatch, tmp_path: Path) -> None:
    calls: dict[str, object] = {}

    class FakeOrchestrator:
        def __init__(self, *, config) -> None:  # type: ignore[no-untyped-def]
            calls["config"] = config

        def verify(self, **kwargs):  # type: ignore[no-untyped-def]
            calls["kwargs"] = kwargs
            return VerificationReport(
                contract=DUTContract(module_name="demo"),
                final_verdict=FinalVerdict(verdict=VerdictKind.PASS),
            )

    monkeypatch.setattr(cli, "VerificationOrchestrator", FakeOrchestrator)

    rc = cli.main(["verify", "--rtl", str(tmp_path / "demo.v"), "--out-dir", str(tmp_path / "out")])

    assert rc == 0
    assert calls["kwargs"]["max_repair_rounds"] == 1
    assert calls["kwargs"]["out_dir"] == tmp_path / "out"


def test_repair_command_invokes_repair_stage(monkeypatch, tmp_path: Path) -> None:
    calls: dict[str, object] = {}

    class FakeRepairPlannerStage:
        def run_from_dir(self, *, in_dir, out_dir):  # type: ignore[no-untyped-def]
            calls["in_dir"] = in_dir
            calls["out_dir"] = out_dir
            return []

    monkeypatch.setattr(cli, "RepairPlannerStage", FakeRepairPlannerStage)

    rc = cli.main(["repair", "--in-dir", str(tmp_path), "--out-dir", str(tmp_path / "out")])

    assert rc == 0
    assert calls["in_dir"] == tmp_path
    assert calls["out_dir"] == tmp_path / "out"
