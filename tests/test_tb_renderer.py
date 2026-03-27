"""Testbench rendering tests for Phase 4."""

from __future__ import annotations

import json
import py_compile
import subprocess
import sys
from pathlib import Path

from cocoverify2.stages.contract_extractor import ContractExtractor
from cocoverify2.stages.oracle_generator import OracleGenerator
from cocoverify2.stages.tb_renderer import TBRenderer
from cocoverify2.stages.test_plan_generator import TestPlanGenerator

_FIXTURES = Path(__file__).parent / "fixtures"
_RTL = _FIXTURES / "rtl"


def _build_phase4_inputs(tmp_path: Path, rtl_name: str) -> tuple[Path, Path, Path]:
    stem = rtl_name.removesuffix(".v")
    artifact_root = tmp_path / f"artifacts_{stem}"
    contract = ContractExtractor().run(
        rtl_paths=[_RTL / rtl_name],
        task_description=None,
        spec_text=None,
        golden_interface_text=None,
        out_dir=artifact_root,
    )
    TestPlanGenerator().run(
        contract=contract,
        task_description=None,
        spec_text=None,
        out_dir=artifact_root,
        based_on_contract=str(artifact_root / "contract" / "contract.json"),
    )
    OracleGenerator().run_from_artifacts(
        contract_path=artifact_root / "contract" / "contract.json",
        plan_path=artifact_root / "plan" / "test_plan.json",
        task_description=None,
        spec_text=None,
        out_dir=artifact_root,
    )
    return (
        artifact_root / "contract" / "contract.json",
        artifact_root / "plan" / "test_plan.json",
        artifact_root / "oracle" / "oracle.json",
    )


def _render_fixture(tmp_path: Path, rtl_name: str):
    contract_path, plan_path, oracle_path = _build_phase4_inputs(tmp_path, rtl_name)
    render_root = tmp_path / f"render_{rtl_name.removesuffix('.v')}"
    metadata = TBRenderer().run_from_artifacts(
        contract_path=contract_path,
        plan_path=plan_path,
        oracle_path=oracle_path,
        task_description=None,
        spec_text=None,
        out_dir=render_root,
    )
    package_dir = render_root / "render" / "cocotb_tests"
    return metadata, render_root, package_dir


def _compile_generated_python(package_dir: Path) -> None:
    for path in package_dir.glob("*.py"):
        py_compile.compile(str(path), doraise=True)


def test_simple_comb_renders_basic_and_edge_without_protocol_file(tmp_path: Path) -> None:
    metadata, render_root, package_dir = _render_fixture(tmp_path, "simple_comb.v")

    assert (package_dir / "test_simple_comb_basic.py").exists()
    assert (package_dir / "test_simple_comb_edge.py").exists()
    assert not (package_dir / "test_simple_comb_protocol.py").exists()
    assert (package_dir / "simple_comb_interface.py").exists()
    assert metadata.interface_summary["clock_signals"] == []
    assert metadata.interface_summary["reset_signals"] == []
    assert "clk" not in metadata.interface_summary["business_inputs"]
    assert "rst" not in metadata.interface_summary["business_inputs"]
    payload = json.loads((render_root / "render" / "metadata.json").read_text(encoding="utf-8"))
    assert set(payload["test_modules"]) == {"test_simple_comb_basic", "test_simple_comb_edge"}
    _compile_generated_python(package_dir)


def test_simple_seq_renders_reset_helpers_without_exact_cycle_default(tmp_path: Path) -> None:
    metadata, _, package_dir = _render_fixture(tmp_path, "simple_seq.v")

    env_text = (package_dir / "simple_seq_env.py").read_text(encoding="utf-8")
    oracle_text = (package_dir / "simple_seq_oracle.py").read_text(encoding="utf-8")
    assert (package_dir / "test_simple_seq_basic.py").exists()
    assert "apply_reset_if_available" in env_text
    assert metadata.env_summary["has_reset_helper"] is True
    assert "wait_exact_cycle" not in env_text
    assert '"exact_cycle"' not in oracle_text
    _compile_generated_python(package_dir)


def test_valid_ready_renders_protocol_safe_modules_without_fixed_latency(tmp_path: Path) -> None:
    metadata, _, package_dir = _render_fixture(tmp_path, "valid_ready.v")

    protocol_text = (package_dir / "test_valid_ready_protocol.py").read_text(encoding="utf-8")
    oracle_text = (package_dir / "valid_ready_oracle.py").read_text(encoding="utf-8")
    interface_text = (package_dir / "valid_ready_interface.py").read_text(encoding="utf-8")

    assert (package_dir / "test_valid_ready_protocol.py").exists()
    assert "acceptance" in protocol_text.lower()
    assert "backpressure" in protocol_text.lower()
    assert "persistence" in protocol_text.lower() or "waiting" in protocol_text.lower()
    assert "ClockCycles(" not in protocol_text
    assert "wait_exact_cycle" not in protocol_text
    assert '"exact_cycle"' not in oracle_text
    assert metadata.interface_summary["protocol_signal_names"]
    assert "aclk" not in metadata.interface_summary["business_inputs"]
    assert "aresetn" not in metadata.interface_summary["business_outputs"]
    assert "BUSINESS_INPUTS" in interface_text
    _compile_generated_python(package_dir)


def test_legacy_non_ansi_renders_conservatively_and_keeps_unresolved_notes(tmp_path: Path) -> None:
    metadata, _, package_dir = _render_fixture(tmp_path, "legacy_non_ansi.v")

    interface_text = (package_dir / "legacy_non_ansi_interface.py").read_text(encoding="utf-8")
    basic_text = (package_dir / "test_legacy_non_ansi_basic.py").read_text(encoding="utf-8")

    assert metadata.render_warnings
    assert any("confidence is low" in item.lower() or "conservative" in item.lower() for item in metadata.render_warnings)
    assert metadata.oracle_summary["empty_functional_cases"]
    assert metadata.interface_summary["unknown_direction_signals"]
    assert "UNKNOWN_DIRECTION_SIGNALS" in interface_text
    assert "Conservative rendering" in basic_text
    assert metadata.render_confidence <= 0.35
    _compile_generated_python(package_dir)


def test_render_stage_writes_metadata_and_makefile(tmp_path: Path) -> None:
    metadata, render_root, package_dir = _render_fixture(tmp_path, "simple_seq.v")

    assert metadata.module_name == "simple_seq"
    assert (render_root / "render" / "metadata.json").exists()
    assert (package_dir / "Makefile").exists()
    makefile_text = (package_dir / "Makefile").read_text(encoding="utf-8")
    assert "TOPLEVEL ?= simple_seq" in makefile_text
    assert "Phase 5" in makefile_text


def test_stage_render_cli_smoke(tmp_path: Path) -> None:
    contract_path, plan_path, oracle_path = _build_phase4_inputs(tmp_path, "simple_comb.v")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cocoverify2.cli",
            "stage",
            "render",
            "--contract",
            str(contract_path),
            "--plan",
            str(plan_path),
            "--oracle",
            str(oracle_path),
            "--out-dir",
            str(tmp_path / "cli_render"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Render package generated for module 'simple_comb'" in result.stdout
    assert (tmp_path / "cli_render" / "render" / "metadata.json").exists()
