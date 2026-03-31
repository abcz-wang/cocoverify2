"""Oracle generation tests for Phase 3."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from cocoverify2.core.config import LLMConfig
from cocoverify2.core.models import DUTContract, PortSpec, TestCasePlan as PlanCaseModel, TestPlan as PlanModel, TimingSpec
from cocoverify2.core.types import (
    AssertionStrength,
    DefinednessMode,
    GenerationMode,
    PortDirection,
    SequentialKind,
    TestCategory as PlanCategory,
)
from cocoverify2.stages.contract_extractor import ContractExtractor
from cocoverify2.stages.oracle_generator import OracleGenerator
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


def test_hybrid_oracle_appends_llm_checks_and_downgrades_exact_cycle(tmp_path: Path) -> None:
    contract_path, plan_path = _build_phase3_inputs(tmp_path, "valid_ready.v")
    llm_response = json.dumps(
        {
            "case_enrichments": [
                {
                    "linked_plan_case_id": "basic_001",
                    "oracle_class": "functional",
                    "checks": [
                        {
                            "check_type": "functional",
                            "check_id": "basic_001_functional_999",
                            "description": "Observe operation-specific output stability.",
                            "observed_signals": ["out_data", "done"],
                            "trigger_condition": "When the basic case drives legal input combinations.",
                            "pass_condition": "Output remains externally consistent across legal input partitions.",
                            "temporal_window": {
                                "mode": "exact_cycle",
                                "min_cycles": 0,
                                "max_cycles": 1,
                                "anchor": "input_stable",
                            },
                            "strictness": "strict",
                            "semantic_tags": ["operation_specific"],
                            "notes": ["Downgrade strict timing when confidence is weak."],
                            "confidence": 0.25,
                            "signal_policies": {"out_data": {"strength": "guarded"}},
                            "source": "rule_based",
                        }
                    ],
                    "assumptions": ["LLM functional enrichment"],
                    "unresolved_items": [],
                    "notes": ["Hybrid append-only oracle enrichment."],
                }
            ],
            "additional_oracle_cases": [],
            "assumptions": ["Oracle hybrid assumption"],
            "unresolved_items": ["Keep ambiguity when spec is partial."],
            "oracle_notes": ["Do not overfit to exact cycles."],
        }
    )
    generator = OracleGenerator(llm_client=_StaticLLMClient(llm_response))
    oracle = generator.run_from_artifacts(
        contract_path=contract_path,
        plan_path=plan_path,
        task_description=None,
        spec_text="Valid/ready datapath with unresolved timing.",
        out_dir=tmp_path,
        generation_mode=GenerationMode.HYBRID,
        llm_config=LLMConfig(),
    )

    assert oracle.oracle_strategy == "hybrid_rule_based_plus_llm"
    functional_case = next(case for case in oracle.functional_oracles if case.linked_plan_case_id == "basic_001")
    assert len(functional_case.checks) >= 1
    llm_check = functional_case.checks[-1]
    assert llm_check.semantic_tags == ["operation_specific"]
    assert llm_check.temporal_window.mode == "event_based"
    assert llm_check.strictness == "conservative"
    assert (tmp_path / "oracle" / "llm_request.json").exists()
    assert (tmp_path / "oracle" / "llm_response_raw.txt").exists()
    assert (tmp_path / "oracle" / "llm_response_parsed.json").exists()
    assert (tmp_path / "oracle" / "llm_response_normalized.json").exists()
    assert (tmp_path / "oracle" / "llm_merge_report.json").exists()
    merge_report = json.loads((tmp_path / "oracle" / "llm_merge_report.json").read_text(encoding="utf-8"))
    assert merge_report["validation_report"]["normalization_report"]["stripped_fields"]


def test_hybrid_oracle_falls_back_cleanly_on_invalid_llm_response(tmp_path: Path) -> None:
    contract_path, plan_path = _build_phase3_inputs(tmp_path, "simple_comb.v")
    generator = OracleGenerator(llm_client=_StaticLLMClient("not json"))
    oracle = generator.run_from_artifacts(
        contract_path=contract_path,
        plan_path=plan_path,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        generation_mode=GenerationMode.HYBRID,
        llm_config=LLMConfig(),
    )

    assert oracle.oracle_strategy == "hybrid_rule_based_plus_llm"
    assert any("fallback" in item.lower() for item in oracle.assumptions)
    payload = json.loads((tmp_path / "oracle" / "llm_merge_report.json").read_text(encoding="utf-8"))
    assert payload["status"] == "fallback"


def test_oracle_artifact_marks_weak_side_outputs_as_unresolved(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="demo_alu",
        ports=[
            PortSpec(name="a", direction=PortDirection.INPUT, width=32),
            PortSpec(name="b", direction=PortDirection.INPUT, width=32),
            PortSpec(name="aluc", direction=PortDirection.INPUT, width=6),
            PortSpec(name="r", direction=PortDirection.OUTPUT, width=32),
            PortSpec(name="zero", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="carry", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="negative", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="overflow", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="flag", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["r", "zero", "carry", "negative", "overflow", "flag"],
        timing=TimingSpec(sequential_kind=SequentialKind.COMB, latency_model="unknown", confidence=0.8),
        assumptions=[
            "The output result (r) is assigned to the lower 32 bits of the datapath result.",
            "The zero output is set to '1' when the result is all zeros, and '0' otherwise.",
            "The flag output is determined by the opcode and is set to '1' for SLT/SLTU and 'z' otherwise.",
            "carry means if there is a carry bit.",
            "negative means if the result is negative.",
            "overflow means if the computation is overflow.",
        ],
        contract_confidence=0.78,
    )
    plan = PlanModel(
        module_name="demo_alu",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.74,
        cases=[
            PlanCaseModel(
                case_id="basic_001",
                goal="Exercise legal ALU operations.",
                category=PlanCategory.BASIC,
                stimulus_intent=["Drive legal ALU operations."],
                stimulus_signals=["a", "b", "aluc"],
                expected_properties=["Outputs respond consistently to legal inputs."],
                observed_signals=["r", "zero", "carry", "negative", "overflow", "flag"],
                timing_assumptions=["Observe after input stabilization."],
                coverage_tags=["basic", "comb"],
                semantic_tags=["ambiguity_preserving"],
                confidence=0.74,
            )
        ],
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )

    functional_case = next(case for case in oracle.functional_oracles if case.linked_plan_case_id == "basic_001")
    check = functional_case.checks[0]

    assert check.signal_policies["r"].strength == AssertionStrength.EXACT
    assert check.signal_policies["zero"].strength == AssertionStrength.EXACT
    assert check.signal_policies["r"].definedness_mode == DefinednessMode.AT_OBSERVATION
    assert check.signal_policies["zero"].definedness_mode == DefinednessMode.AT_OBSERVATION
    assert check.signal_policies["flag"].strength == AssertionStrength.GUARDED
    assert check.signal_policies["flag"].allow_unknown is True
    assert check.signal_policies["flag"].allow_high_impedance is True
    assert check.signal_policies["flag"].definedness_mode == DefinednessMode.NOT_REQUIRED
    assert check.signal_policies["carry"].strength == AssertionStrength.UNRESOLVED
    assert check.signal_policies["negative"].strength == AssertionStrength.UNRESOLVED
    assert check.signal_policies["overflow"].strength == AssertionStrength.UNRESOLVED


def test_oracle_preserves_primary_output_ambiguity_for_control_heavy_edge_cases(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="demo_alu_edge",
        ports=[
            PortSpec(name="a", direction=PortDirection.INPUT, width=32),
            PortSpec(name="b", direction=PortDirection.INPUT, width=32),
            PortSpec(name="aluc", direction=PortDirection.INPUT, width=6),
            PortSpec(name="r", direction=PortDirection.OUTPUT, width=32),
            PortSpec(name="zero", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["r", "zero"],
        timing=TimingSpec(sequential_kind=SequentialKind.COMB, latency_model="unknown", confidence=0.8),
        contract_confidence=0.8,
    )
    plan = PlanModel(
        module_name="demo_alu_edge",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.8,
        cases=[
            PlanCaseModel(
                case_id="edge_001",
                goal="Probe edge patterns conservatively.",
                category=PlanCategory.EDGE,
                stimulus_intent=["Drive data boundaries while holding a control opcode."],
                stimulus_signals=["a", "b", "aluc"],
                expected_properties=["Observe externally visible response."],
                observed_signals=["r", "zero"],
                timing_assumptions=["Observe after input stabilization."],
                coverage_tags=["edge"],
                semantic_tags=["width_sensitive"],
                confidence=0.8,
            )
        ],
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )

    functional_case = next(case for case in oracle.functional_oracles if case.linked_plan_case_id == "edge_001")
    check = functional_case.checks[0]
    assert check.signal_policies["r"].strength == AssertionStrength.UNRESOLVED


def test_oracle_protocol_status_outputs_do_not_require_immediate_definedness(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="demo_protocol_status",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="start", direction=PortDirection.INPUT, width=1),
            PortSpec(name="done", direction=PortDirection.OUTPUT, width=1),
        ],
        handshake_signals=["start", "done"],
        observable_outputs=["done"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.82),
        contract_confidence=0.84,
    )
    plan = PlanModel(
        module_name="demo_protocol_status",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.8,
        cases=[
            PlanCaseModel(
                case_id="protocol_001",
                goal="Check that completion eventually becomes externally visible.",
                category=PlanCategory.PROTOCOL,
                stimulus_intent=["Assert start and observe done conservatively."],
                stimulus_signals=["start"],
                expected_properties=["Completion remains externally visible when it occurs."],
                observed_signals=["done"],
                timing_assumptions=["Observe around protocol events without fixed latency assumptions."],
                coverage_tags=["sequence", "persistence"],
                semantic_tags=["ambiguity_preserving"],
                confidence=0.8,
            )
        ],
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )

    checks = [
        check
        for oracle_case in [*oracle.protocol_oracles, *oracle.functional_oracles, *oracle.property_oracles]
        if oracle_case.linked_plan_case_id == "protocol_001"
        for check in oracle_case.checks
        if "done" in check.signal_policies
    ]

    assert checks
    assert all(check.signal_policies["done"].strength == AssertionStrength.GUARDED for check in checks)
    assert all(check.signal_policies["done"].definedness_mode == DefinednessMode.NOT_REQUIRED for check in checks)


def test_oracle_treats_valid_driven_edge_cases_as_control_heavy_for_primary_outputs(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="demo_serial2parallel",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="din_serial", direction=PortDirection.INPUT, width=1),
            PortSpec(name="din_valid", direction=PortDirection.INPUT, width=1),
            PortSpec(name="dout_parallel", direction=PortDirection.OUTPUT, width=8),
            PortSpec(name="dout_valid", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["dout_parallel", "dout_valid"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.85),
        assumptions=[
            "dout_parallel outputs the accumulated byte after a legal transfer.",
            "dout_valid is set to '1' after a complete transfer.",
        ],
        contract_confidence=0.85,
    )
    plan = PlanModel(
        module_name="demo_serial2parallel",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.82,
        cases=[
            PlanCaseModel(
                case_id="edge_001",
                goal="Probe valid-edge handling conservatively.",
                category=PlanCategory.EDGE,
                stimulus_intent=["Toggle din_valid at the transfer boundary."],
                stimulus_signals=["din_valid"],
                expected_properties=["Observe externally visible progress."],
                observed_signals=["dout_parallel", "dout_valid"],
                timing_assumptions=["Observe after rising edges of clk."],
                coverage_tags=["edge"],
                semantic_tags=["width_sensitive"],
                confidence=0.82,
            )
        ],
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )

    functional_case = next(case for case in oracle.functional_oracles if case.linked_plan_case_id == "edge_001")
    check = functional_case.checks[0]

    assert check.signal_policies["dout_parallel"].strength == AssertionStrength.UNRESOLVED
    assert check.signal_policies["dout_valid"].strength == AssertionStrength.UNRESOLVED


def test_oracle_reset_scalar_data_like_output_does_not_require_immediate_definedness(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="demo_parallel2serial",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="d", direction=PortDirection.INPUT, width=4),
            PortSpec(name="dout", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="valid_out", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["dout", "valid_out"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.86),
        assumptions=[
            "dout is assigned from serialized data.",
            "During reset, dout behavior may be implementation dependent until normal operation resumes.",
        ],
        contract_confidence=0.85,
    )
    plan = PlanModel(
        module_name="demo_parallel2serial",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.82,
        cases=[
            PlanCaseModel(
                case_id="reset_001",
                goal="reset baseline",
                category=PlanCategory.RESET,
                stimulus_intent=["assert reset"],
                stimulus_signals=["rst_n"],
                expected_properties=["stable baseline"],
                observed_signals=["dout", "valid_out"],
                timing_assumptions=["conservative"],
                coverage_tags=["reset"],
                semantic_tags=["ambiguity_preserving"],
                confidence=0.8,
            )
        ],
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )

    reset_case = next(case for case in oracle.functional_oracles if case.linked_plan_case_id == "reset_001")
    check = reset_case.checks[0]
    assert check.signal_policies["dout"].definedness_mode == DefinednessMode.NOT_REQUIRED


def test_oracle_preserves_scalar_status_output_ambiguity_for_width_sensitive_seq_edges(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="demo_lifo",
        ports=[
            PortSpec(name="Clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="Rst", direction=PortDirection.INPUT, width=1),
            PortSpec(name="dataIn", direction=PortDirection.INPUT, width=4),
            PortSpec(name="RW", direction=PortDirection.INPUT, width=1),
            PortSpec(name="EN", direction=PortDirection.INPUT, width=1),
            PortSpec(name="EMPTY", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="FULL", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="dataOut", direction=PortDirection.OUTPUT, width=4),
        ],
        observable_outputs=["EMPTY", "FULL", "dataOut"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.88),
        assumptions=[
            "EMPTY is set based on the stack pointer status.",
            "FULL is set based on the stack pointer status.",
        ],
        contract_confidence=0.88,
    )
    plan = PlanModel(
        module_name="demo_lifo",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.83,
        cases=[
            PlanCaseModel(
                case_id="edge_001",
                goal="Probe width-sensitive buffer boundaries.",
                category=PlanCategory.EDGE,
                stimulus_intent=["Exercise write/read behavior at a boundary value."],
                stimulus_signals=["dataIn", "EN"],
                expected_properties=["Observe externally visible flag progress."],
                observed_signals=["EMPTY", "FULL", "dataOut"],
                timing_assumptions=["Observe after rising edges of Clk."],
                coverage_tags=["edge", "boundary"],
                semantic_tags=["width_sensitive"],
                confidence=0.83,
            )
        ],
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )

    functional_case = next(case for case in oracle.functional_oracles if case.linked_plan_case_id == "edge_001")
    check = functional_case.checks[0]

    assert check.signal_policies["EMPTY"].strength == AssertionStrength.UNRESOLVED
    assert check.signal_policies["FULL"].strength == AssertionStrength.UNRESOLVED


def test_oracle_emits_fifo_readback_relation_for_weak_async_fifo_contract(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="asyn_fifo",
        ports=[
            PortSpec(name="wclk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rclk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="wrstn", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rrstn", direction=PortDirection.INPUT, width=1),
            PortSpec(name="winc", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rinc", direction=PortDirection.INPUT, width=1),
            PortSpec(name="wdata", direction=PortDirection.INPUT, width=8),
            PortSpec(name="wfull", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="rempty", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="rdata", direction=PortDirection.OUTPUT, width=8),
        ],
        observable_outputs=["wfull", "rempty", "rdata"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.75),
        contract_confidence=0.68,
        ambiguities=["a", "b", "c"],
    )
    plan = PlanModel(
        module_name="asyn_fifo",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.82,
        cases=[
            PlanCaseModel(
                case_id="basic_001",
                goal="write then read",
                category=PlanCategory.BASIC,
                stimulus_intent=["write a value then read it back"],
                stimulus_signals=["winc", "rinc", "wdata"],
                expected_properties=["observe fifo behavior"],
                observed_signals=["wfull", "rempty", "rdata"],
                timing_assumptions=["clocked"],
                coverage_tags=["basic", "seq"],
                semantic_tags=["operation_specific"],
                confidence=0.8,
            )
        ],
        unresolved_items=["generic ambiguity 1", "generic ambiguity 2", "generic ambiguity 3"],
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )

    functional_case = next(case for case in oracle.functional_oracles if case.linked_plan_case_id == "basic_001")
    assert any(check.relation_kind == "fifo_write_readback" for check in functional_case.checks)


def test_oracle_emits_packing_and_divide_relations_for_operation_specific_cases(tmp_path: Path) -> None:
    width_contract = DUTContract(
        module_name="width_8to16",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="valid_in", direction=PortDirection.INPUT, width=1),
            PortSpec(name="data_in", direction=PortDirection.INPUT, width=8),
            PortSpec(name="valid_out", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="data_out", direction=PortDirection.OUTPUT, width=16),
        ],
        observable_outputs=["valid_out", "data_out"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.82),
        contract_confidence=0.8,
    )
    width_plan = PlanModel(
        module_name="width_8to16",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.82,
        cases=[
            PlanCaseModel(
                case_id="basic_001",
                goal="pack bytes",
                category=PlanCategory.BASIC,
                stimulus_intent=["drive two input bytes"],
                stimulus_signals=["valid_in", "data_in"],
                expected_properties=["observe packed output"],
                observed_signals=["valid_out", "data_out"],
                timing_assumptions=["clocked"],
                coverage_tags=["basic"],
                semantic_tags=["operation_specific"],
                confidence=0.8,
            )
        ],
    )

    width_oracle = OracleGenerator().run(
        contract=width_contract,
        plan=width_plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path / "width",
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )
    width_case = next(case for case in width_oracle.functional_oracles if case.linked_plan_case_id == "basic_001")
    assert any(check.relation_kind == "byte_pack_pair" for check in width_case.checks)

    div_contract = DUTContract(
        module_name="div_16bit",
        ports=[
            PortSpec(name="A", direction=PortDirection.INPUT, width=16),
            PortSpec(name="B", direction=PortDirection.INPUT, width=8),
            PortSpec(name="result", direction=PortDirection.OUTPUT, width=16),
            PortSpec(name="odd", direction=PortDirection.OUTPUT, width=16),
        ],
        observable_outputs=["result", "odd"],
        timing=TimingSpec(sequential_kind=SequentialKind.COMB, latency_model="unknown", confidence=0.72),
        contract_confidence=0.71,
    )
    div_plan = PlanModel(
        module_name="div_16bit",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.82,
        cases=[
            PlanCaseModel(
                case_id="basic_001",
                goal="divide operands",
                category=PlanCategory.BASIC,
                stimulus_intent=["drive dividend/divisor"],
                stimulus_signals=["A", "B"],
                expected_properties=["observe quotient/remainder"],
                observed_signals=["result", "odd"],
                timing_assumptions=["settle"],
                coverage_tags=["basic"],
                semantic_tags=["operation_specific"],
                confidence=0.8,
            )
        ],
    )

    div_oracle = OracleGenerator().run(
        contract=div_contract,
        plan=div_plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path / "div",
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )
    div_case = next(case for case in div_oracle.functional_oracles if case.linked_plan_case_id == "basic_001")
    assert any(check.relation_kind == "unsigned_divide_16_by_8" for check in div_case.checks)


def test_oracle_does_not_force_pattern_detect_relation_for_generic_sequence_detector(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="sequence_detector",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="data_in", direction=PortDirection.INPUT, width=1),
            PortSpec(name="sequence_detected", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["sequence_detected"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
        contract_confidence=0.8,
    )
    plan = PlanModel(
        module_name="sequence_detector",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.82,
        cases=[
            PlanCaseModel(
                case_id="edge_001",
                goal="probe sequence",
                category=PlanCategory.EDGE,
                stimulus_intent=["drive a representative sequence"],
                stimulus_signals=["data_in"],
                expected_properties=["observe output progress"],
                observed_signals=["sequence_detected"],
                timing_assumptions=["clocked"],
                coverage_tags=["edge"],
                semantic_tags=["operation_specific"],
                confidence=0.8,
            )
        ],
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path / "sequence",
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )
    functional_case = next(case for case in oracle.functional_oracles if case.linked_plan_case_id == "edge_001")

    assert all(check.relation_kind != "sequence_pattern_detect" for check in functional_case.checks)


def test_oracle_emits_grouped_valid_accumulation_relation_for_accumulator_family(tmp_path: Path) -> None:
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
        assumptions=["valid_out is asserted after 4 valid input accumulation samples have been accepted."],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
        contract_confidence=0.82,
    )
    plan = TestPlanGenerator().run(
        contract=contract,
        task_description="Accumulate every four valid inputs and emit one output event.",
        spec_text="Use valid_in gating and allow reset to clear partial progress.",
        out_dir=tmp_path / "plan_src",
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )

    grouped_cases = [
        case
        for case in oracle.functional_oracles
        if any(check.relation_kind == "grouped_valid_accumulation" for check in case.checks)
    ]
    assert grouped_cases
    closure_case = next(case for case in grouped_cases if case.linked_plan_case_id == "basic_002")
    grouped_check = next(check for check in closure_case.checks if check.relation_kind == "grouped_valid_accumulation")
    assert grouped_check.oracle_pattern
    assert "\"group_size\": 4" in grouped_check.oracle_pattern
    assert grouped_check.expected_transition == "single_group_sum"


def test_oracle_emits_ring_and_traffic_relations_for_autonomous_stateful_families(tmp_path: Path) -> None:
    ring_contract = DUTContract(
        module_name="ring_counter",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="reset", direction=PortDirection.INPUT, width=1),
            PortSpec(name="out", direction=PortDirection.OUTPUT, width=8),
        ],
        observable_outputs=["out"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
        contract_confidence=0.8,
    )
    ring_plan = TestPlanGenerator().run(
        contract=ring_contract,
        task_description="Ring counter",
        spec_text="Rotate a single asserted bit across the output register.",
        out_dir=tmp_path / "ring_plan",
    )
    ring_oracle = OracleGenerator().run(
        contract=ring_contract,
        plan=ring_plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path / "ring_oracle",
        based_on_contract="ring_contract.json",
        based_on_plan="ring_plan.json",
    )
    ring_case = next(case for case in ring_oracle.functional_oracles if case.linked_plan_case_id == "basic_001")
    assert any(check.relation_kind == "one_hot_rotation_progression" for check in ring_case.checks)

    traffic_contract = DUTContract(
        module_name="traffic_light",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="pass_request", direction=PortDirection.INPUT, width=1),
            PortSpec(name="red", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="yellow", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="green", direction=PortDirection.OUTPUT, width=1),
        ],
        observable_outputs=["red", "yellow", "green"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
        contract_confidence=0.8,
    )
    traffic_plan = TestPlanGenerator().run(
        contract=traffic_contract,
        task_description="Traffic light controller",
        spec_text="Respond to pass_request by progressing through green, yellow, and red phases.",
        out_dir=tmp_path / "traffic_plan",
    )
    traffic_oracle = OracleGenerator().run(
        contract=traffic_contract,
        plan=traffic_plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path / "traffic_oracle",
        based_on_contract="traffic_contract.json",
        based_on_plan="traffic_plan.json",
    )
    basic_case = next(case for case in traffic_oracle.functional_oracles if case.linked_plan_case_id == "basic_001")
    assert any(check.relation_kind == "traffic_light_phase_progression" for check in basic_case.checks)


def test_oracle_reset_data_outputs_do_not_require_immediate_definedness_without_reset_specific_evidence(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="demo_seq_ram",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="read_en", direction=PortDirection.INPUT, width=1),
            PortSpec(name="read_addr", direction=PortDirection.INPUT, width=4),
            PortSpec(name="read_data", direction=PortDirection.OUTPUT, width=8),
        ],
        observable_outputs=["read_data"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.85),
        assumptions=[
            "If the read enable signal (read_en) is active, the data at the specified address is assigned to the read_data register.",
        ],
        contract_confidence=0.86,
    )
    plan = PlanModel(
        module_name="demo_seq_ram",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.8,
        cases=[
            PlanCaseModel(
                case_id="reset_001",
                goal="Establish a post-reset baseline.",
                category=PlanCategory.RESET,
                stimulus_intent=["Apply reset and observe outputs conservatively."],
                stimulus_signals=["rst_n"],
                expected_properties=["Post-reset behavior remains externally visible."],
                observed_signals=["read_data"],
                timing_assumptions=["Observe after reset release without fixed read latency assumptions."],
                coverage_tags=["reset"],
                semantic_tags=["ambiguity_preserving"],
                confidence=0.8,
            )
        ],
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )

    reset_functional = next(case for case in oracle.functional_oracles if case.linked_plan_case_id == "reset_001")
    check = reset_functional.checks[0]

    assert check.signal_policies["read_data"].strength == AssertionStrength.EXACT
    assert check.signal_policies["read_data"].definedness_mode == DefinednessMode.NOT_REQUIRED


def test_oracle_preserves_scalar_status_output_ambiguity_for_seq_protocol_guardrails(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="demo_lifo_protocol",
        ports=[
            PortSpec(name="Clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="Rst", direction=PortDirection.INPUT, width=1),
            PortSpec(name="dataIn", direction=PortDirection.INPUT, width=4),
            PortSpec(name="RW", direction=PortDirection.INPUT, width=1),
            PortSpec(name="EN", direction=PortDirection.INPUT, width=1),
            PortSpec(name="EMPTY", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="FULL", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="dataOut", direction=PortDirection.OUTPUT, width=4),
        ],
        observable_outputs=["EMPTY", "FULL", "dataOut"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.88),
        assumptions=[
            "EMPTY is set based on the stack pointer status.",
            "FULL is set based on the stack pointer status.",
        ],
        contract_confidence=0.88,
    )
    plan = PlanModel(
        module_name="demo_lifo_protocol",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.83,
        cases=[
            PlanCaseModel(
                case_id="protocol_001",
                goal="Validate push-pop ordering conservatively.",
                category=PlanCategory.PROTOCOL,
                stimulus_intent=["Push once, then pop once under enable."],
                stimulus_signals=["dataIn", "RW", "EN"],
                expected_properties=["Observe sequence-safe visible progress."],
                observed_signals=["EMPTY", "FULL", "dataOut"],
                timing_assumptions=["Observe after rising edges of Clk."],
                coverage_tags=["sequence", "push_pop"],
                semantic_tags=["ambiguity_preserving"],
                confidence=0.83,
            )
        ],
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )

    property_case = next(case for case in oracle.property_oracles if case.linked_plan_case_id == "protocol_001")
    check = property_case.checks[0]

    assert check.signal_policies["EMPTY"].strength == AssertionStrength.UNRESOLVED
    assert check.signal_policies["FULL"].strength == AssertionStrength.UNRESOLVED


def test_oracle_ignores_incidental_signal_mentions_when_building_explicit_output_hints(tmp_path: Path) -> None:
    contract = DUTContract(
        module_name="demo_traffic",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="red", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="counter", direction=PortDirection.OUTPUT, width=8),
        ],
        observable_outputs=["red", "counter"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.82),
        assumptions=[
            "If the red signal is inactive and the previous red signal was active, the counter is set to 10.",
        ],
        contract_confidence=0.82,
    )
    plan = PlanModel(
        module_name="demo_traffic",
        based_on_contract="demo",
        plan_strategy="rule_based_conservative",
        plan_confidence=0.79,
        cases=[
            PlanCaseModel(
                case_id="protocol_001",
                goal="Observe protocol-safe visible progress.",
                category=PlanCategory.PROTOCOL,
                stimulus_intent=["Observe red conservatively."],
                stimulus_signals=[],
                expected_properties=["Visibility remains conservative."],
                observed_signals=["red"],
                timing_assumptions=["Event-based observation only."],
                coverage_tags=["sequence"],
                semantic_tags=["ambiguity_preserving"],
                confidence=0.79,
            )
        ],
    )

    oracle = OracleGenerator().run(
        contract=contract,
        plan=plan,
        task_description=None,
        spec_text=None,
        out_dir=tmp_path,
        based_on_contract="demo_contract.json",
        based_on_plan="demo_plan.json",
    )

    property_case = next(case for case in oracle.property_oracles if case.linked_plan_case_id == "protocol_001")
    check = property_case.checks[0]

    assert check.signal_policies["red"].strength == AssertionStrength.UNRESOLVED


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
        env={
            **os.environ,
            "PYTHONPATH": str(_SRC) if not os.environ.get("PYTHONPATH") else f"{_SRC}{os.pathsep}{os.environ['PYTHONPATH']}",
        },
    )

    assert result.returncode == 0, result.stderr
    assert "Oracle generated for module 'simple_comb'" in result.stdout
    assert (tmp_path / "cli_oracle" / "oracle" / "oracle.json").exists()
