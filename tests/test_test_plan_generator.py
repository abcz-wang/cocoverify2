"""Test plan generation tests for Phase 2."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from cocoverify2.core.config import LLMConfig
from cocoverify2.core.models import DUTContract, PortSpec, TestCasePlan, TestPlan, TimingSpec
from cocoverify2.core.types import GenerationMode, PortDirection, SequentialKind
from cocoverify2.llm.prompts import build_plan_user_prompt
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


def test_hybrid_plan_drops_nondeterministic_stimulus_placeholders(tmp_path: Path) -> None:
    _, contract_path = _extract_contract(tmp_path, "simple_comb.v")
    llm_response = json.dumps(
        {
            "baseline_case_enrichments": [
                {
                    "case_id": "basic_001",
                    "stimulus_signals": ["a", "b"],
                    "scenario_kind": "single_operation",
                    "stimulus_program": [
                        {"action": "drive", "signals": {"a": "rand64", "b": "0x4"}},
                        {"action": "record_inputs", "signals": {"a": "rand64", "y": 1, "b": "8'b00000101"}},
                    ],
                    "notes": ["Keep only deterministic literals."],
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

    basic_case = next(case for case in plan.cases if case.case_id == "basic_001")
    assert basic_case.stimulus_program == [
        {"action": "drive", "signals": {"b": 4}},
        {"action": "record_inputs", "signals": {"b": 5}},
    ]
    payload = json.loads((tmp_path / "plan" / "test_plan.json").read_text(encoding="utf-8"))
    assert "rand64" not in json.dumps(payload)
    merge_report = json.loads((tmp_path / "plan" / "llm_merge_report.json").read_text(encoding="utf-8"))
    warnings = merge_report["validation_report"]["signal_normalization_warnings"]
    assert any("stimulus_program_warnings" in item for item in warnings)


def test_hybrid_plan_repairs_misslotted_category_into_scenario_kind(tmp_path: Path) -> None:
    _, contract_path = _extract_contract(tmp_path, "simple_comb.v")
    llm_response = json.dumps(
        {
            "baseline_case_enrichments": [],
            "additional_cases": [
                {
                    "draft_id": "extra_001",
                    "category": "write_then_readback",
                    "goal": "Write then read back conservatively.",
                    "preconditions": [],
                    "stimulus_intent": ["Drive one value and observe a readback."],
                    "stimulus_signals": ["a", "b"],
                    "expected_properties": ["Observe external consistency only."],
                    "observed_signals": ["y"],
                    "timing_assumptions": [],
                    "dependencies": ["basic_001"],
                    "coverage_tags": ["functional"],
                    "semantic_tags": ["operation_specific"],
                    "notes": [],
                    "priority": 4,
                }
            ],
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

    added_case = next(case for case in plan.cases if case.case_id == "basic_002")
    assert added_case.category == "basic"
    assert added_case.scenario_kind == "write_then_readback"
    merge_report = json.loads((tmp_path / "plan" / "llm_merge_report.json").read_text(encoding="utf-8"))
    repairs = merge_report["validation_report"]["normalization_report"]["semantic_repairs"]
    assert any(item["repair"] == "moved_invalid_category_to_scenario_kind" for item in repairs)


def test_hybrid_plan_repairs_calendar_style_numeric_expression_json(tmp_path: Path) -> None:
    _, contract_path = _extract_contract(tmp_path, "simple_seq.v")
    llm_response = """
    {
      "baseline_case_enrichments": [
        {
          "case_id": "reset_001",
          "stimulus_program": [
            {"action": "wait_cycles", "cycles": (23 * 60 * 60) - 1,}
          ]
        }
      ],
      "additional_cases": [],
    }
    """
    generator = TestPlanGenerator(llm_client=_StaticLLMClient(llm_response))
    plan = generator.run_from_artifact(
        contract_path=contract_path,
        task_description=None,
        spec_text="calendar style reset sequencing",
        out_dir=tmp_path,
        generation_mode=GenerationMode.HYBRID,
        llm_config=LLMConfig(),
    )

    reset_case = next(case for case in plan.cases if case.case_id == "reset_001")
    assert reset_case.stimulus_program == [{"action": "wait_cycles", "cycles": 82799}]
    merge_report = json.loads((tmp_path / "plan" / "llm_merge_report.json").read_text(encoding="utf-8"))
    assert merge_report["status"] == "merged"
    assert merge_report["repaired_response_applied"] is True
    assert (tmp_path / "plan" / "llm_response_extracted.json.txt").exists()
    assert (tmp_path / "plan" / "llm_response_repaired.json.txt").exists()


def test_build_plan_user_prompt_uses_compact_context() -> None:
    plan = _demo_prompt_plan()
    contract = _demo_prompt_contract()

    payload = json.loads(
        build_plan_user_prompt(
            contract=contract,
            baseline_plan=plan,
            task_description="Demo task",
            spec_text="Spec text " * 1000,
        )
    )

    assert "baseline_plan" not in payload
    assert "baseline_plan_cases" in payload
    assert "baseline_plan_summary" in payload
    assert "coarse_category_enum" in payload["requirements"]
    assert len(payload["spec_text"]) <= 5014
    assert set(payload["baseline_plan_cases"][0].keys()) <= {
        "case_id",
        "category",
        "goal",
        "stimulus_signals",
        "observed_signals",
        "execution_policy",
        "scenario_kind",
        "settle_requirement",
        "timing_assumptions",
        "dependencies",
        "coverage_tags",
        "semantic_tags",
        "comparison_operands",
        "relation_kind",
        "expected_transition",
        "reference_domain",
    }


def test_accumulator_like_contract_generates_group_closure_cases(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="accu",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="data_in", direction=PortDirection.INPUT, width=8),
            PortSpec(name="valid_in", direction=PortDirection.INPUT, width=1),
            PortSpec(name="valid_out", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="data_out", direction=PortDirection.OUTPUT, width=10),
        ],
        observable_outputs=["valid_out", "data_out"],
        assumptions=["The valid_out signal is set to 1 when the data_out outputs 4 received data accumulation results."],
        contract_confidence=0.83,
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
        clocks=[{"name": "clk", "source": "rtl_heuristic", "confidence": 0.9}],
        resets=[{"name": "rst_n", "active_level": 0, "source": "rtl_heuristic", "confidence": 0.9}],
    )

    plan = TestPlanGenerator().run(
        contract=contract,
        task_description="Accumulate every 4 valid input bytes into one output group.",
        spec_text="Use valid_in gating; only accepted valid cycles count toward the four-sample accumulation window.",
        out_dir=tmp_path,
    )

    scenario_kinds = {case.scenario_kind for case in plan.cases}
    assert {"grouped_valid_closure", "gapped_valid_group", "reset_mid_progress", "multi_group_stream"} <= scenario_kinds

    closure_case = next(case for case in plan.cases if case.scenario_kind == "grouped_valid_closure")
    valid_drives = [
        step
        for step in closure_case.stimulus_program
        if step["action"] == "drive" and step["signals"].get("valid_in") == 1
    ]
    assert len(valid_drives) == 4
    assert closure_case.relation_kind == "grouped_valid_accumulation"
    assert closure_case.comparison_operands == ["data_in", "valid_in", "data_out", "valid_out"]
    assert closure_case.stimulus_program[-2] == {"action": "drive", "signals": {"valid_in": 0, "data_in": 4}}

    reset_case = next(case for case in plan.cases if case.scenario_kind == "reset_mid_progress")
    assert any(step["action"] == "drive" and "rst_n" in step["signals"] for step in reset_case.stimulus_program)


def test_accumulator_like_contract_with_noncanonical_roles_generates_group_closure_cases(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="stream_accumulator",
        ports=[
            PortSpec(name="clk_i", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_ni", direction=PortDirection.INPUT, width=1),
            PortSpec(name="sample_bus", direction=PortDirection.INPUT, width=8),
            PortSpec(name="accept_i", direction=PortDirection.INPUT, width=1),
            PortSpec(name="sum_total", direction=PortDirection.OUTPUT, width=10),
            PortSpec(name="sum_done", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["sum_total", "sum_done"],
        assumptions=["One output event occurs after four accepted samples have been accumulated."],
        contract_confidence=0.82,
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
        clocks=[{"name": "clk_i", "source": "rtl_heuristic", "confidence": 0.9}],
        resets=[{"name": "rst_ni", "active_level": 0, "source": "rtl_heuristic", "confidence": 0.9}],
    )

    plan = TestPlanGenerator().run(
        contract=contract,
        task_description="Accumulate every four accepted samples and emit one grouped sum output.",
        spec_text="After four valid input samples, assert a completion pulse and present the accumulated sum.",
        out_dir=tmp_path,
    )

    closure_case = next(case for case in plan.cases if case.scenario_kind == "grouped_valid_closure")
    valid_drives = [
        step
        for step in closure_case.stimulus_program
        if step["action"] == "drive" and step["signals"].get("accept_i") == 1
    ]

    assert len(valid_drives) == 4
    assert closure_case.comparison_operands == ["sample_bus", "accept_i", "sum_total", "sum_done"]
    assert closure_case.stimulus_program[-2] == {"action": "drive", "signals": {"accept_i": 0, "sample_bus": 4}}


def test_multiplier_like_start_done_design_does_not_get_grouped_accumulator_cases(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="iterative_multiplier",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="start", direction=PortDirection.INPUT, width=1),
            PortSpec(name="ain", direction=PortDirection.INPUT, width=16),
            PortSpec(name="bin", direction=PortDirection.INPUT, width=16),
            PortSpec(name="done", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="yout", direction=PortDirection.OUTPUT, width=32),
        ],
        observable_outputs=["done", "yout"],
        contract_confidence=0.82,
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
        clocks=[{"name": "clk", "source": "rtl_heuristic", "confidence": 0.9}],
        resets=[{"name": "rst_n", "active_level": 0, "source": "rtl_heuristic", "confidence": 0.9}],
    )

    plan = TestPlanGenerator().run(
        contract=contract,
        task_description="Start a 16-bit multiplication and assert done when the product is ready.",
        spec_text="Multiply ain by bin after start and present the product on yout when done is asserted.",
        out_dir=tmp_path / "multiplier_plan",
    )

    assert all(case.relation_kind != "grouped_valid_accumulation" for case in plan.cases)
    assert all(
        case.scenario_kind not in {"grouped_valid_closure", "gapped_valid_group", "reset_mid_progress", "multi_group_stream"}
        for case in plan.cases
    )


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


def _demo_prompt_contract() -> DUTContract:
    return DUTContract(
        module_name="prompt_demo",
        ports=[
            PortSpec(name="a", direction=PortDirection.INPUT, width=8),
            PortSpec(name="b", direction=PortDirection.INPUT, width=8),
            PortSpec(name="y", direction=PortDirection.OUTPUT, width=8),
        ],
        observable_outputs=["y"],
        contract_confidence=0.8,
        timing=TimingSpec(sequential_kind=SequentialKind.COMB, latency_model="fixed", confidence=0.9),
    )


def _demo_prompt_plan():
    return TestPlan(
        module_name="prompt_demo",
        based_on_contract="contract.json",
        plan_strategy="rule_based_conservative",
        cases=[
            TestCasePlan(
                case_id="basic_001",
                goal="Exercise a simple deterministic combination.",
                category="basic",
                stimulus_intent=["Drive a legal pattern."],
                stimulus_signals=["a", "b"],
                expected_properties=["Observe y."],
                observed_signals=["y"],
                timing_assumptions=["Allow combinational settle."],
                execution_policy="deterministic",
                scenario_kind="single_operation",
                coverage_tags=["basic"],
                semantic_tags=["operation_specific"],
                confidence=0.7,
                source="rule_based",
            )
        ],
        unresolved_items=["keep it compact"],
        assumptions=["compact baseline"],
        plan_confidence=0.7,
    )
