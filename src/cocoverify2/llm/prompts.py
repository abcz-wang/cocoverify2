"""Prompt builders for Phase 2/3 hybrid LLM generation."""

from __future__ import annotations

import json
from typing import Any

from cocoverify2.core.models import DUTContract, OracleSpec, TestPlan

_MAX_SPEC_CHARS = 12000
_MAX_TASK_CHARS = 4000


def build_plan_system_prompt() -> str:
    """Return the fixed system prompt for Phase 2 plan augmentation."""
    return (
        "You are generating a conservative verification-plan augmentation for RTL validation. "
        "Return JSON only. Do not include markdown, prose outside JSON, or code fences. "
        "Never invent ports, protocols, clocks, resets, outputs, or timing guarantees that are not present in the provided contract. "
        "Preserve ambiguity when behavior is underspecified. "
        "Always keep baseline basic and edge coverage intact; enrich or add cases without deleting baseline coverage."
    )


def build_plan_user_prompt(
    *,
    contract: DUTContract,
    baseline_plan: TestPlan,
    task_description: str | None,
    spec_text: str | None,
) -> str:
    """Build the Phase 2 augmentation prompt."""
    payload = {
        "task_description": _trim_text(task_description, _MAX_TASK_CHARS),
        "spec_text": _trim_text(spec_text, _MAX_SPEC_CHARS),
        "contract": _compact_contract(contract),
        "baseline_plan": baseline_plan.model_dump(mode="json"),
        "requirements": {
            "must_preserve_categories": ["basic", "edge"],
            "semantic_tag_examples": [
                "operation_specific",
                "invalid_illegal_input",
                "width_sensitive",
                "ambiguity_preserving",
            ],
            "allowed_actions": {
                "baseline_case_enrichments": [
                    "goal",
                    "stimulus_intent",
                    "timing_assumptions",
                    "observed_signals",
                    "stimulus_signals",
                    "expected_properties",
                    "coverage_tags",
                    "semantic_tags",
                    "notes",
                    "priority",
                ],
                "additional_cases": "coarse category only; use semantic_tags for richer subtypes",
            },
            "forbidden": [
                "inventing unknown signals",
                "removing baseline cases",
                "changing baseline case category",
                "assuming exact-cycle timing when contract timing is weak or unknown",
            ],
        },
        "output_schema": {
            "baseline_case_enrichments": [
                {
                    "case_id": "basic_001",
                    "goal": "optional string",
                    "stimulus_intent": ["optional strings"],
                    "timing_assumptions": ["optional strings"],
                    "observed_signals": ["known signals only"],
                    "stimulus_signals": ["known input signals only"],
                    "expected_properties": ["optional strings"],
                    "coverage_tags": ["optional strings"],
                    "semantic_tags": ["snake_case tags"],
                    "notes": ["optional strings"],
                    "priority": 1,
                }
            ],
            "additional_cases": [
                {
                    "draft_id": "new_case_001",
                    "category": "basic|edge|protocol|back_to_back|negative|regression|metamorphic",
                    "goal": "required",
                    "preconditions": [],
                    "stimulus_intent": ["required list"],
                    "stimulus_signals": ["known inputs only"],
                    "expected_properties": ["required list"],
                    "observed_signals": ["known signals only"],
                    "timing_assumptions": [],
                    "dependencies": ["baseline case_id or another draft_id"],
                    "coverage_tags": [],
                    "semantic_tags": [],
                    "notes": [],
                    "priority": 5,
                }
            ],
            "assumptions": [],
            "unresolved_items": [],
            "planning_notes": [],
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)


def build_oracle_system_prompt() -> str:
    """Return the fixed system prompt for Phase 3 oracle augmentation."""
    return (
        "You are generating a conservative oracle augmentation for RTL verification. "
        "Return JSON only. Do not include markdown, prose outside JSON, or code fences. "
        "Keep protocol, functional, and property checks separate. "
        "Never invent signals or reference-model semantics not grounded in the provided contract, plan, or spec. "
        "Prefer ambiguity-preserving checks when the spec or timing is uncertain."
    )


def build_oracle_user_prompt(
    *,
    contract: DUTContract,
    final_plan: TestPlan,
    baseline_oracle: OracleSpec,
    spec_text: str | None,
) -> str:
    """Build the Phase 3 augmentation prompt."""
    payload = {
        "spec_text": _trim_text(spec_text, _MAX_SPEC_CHARS),
        "contract": _compact_contract(contract),
        "final_plan": final_plan.model_dump(mode="json"),
        "baseline_oracle": baseline_oracle.model_dump(mode="json"),
        "requirements": {
            "oracle_classes": ["protocol", "functional", "property"],
            "semantic_tag_examples": [
                "operation_specific",
                "invalid_illegal_input",
                "width_sensitive",
                "ambiguity_preserving",
            ],
            "forbidden": [
                "replacing baseline checks",
                "inventing unknown signals",
                "using exact_cycle windows when timing is weak or unknown",
                "pretending spec certainty where ambiguity remains",
            ],
        },
        "output_schema": {
            "case_enrichments": [
                {
                    "linked_plan_case_id": "basic_001",
                    "oracle_class": "functional",
                    "checks": [
                        {
                            "check_type": "functional",
                            "description": "required",
                            "observed_signals": ["known signals only"],
                            "trigger_condition": "",
                            "pass_condition": "",
                            "temporal_window": {
                                "mode": "event_based|bounded_range|unbounded_safe|exact_cycle",
                                "min_cycles": 0,
                                "max_cycles": 1,
                                "anchor": "operation_applied",
                            },
                            "strictness": "conservative|guarded|strict",
                            "semantic_tags": ["snake_case tags"],
                            "notes": [],
                        }
                    ],
                    "assumptions": [],
                    "unresolved_items": [],
                    "notes": [],
                }
            ],
            "additional_oracle_cases": [
                {
                    "linked_plan_case_id": "edge_001",
                    "oracle_class": "property",
                    "checks": [],
                    "assumptions": [],
                    "unresolved_items": [],
                    "notes": [],
                }
            ],
            "assumptions": [],
            "unresolved_items": [],
            "oracle_notes": [],
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)


def _compact_contract(contract: DUTContract) -> dict[str, Any]:
    return {
        "module_name": contract.module_name,
        "ports": [port.model_dump(mode="json") for port in contract.ports],
        "clocks": [clock.model_dump(mode="json") for clock in contract.clocks],
        "resets": [reset.model_dump(mode="json") for reset in contract.resets],
        "handshake_groups": [group.model_dump(mode="json") for group in contract.handshake_groups],
        "handshake_signals": list(contract.handshake_signals),
        "timing": contract.timing.model_dump(mode="json"),
        "observable_outputs": list(contract.observable_outputs),
        "illegal_input_constraints": list(contract.illegal_input_constraints),
        "assumptions": list(contract.assumptions),
        "ambiguities": list(contract.ambiguities),
        "contract_confidence": contract.contract_confidence,
    }


def _trim_text(text: str | None, limit: int) -> str:
    content = str(text or "").strip()
    if len(content) <= limit:
        return content
    return f"{content[:limit].rstrip()} ...[truncated]"
