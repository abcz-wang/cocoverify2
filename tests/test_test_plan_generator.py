"""Test plan generation tests for Phase 2."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from cocoverify2.core.config import LLMConfig
from cocoverify2.core.models import DUTContract, PortSpec, TimingSpec
from cocoverify2.core.types import GenerationMode, PortDirection, SequentialKind
from cocoverify2.stages.contract_extractor import ContractExtractor
from cocoverify2.stages.test_plan_generator import TestPlanGenerator

_FIXTURES = Path(__file__).parent / "fixtures"
_RTL = _FIXTURES / "rtl"
_SRC = Path(__file__).resolve().parents[1] / "src"


class _StaticLLMClient:
    def __init__(self, response: str) -> None:
        self.response = response

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        assert system_prompt
        assert user_prompt
        return self.response


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
    assert plan.plan_strategy == "rule_based_conservative"
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
    assert plan.plan_confidence <= 0.65
    assert plan.plan_strategy == "rule_based_conservative"
    assert {case.category for case in plan.cases} <= {"reset", "basic"}
    assert "basic" in {case.category for case in plan.cases}
    assert any("unresolved" in item.lower() or "incomplete" in item.lower() for item in plan.unresolved_items)
    basic_case = next(case for case in plan.cases if case.category == "basic")
    assert basic_case.stimulus_signals == ["data"]
    assert basic_case.execution_policy in {"deterministic", "deferred"}


def test_low_confidence_no_input_contract_avoids_executable_placeholder_cases(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="weak_demo",
        ports=[
            PortSpec(name="clk", direction=PortDirection.UNKNOWN, width=1),
            PortSpec(name="rst", direction=PortDirection.UNKNOWN, width=1),
            PortSpec(name="out", direction=PortDirection.UNKNOWN, width=4),
        ],
        timing=TimingSpec(sequential_kind=SequentialKind.UNKNOWN, latency_model="unknown", confidence=0.0),
        observable_outputs=[],
        ambiguities=["all directions unresolved", "timing unresolved", "no observable outputs"],
        contract_confidence=0.1,
    )

    plan = TestPlanGenerator().run(
        contract=contract,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
    )

    assert {case.category for case in plan.cases} == {"basic"}
    basic_case = plan.cases[0]
    assert basic_case.execution_policy == "deferred"
    assert basic_case.stimulus_signals == []
    assert not any("<no resolved inputs>" in item for item in basic_case.stimulus_intent)


def test_hybrid_plan_merges_llm_enrichment_and_additional_cases(tmp_path: Path) -> None:
    _, contract_path = _extract_contract(tmp_path, "simple_comb.v")
    llm_response = json.dumps(
        {
            "baseline_case_enrichments": [
                {
                    "case_id": "basic_001",
                    "stimulus_signals": ["a", "b"],
                    "semantic_tags": ["operation_specific"],
                    "scenario_kind": "single_operation",
                    "stimulus_program": [
                        {"action": "drive", "signals": {"a": 3, "b": 4}},
                        {"action": "wait_for_settle"}
                    ],
                    "notes": ["Exercise add/sub partitions conservatively."],
                }
            ],
            "additional_cases": [
                {
                    "case_id": "op_case_001",
                    "category": "basic",
                    "goal": "Exercise operation-specific combinations for arithmetic controls.",
                    "preconditions": [],
                    "stimulus_intent": ["Drive arithmetic opcode partitions while varying inputs."],
                    "stimulus_signals": ["a", "b", "unknown_signal"],
                    "expected_properties": ["Observe externally visible output partition changes."],
                    "observed_signals": ["y"],
                    "timing_assumptions": ["Observe after input stabilization."],
                    "dependencies": ["basic_001"],
                    "coverage_tags": ["basic", "operation_partition"],
                    "semantic_tags": ["operation_specific"],
                    "scenario_kind": "boundary_vector",
                    "stimulus_program": [
                        {"action": "drive", "signals": {"a": 0, "b": 1}},
                        {"action": "wait_for_settle"}
                    ],
                    "notes": ["Stay conservative when opcode semantics are partial."],
                    "priority": 2,
                }
            ],
            "assumptions": ["LLM added one operation-specific case."],
            "unresolved_items": ["Opcode naming remains partially heuristic."],
            "planning_notes": ["Do not overcommit to exact opcode semantics."],
        }
    )
    generator = TestPlanGenerator(llm_client=_StaticLLMClient(llm_response))
    plan = generator.run_from_artifact(
        contract_path=contract_path,
        task_description="simple comb demo",
        spec_text="Arithmetic behavior with representative controls.",
        out_dir=tmp_path,
        generation_mode=GenerationMode.HYBRID,
        llm_config=LLMConfig(),
    )

    categories = [case.category for case in plan.cases]
    assert plan.plan_strategy == "hybrid_rule_based_plus_llm"
    assert "basic" in categories
    assert "edge" in categories
    assert any(case.case_id == "basic_002" for case in plan.cases)
    basic_case = next(case for case in plan.cases if case.case_id == "basic_001")
    added_case = next(case for case in plan.cases if case.case_id == "basic_002")
    assert "operation_specific" in basic_case.semantic_tags
    assert basic_case.stimulus_signals == ["a", "b"]
    assert basic_case.scenario_kind == "single_operation"
    assert basic_case.stimulus_program
    assert added_case.stimulus_signals == ["a", "b"]
    assert added_case.scenario_kind == "boundary_vector"
    assert added_case.stimulus_program
    assert "LLM planning note: Do not overcommit to exact opcode semantics." in plan.assumptions
    assert (tmp_path / "plan" / "llm_request.json").exists()
    assert (tmp_path / "plan" / "llm_response_raw.txt").exists()
    assert (tmp_path / "plan" / "llm_response_parsed.json").exists()
    assert (tmp_path / "plan" / "llm_response_normalized.json").exists()
    assert (tmp_path / "plan" / "llm_merge_report.json").exists()
    merge_report = json.loads((tmp_path / "plan" / "llm_merge_report.json").read_text(encoding="utf-8"))
    assert merge_report["validation_report"]["normalization_report"]["renamed_fields"]


def test_hybrid_plan_falls_back_cleanly_on_invalid_llm_response(tmp_path: Path) -> None:
    _, contract_path = _extract_contract(tmp_path, "simple_comb.v")
    generator = TestPlanGenerator(llm_client=_StaticLLMClient("not json"))
    plan = generator.run_from_artifact(
        contract_path=contract_path,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        generation_mode=GenerationMode.HYBRID,
        llm_config=LLMConfig(),
    )

    assert plan.plan_strategy == "hybrid_rule_based_plus_llm"
    assert {case.category for case in plan.cases} >= {"basic", "edge"}
    assert any("fallback" in item.lower() for item in plan.assumptions)
    payload = json.loads((tmp_path / "plan" / "llm_merge_report.json").read_text(encoding="utf-8"))
    assert payload["status"] == "fallback"


def test_hybrid_plan_uses_normalized_payload_for_validation(tmp_path: Path) -> None:
    _, contract_path = _extract_contract(tmp_path, "simple_comb.v")
    llm_response = json.dumps(
        {
            "baseline_case_enrichments": [
                {
                    "case_id": "basic_001",
                    "stimulus_signals": ["a", "b"],
                    "preconditions": ["This extra field should be stripped by normalization."],
                    "notes": ["Keep this enrichment valid after normalization."],
                }
            ],
            "additional_cases": [],
            "assumptions": [],
            "unresolved_items": [],
            "planning_notes": [],
        }
    )
    generator = TestPlanGenerator(llm_client=_StaticLLMClient(llm_response))
    plan = generator.run_from_artifact(
        contract_path=contract_path,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        generation_mode=GenerationMode.HYBRID,
        llm_config=LLMConfig(),
    )

    assert plan.plan_strategy == "hybrid_rule_based_plus_llm"
    merge_report = json.loads((tmp_path / "plan" / "llm_merge_report.json").read_text(encoding="utf-8"))
    assert merge_report["status"] == "merged"
    stripped = merge_report["validation_report"]["normalization_report"]["stripped_fields"]
    assert any(item.get("field") == "preconditions" for item in stripped)


def test_seq_without_business_inputs_keeps_clock_driven_basic_case_deterministic(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="counter_like",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="q", direction=PortDirection.OUTPUT, width=8),
        ],
        observable_outputs=["q"],
        contract_confidence=0.75,
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
        clocks=[{"name": "clk", "source": "rtl_heuristic", "confidence": 0.9}],
        resets=[{"name": "rst_n", "active_level": 0, "source": "rtl_heuristic", "confidence": 0.9}],
    )
    plan = TestPlanGenerator().run(
        contract=contract,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path / "clock_only_plan",
    )

    basic_case = next(case for case in plan.cases if case.category == "basic")
    assert basic_case.execution_policy == "deterministic"
    assert basic_case.stimulus_signals == []


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
        env={
            **os.environ,
            "PYTHONPATH": str(_SRC) if not os.environ.get("PYTHONPATH") else f"{_SRC}{os.pathsep}{os.environ['PYTHONPATH']}",
        },
    )

    assert result.returncode == 0, result.stderr
    assert "Test plan generated for module 'simple_comb'" in result.stdout
    assert (tmp_path / "cli_plan" / "plan" / "test_plan.json").exists()
