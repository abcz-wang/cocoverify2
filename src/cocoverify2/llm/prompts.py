"""Prompt builders for Phase 2/3 hybrid LLM generation."""

from __future__ import annotations

import json
from typing import Any

from cocoverify2.core.models import DUTContract, LLMTodoBlock, OracleCase, OracleCheck, OracleSpec, TestCasePlan, TestPlan

_MAX_SPEC_CHARS = 12000
_MAX_TASK_CHARS = 4000
_MAX_FILE_CONTEXT_CHARS = 6000


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


def build_todo_fill_system_prompt(fill_kind: str) -> str:
    """Return the fixed system prompt for block-level TODO filling."""
    if fill_kind == "stimulus":
        role = "stimulus-generation"
        goal = "Fill one cocotb stimulus TODO block with concrete legal drives only."
    elif fill_kind == "oracle_check":
        role = "oracle-generation"
        goal = (
            "Fill one cocotb oracle TODO block with concrete assertions derived from the spec and recorded inputs. "
            "Be ambiguity-preserving: only assert exact 0/1 semantics for an output when the spec explicitly defines that output's behavior. "
            "Do not infer carry, overflow, negative, or similar side-output rules from generic ALU conventions alone. "
            "If the repair feedback shows observed 'x' or 'z' values on the candidate DUT, relax those outputs unless the spec clearly forbids unknown or high-impedance behavior."
        )
    else:
        role = "todo-generation"
        goal = "Fill one cocotb TODO block conservatively."
    return (
        f"You are performing {role} for a rendered cocotb testbench. {goal} "
        "Return JSON only. Do not include markdown, code fences, or prose outside JSON. "
        "Never edit outside the target TODO block. "
        "Do not emit imports, function definitions, class definitions, file IO, network calls, subprocess calls, eval, exec, or shell commands. "
        "Use only the provided helper API contract and ordinary Python control flow."
    )


def build_todo_fill_user_prompt(
    *,
    block: LLMTodoBlock,
    contract: DUTContract,
    task_description: str | None,
    spec_text: str | None,
    file_context: str,
    helper_contract: dict[str, Any],
    plan_case: TestCasePlan | None = None,
    oracle_case: OracleCase | None = None,
    oracle_check: OracleCheck | None = None,
    repair_feedback: dict[str, Any] | None = None,
) -> str:
    """Build the user prompt for one block-level TODO fill request."""
    payload = {
        "task_description": _trim_text(task_description, _MAX_TASK_CHARS),
        "spec_text": _trim_text(spec_text, _MAX_SPEC_CHARS),
        "contract": _compact_contract(contract),
        "target_block": block.model_dump(mode="json"),
        "plan_case": plan_case.model_dump(mode="json") if plan_case is not None else None,
        "oracle_case": oracle_case.model_dump(mode="json") if oracle_case is not None else None,
        "oracle_check": oracle_check.model_dump(mode="json") if oracle_check is not None else None,
        "helper_contract": helper_contract,
        "file_context": _trim_text(file_context, _MAX_FILE_CONTEXT_CHARS),
        "repair_feedback": repair_feedback or {},
        "requirements": {
            "truth_source": "spec_first",
            "forbidden": [
                "inventing new ports or signals",
                "using DUT RTL as the primary functional truth source",
                "editing outside the target TODO block",
                "adding imports or top-level definitions",
            ],
            "stimulus_rules": [
                "Drive only known business inputs or declared stimulus_signals.",
                "Record concrete applied inputs using the helper contract.",
            ],
            "oracle_rules": [
                "Read recorded case inputs from env helpers.",
                "Assert against externally visible outputs only.",
                "Preserve ambiguity when the spec is underspecified.",
                "Do not invent exact semantics for secondary outputs unless the spec explicitly defines them.",
                "If an output appears as 'x' or 'z' in repair feedback, prefer ambiguity-preserving assertions for that output.",
                "Prefer checking primary result outputs and explicitly documented flags before asserting optional side outputs.",
            ],
        },
        "output_schema": {
            "block_id": block.block_id,
            "code_lines": ["Python statements only, without surrounding code fences."],
            "helper_calls": ["list helper names actually used"],
            "assumptions": ["optional strings"],
            "unresolved_items": ["optional strings"],
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True)
