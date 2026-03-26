"""Oracle generation tests for Phase 3."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from cocoverify2.stages.contract_extractor import ContractExtractor
from cocoverify2.stages.oracle_generator import OracleGenerator
from cocoverify2.stages.test_plan_generator import TestPlanGenerator

_FIXTURES = Path(__file__).parent / "fixtures"
_RTL = _FIXTURES / "rtl"


def _build_phase3_inputs(tmp_path: Path, rtl_name: str) -> tuple[Path, Path]:
    stem = rtl_name.removesuffix(".v")
    artifact_root = tmp_path / stem
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
    return artifact_root / "contract" / "contract.json", artifact_root / "plan" / "test_plan.json"


def _collect_modes(oracle_payload: dict) -> set[str]:
    modes: set[str] = set()
    for key in ("protocol_oracles", "functional_oracles", "property_oracles"):
        for oracle_case in oracle_payload[key]:
            for check in oracle_case["checks"]:
                modes.add(check["temporal_window"]["mode"])
    return modes


def test_simple_comb_generates_functional_and_property_oracles(tmp_path: Path) -> None:
    contract_path, plan_path = _build_phase3_inputs(tmp_path, "simple_comb.v")
    oracle = OracleGenerator().run_from_artifacts(
        contract_path=contract_path,
        plan_path=plan_path,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
    )

    assert oracle.module_name == "simple_comb"
    assert len(oracle.functional_oracles) >= 2
    assert len(oracle.property_oracles) >= 2
    assert oracle.protocol_oracles == []
    assert all(check.temporal_window.mode != "exact_cycle" for case in oracle.functional_oracles for check in case.checks)
    assert all("reset" not in check.observed_signals for case in oracle.functional_oracles for check in case.checks)
    assert (tmp_path / "oracle" / "oracle.json").exists()
    assert (tmp_path / "oracle" / "oracle_summary.yaml").exists()

    payload = json.loads((tmp_path / "oracle" / "oracle.json").read_text(encoding="utf-8"))
    assert payload["module_name"] == "simple_comb"
    assert _collect_modes(payload) <= {"event_based", "bounded_range", "unbounded_safe"}


def test_simple_seq_generates_reset_safe_and_state_progress_oracles(tmp_path: Path) -> None:
    contract_path, plan_path = _build_phase3_inputs(tmp_path, "simple_seq.v")
    oracle = OracleGenerator().run_from_artifacts(
        contract_path=contract_path,
        plan_path=plan_path,
        task_description="Sequential register",
        spec_text="Observe reset before checking outputs.",
        out_dir=tmp_path,
    )

    assert oracle.protocol_oracles
    assert any(case.linked_plan_case_id == "reset_001" for case in oracle.protocol_oracles)
    assert any(
        "eventually updates" in check.pass_condition.lower()
        for case in oracle.functional_oracles
        for check in case.checks
    )
    assert all(check.temporal_window.mode != "exact_cycle" for case in oracle.functional_oracles for check in case.checks)
    assert any("Task description was provided" in item for item in oracle.assumptions)
    assert any("Spec text was provided" in item for item in oracle.assumptions)


def test_valid_ready_generates_protocol_safe_oracles_without_fixed_latency(tmp_path: Path) -> None:
    contract_path, plan_path = _build_phase3_inputs(tmp_path, "valid_ready.v")
    oracle = OracleGenerator().run_from_artifacts(
        contract_path=contract_path,
        plan_path=plan_path,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
    )

    descriptions = [check.description.lower() for case in oracle.protocol_oracles for check in case.checks]
    pass_conditions = [check.pass_condition.lower() for case in oracle.protocol_oracles for check in case.checks]
    modes = {check.temporal_window.mode for case in oracle.protocol_oracles for check in case.checks}

    assert any("acceptance" in description for description in descriptions)
    assert any("ready is low" in description or "backpressure" in description for description in descriptions)
    assert any("persistence" in description or "waiting behavior" in description for description in descriptions)
    assert any("start event" in description or "completion" in description for description in descriptions)
    assert "exact_cycle" not in modes
    assert all("fixed later cycle" not in condition for condition in pass_conditions)
    assert all("exact completion cycle" not in condition for condition in pass_conditions)
    assert all("aclk" not in check.observed_signals and "aresetn" not in check.observed_signals for case in oracle.protocol_oracles for check in case.checks)


def test_legacy_non_ansi_generates_more_unresolved_and_weaker_functional_oracles(tmp_path: Path) -> None:
    simple_contract_path, simple_plan_path = _build_phase3_inputs(tmp_path / "simple_ref", "simple_comb.v")
    simple_oracle = OracleGenerator().run_from_artifacts(
        contract_path=simple_contract_path,
        plan_path=simple_plan_path,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path / "simple_ref",
    )

    legacy_contract_path, legacy_plan_path = _build_phase3_inputs(tmp_path / "legacy_ref", "legacy_non_ansi.v")
    legacy_oracle = OracleGenerator().run_from_artifacts(
        contract_path=legacy_contract_path,
        plan_path=legacy_plan_path,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path / "legacy_ref",
    )

    assert len(legacy_oracle.unresolved_items) > len(simple_oracle.unresolved_items)
    assert legacy_oracle.oracle_confidence.overall_confidence < simple_oracle.oracle_confidence.overall_confidence
    assert sum(len(case.checks) for case in legacy_oracle.functional_oracles) < sum(len(case.checks) for case in simple_oracle.functional_oracles)
    assert all(len(case.checks) == 0 for case in legacy_oracle.functional_oracles)


def test_stage_oracle_cli_smoke(tmp_path: Path) -> None:
    contract_path, plan_path = _build_phase3_inputs(tmp_path, "simple_comb.v")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cocoverify2.cli",
            "stage",
            "oracle",
            "--contract",
            str(contract_path),
            "--plan",
            str(plan_path),
            "--out-dir",
            str(tmp_path / "cli_oracle"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Oracle generated for module 'simple_comb'" in result.stdout
    assert (tmp_path / "cli_oracle" / "oracle" / "oracle.json").exists()
