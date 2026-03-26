"""Test plan generation tests for Phase 2."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from cocoverify2.stages.contract_extractor import ContractExtractor
from cocoverify2.stages.test_plan_generator import TestPlanGenerator

_FIXTURES = Path(__file__).parent / "fixtures"
_RTL = _FIXTURES / "rtl"


def _extract_contract(tmp_path: Path, rtl_name: str):
    out_dir = tmp_path / f"contract_{rtl_name.removesuffix('.v')}"
    contract = ContractExtractor().run(
        rtl_paths=[_RTL / rtl_name],
        task_description=None,
        spec_text=None,
        golden_interface_text=None,
        out_dir=out_dir,
    )
    return contract, out_dir / "contract" / "contract.json"


def test_simple_comb_contract_generates_basic_and_edge_plan(tmp_path: Path) -> None:
    contract, contract_path = _extract_contract(tmp_path, "simple_comb.v")
    plan = TestPlanGenerator().run_from_artifact(
        contract_path=contract_path,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
    )

    categories = {case.category for case in plan.cases}
    assert contract.timing.sequential_kind == "comb"
    assert categories >= {"basic", "edge"}
    assert plan.module_name == "simple_comb"
    assert plan.based_on_contract == str(contract_path)
    assert (tmp_path / "plan" / "test_plan.json").exists()
    assert (tmp_path / "plan" / "test_plan_summary.yaml").exists()

    payload = json.loads((tmp_path / "plan" / "test_plan.json").read_text(encoding="utf-8"))
    assert payload["module_name"] == "simple_comb"
    assert len(payload["cases"]) >= 2


def test_simple_seq_contract_generates_reset_and_basic_cases(tmp_path: Path) -> None:
    _, contract_path = _extract_contract(tmp_path, "simple_seq.v")
    plan = TestPlanGenerator().run_from_artifact(
        contract_path=contract_path,
        task_description="Sequential register",
        spec_text="Use reset before checking outputs.",
        out_dir=tmp_path,
    )

    categories = [case.category for case in plan.cases]
    assert "reset" in categories
    assert "basic" in categories
    assert plan.plan_strategy == "rule_based_seq_contract_first"
    assert any("Task description was provided" in item for item in plan.assumptions)
    assert any("Spec text was provided" in item for item in plan.assumptions)


def test_valid_ready_contract_generates_protocol_safe_cases_without_fixed_latency(tmp_path: Path) -> None:
    _, contract_path = _extract_contract(tmp_path, "valid_ready.v")
    plan = TestPlanGenerator().run_from_artifact(
        contract_path=contract_path,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
    )

    protocol_cases = [case for case in plan.cases if case.category == "protocol"]
    assert protocol_cases
    assert any("Timing model is unresolved" in item for item in plan.unresolved_items)
    assert {tag for case in protocol_cases for tag in case.coverage_tags} >= {"valid_ready", "start_done"}
    for case in protocol_cases:
        assert any(
            phrase in assumption
            for assumption in case.timing_assumptions
            for phrase in ("Do not assume fixed latency.", "Avoid fixed-cycle acceptance or completion checks")
        )
        assert not any("fixed latency of" in prop.lower() for prop in case.expected_properties)
        assert not any("exactly 1 cycle" in prop.lower() for prop in case.expected_properties)


def test_legacy_non_ansi_contract_generates_conservative_plan_with_unresolved_items(tmp_path: Path) -> None:
    _, contract_path = _extract_contract(tmp_path, "legacy_non_ansi.v")
    plan = TestPlanGenerator().run_from_artifact(
        contract_path=contract_path,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
    )

    assert plan.unresolved_items
    assert plan.plan_confidence <= 0.35
    assert plan.plan_strategy == "conservative_rule_based_from_contract_with_unresolved_safe_bias"
    assert {case.category for case in plan.cases} <= {"reset", "basic"}
    assert "basic" in {case.category for case in plan.cases}
    assert any("unresolved" in item.lower() or "incomplete" in item.lower() for item in plan.unresolved_items)


def test_stage_plan_cli_smoke(tmp_path: Path) -> None:
    _, contract_path = _extract_contract(tmp_path, "simple_comb.v")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cocoverify2.cli",
            "stage",
            "plan",
            "--contract",
            str(contract_path),
            "--out-dir",
            str(tmp_path / "cli_plan"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Test plan generated for module 'simple_comb'" in result.stdout
    assert (tmp_path / "cli_plan" / "plan" / "test_plan.json").exists()
