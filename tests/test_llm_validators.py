"""Validator tests for LLM hybrid plan/oracle payloads."""

from __future__ import annotations

from cocoverify2.core.models import DUTContract, OracleSpec, PortSpec, TestCasePlan as CasePlanModel, TestPlan as PlanModel, TimingSpec
from cocoverify2.core.types import LatencyModel, PortDirection, SequentialKind, TemporalWindowMode, TestCategory as PlanCategory
from cocoverify2.llm.validators import (
    parse_plan_augmentation,
    parse_oracle_augmentation,
    validate_oracle_augmentation,
    validate_plan_augmentation,
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
