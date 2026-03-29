"""Validator tests for LLM hybrid plan/oracle payloads."""

from __future__ import annotations

from cocoverify2.core.models import DUTContract, LLMTodoBlock, OracleSpec, PortSpec, TestCasePlan as CasePlanModel, TestPlan as PlanModel, TimingSpec
from cocoverify2.core.types import LatencyModel, PortDirection, SequentialKind, TemporalWindowMode, TestCategory as PlanCategory
from cocoverify2.llm.validators import (
    extract_json_payload,
    normalize_oracle_augmentation_payload,
    normalize_plan_augmentation_payload,
    parse_plan_augmentation,
    parse_oracle_augmentation,
    parse_todo_fill_response,
    validate_oracle_augmentation,
    validate_plan_augmentation,
    validate_todo_fill_response,
)


def _demo_contract() -> DUTContract:
    return DUTContract(
        module_name="demo",
        ports=[
            PortSpec(name="a", direction=PortDirection.INPUT),
            PortSpec(name="b", direction=PortDirection.INPUT),
            PortSpec(name="y", direction=PortDirection.OUTPUT),
        ],
        observable_outputs=["y"],
        timing=TimingSpec(
            sequential_kind=SequentialKind.UNKNOWN,
            latency_model=LatencyModel.UNKNOWN,
            confidence=0.4,
        ),
        contract_confidence=0.55,
    )


def _demo_plan() -> PlanModel:
    return PlanModel(
        module_name="demo",
        based_on_contract="contract.json",
        plan_strategy="rule_based_conservative",
        cases=[
            CasePlanModel(
                case_id="basic_001",
                goal="demo",
                category=PlanCategory.BASIC,
                stimulus_intent=["Drive a legal pattern."],
                stimulus_signals=["a", "b"],
                expected_properties=["Observe y."],
                observed_signals=["y"],
                timing_assumptions=["Stay conservative."],
                coverage_tags=["basic"],
                confidence=0.5,
                source="rule_based",
            )
        ],
        plan_confidence=0.5,
    )


def _demo_oracle() -> OracleSpec:
    return OracleSpec(
        module_name="demo",
        based_on_contract="contract.json",
        based_on_plan="plan.json",
        oracle_strategy="rule_based_conservative",
    )


def test_parse_plan_augmentation_extracts_json_from_code_fence() -> None:
    payload = parse_plan_augmentation(
        """```json
        {
          "baseline_case_enrichments": [],
          "additional_cases": [],
          "assumptions": ["demo"],
          "unresolved_items": [],
          "planning_notes": []
        }
        ```"""
    )

    assert payload.assumptions == ["demo"]


def test_validate_plan_augmentation_filters_unknown_signals_and_normalizes_tags() -> None:
    augmentation = parse_plan_augmentation(
        """
        {
          "baseline_case_enrichments": [],
          "additional_cases": [
            {
              "draft_id": "extra_001",
              "category": "basic",
              "goal": "extra",
              "preconditions": [],
              "stimulus_intent": ["Drive a new case."],
              "stimulus_signals": ["a", "unknown"],
              "expected_properties": ["Observe y."],
              "observed_signals": ["y", "ghost"],
              "timing_assumptions": [],
              "dependencies": ["basic_001"],
              "coverage_tags": ["Basic"],
              "semantic_tags": ["Operation Specific"],
              "notes": [],
              "priority": 3
            }
          ],
          "assumptions": [],
          "unresolved_items": [],
          "planning_notes": []
        }
        """
    )

    validated, report = validate_plan_augmentation(augmentation, contract=_demo_contract(), baseline_plan=_demo_plan())

    extra_case = validated.additional_cases[0]
    assert extra_case.stimulus_signals == ["a"]
    assert extra_case.observed_signals == ["y"]
    assert extra_case.coverage_tags == ["basic"]
    assert extra_case.semantic_tags == ["operation_specific"]
    assert report["signal_normalization_warnings"]


def test_normalize_plan_augmentation_repairs_case_id_to_draft_id() -> None:
    payload = extract_json_payload(
        """
        {
          "baseline_case_enrichments": [],
          "additional_cases": [
            {
              "case_id": "negative_001",
              "category": "negative",
              "goal": "Probe an invalid input partition conservatively.",
              "stimulus_intent": ["Drive a constrained invalid partition."],
              "stimulus_signals": ["a"],
              "expected_properties": ["Observe external safety only."],
              "observed_signals": ["y"],
              "confidence": 0.2,
              "source": "llm"
            }
          ]
        }
        """
    )

    normalized, report = normalize_plan_augmentation_payload(payload)

    assert normalized["additional_cases"][0]["draft_id"] == "negative_001"
    assert "case_id" not in normalized["additional_cases"][0]
    assert any(item["from"] == "case_id" and item["to"] == "draft_id" for item in report["renamed_fields"])
    assert any(item["field"] == "confidence" for item in report["stripped_fields"])


def test_normalize_oracle_augmentation_strips_safe_extra_check_fields() -> None:
    payload = extract_json_payload(
        """
        {
          "case_enrichments": [],
          "additional_oracle_cases": [
            {
              "linked_plan_case_id": "basic_001",
              "oracle_group": "property",
              "checks": [
                {
                  "check_type": "property",
                  "description": "Observe safety-style behavior.",
                  "observed_signals": ["y"],
                  "trigger_condition": "when driven",
                  "pass_condition": "remain externally consistent",
                  "temporal_window": {"mode": "event_based"},
                  "strictness": "guarded",
                  "semantic_tags": [],
                  "notes": [],
                  "check_id": "basic_001_property_002",
                  "confidence": 0.2,
                  "signal_policies": {"y": {"strength": "guarded"}},
                  "source": "rule_based"
                }
              ],
              "case_id": "property_basic_001",
              "confidence": 0.2
            }
          ]
        }
        """
    )

    normalized, report = normalize_oracle_augmentation_payload(payload)

    oracle_case = normalized["additional_oracle_cases"][0]
    check = oracle_case["checks"][0]
    assert oracle_case["oracle_class"] == "property"
    assert "oracle_group" not in oracle_case
    assert "case_id" not in oracle_case
    assert "check_id" not in check
    assert "signal_policies" not in check
    assert any(item["field"] == "check_id" for item in report["stripped_fields"])


def test_validate_oracle_augmentation_downgrades_exact_cycle_and_strict() -> None:
    augmentation = parse_oracle_augmentation(
        """
        {
          "case_enrichments": [
            {
              "linked_plan_case_id": "basic_001",
              "oracle_class": "functional",
              "checks": [
                {
                  "check_type": "functional",
                  "description": "demo check",
                  "observed_signals": ["y", "ghost"],
                  "trigger_condition": "when driven",
                  "pass_condition": "observe stable output",
                  "temporal_window": {
                    "mode": "exact_cycle",
                    "min_cycles": 0,
                    "max_cycles": 1,
                    "anchor": "input_stable"
                  },
                  "strictness": "strict",
                  "semantic_tags": ["Ambiguity Preserving"],
                  "notes": []
                }
              ],
              "assumptions": [],
              "unresolved_items": [],
              "notes": []
            }
          ],
          "additional_oracle_cases": [],
          "assumptions": [],
          "unresolved_items": [],
          "oracle_notes": []
        }
        """
    )

    validated, report = validate_oracle_augmentation(
        augmentation,
        contract=_demo_contract(),
        plan=_demo_plan(),
        baseline_oracle=_demo_oracle(),
    )

    check = validated.case_enrichments[0].checks[0]
    assert check.observed_signals == ["y"]
    assert check.temporal_window.mode == TemporalWindowMode.EVENT_BASED
    assert check.strictness == "conservative"
    assert check.semantic_tags == ["ambiguity_preserving"]
    assert report["check_adjustments"]


def test_parse_and_validate_todo_fill_response_accepts_safe_block_code() -> None:
    response = parse_todo_fill_response(
        """
        {
          "block_id": "stimulus_basic_001",
          "code_lines": [
            "signals = {'a': 1, 'b': 1}",
            "await self.drive_inputs(**signals)",
            "self.record_case_inputs('basic_001', signals)"
          ],
          "helper_calls": ["drive_inputs", "record_case_inputs"],
          "assumptions": [],
          "unresolved_items": []
        }
        """
    )
    block = LLMTodoBlock(
        block_id="stimulus_basic_001",
        fill_kind="stimulus",
        case_id="basic_001",
        start_marker="# TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_001 case_id=basic_001",
        end_marker="# TODO(cocoverify2:stimulus) END block_id=stimulus_basic_001 case_id=basic_001",
    )

    validated, report = validate_todo_fill_response(response, block=block)

    assert validated.block_id == "stimulus_basic_001"
    assert "drive_inputs" in report["used_helper_calls"]


def test_validate_todo_fill_response_rejects_imports() -> None:
    response = parse_todo_fill_response(
        """
        {
          "block_id": "oracle_basic_001_functional_001",
          "code_lines": [
            "import os",
            "assert_true(True, 'demo')"
          ],
          "helper_calls": ["assert_true"],
          "assumptions": [],
          "unresolved_items": []
        }
        """
    )
    block = LLMTodoBlock(
        block_id="oracle_basic_001_functional_001",
        fill_kind="oracle_check",
        case_id="basic_001",
        oracle_case_id="functional_basic_001",
        check_id="basic_001_functional_001",
        start_marker="# TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001",
        end_marker="# TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001",
    )

    try:
        validate_todo_fill_response(response, block=block)
    except ValueError as exc:
        assert "Import" in str(exc)
    else:
        raise AssertionError("Expected fill validator to reject import statements.")
