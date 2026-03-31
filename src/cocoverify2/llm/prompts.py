"""Prompt builders for Phase 2/3 hybrid LLM generation."""

from __future__ import annotations

import json
from typing import Any

from cocoverify2.core.models import DUTContract, LLMTodoBlock, OracleCase, OracleCheck, OracleSpec, TestCasePlan, TestPlan

_MAX_SPEC_CHARS = 12000
_MAX_PLAN_SPEC_CHARS = 2500
_MAX_TASK_CHARS = 4000
_MAX_PLAN_TASK_CHARS = 2000
_MAX_FILE_CONTEXT_CHARS = 6000


def build_plan_system_prompt() -> str:
    """Return the fixed system prompt for Phase 2 plan augmentation."""
    return (
        "You are generating a conservative verification-plan augmentation for RTL validation. "
        "Return JSON only. Do not include markdown, prose outside JSON, or code fences. "
        "Never invent ports, protocols, clocks, resets, outputs, or timing guarantees that are not present in the provided contract. "
        "Preserve ambiguity when behavior is underspecified. "
        "Always keep baseline basic and edge coverage intact; enrich or add cases without deleting baseline coverage. "
        "Follow the schema exactly. In additional_cases, use 'draft_id' and never emit 'case_id'. "
        "Do not emit confidence, source, or other bookkeeping fields. "
        "In additional_cases, 'category' is a coarse enum only: reset, basic, edge, protocol, back_to_back, negative, regression, metamorphic. "
        "Put richer subtype information into 'scenario_kind', not into 'category'. "
        "For sequential accumulator, counter, or valid-gated stream families, include at least one concrete closure case that can produce an externally visible output event when the contract or spec supports it. "
        "When valid-like gating exists, include at least one interrupted or gapped-valid case and make end-of-case cleanup explicit so tail cycles do not accidentally create extra accepted samples. "
        "When grouped or width-sensitive accumulation exists, include at least one boundary-output case using concrete literals. "
        "Inside stimulus_program, drive and record_inputs steps must use only concrete deterministic literals: bools, integers, 0x-style literals, or Verilog numeric literals such as 16'h1234. "
        "Never emit placeholders like rand64, random, arbitrary, any_value, or symbolic generator tokens."
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
        "task_description": _trim_text(task_description, _MAX_PLAN_TASK_CHARS),
        "spec_text": _compact_plan_spec_text(spec_text),
        "contract": _compact_contract_for_plan(contract),
        "baseline_plan_summary": {
            "module_name": baseline_plan.module_name,
            "plan_strategy": baseline_plan.plan_strategy,
            "plan_confidence": baseline_plan.plan_confidence,
            "case_count": len(baseline_plan.cases),
            "categories": sorted({str(case.category) for case in baseline_plan.cases}),
            "unresolved_items": baseline_plan.unresolved_items[:8],
        },
        "baseline_plan_cases": _compact_plan_cases(baseline_plan),
        "requirements": {
            "must_preserve_categories": ["basic", "edge"],
            "coarse_category_enum": [
                "reset",
                "basic",
                "edge",
                "protocol",
                "back_to_back",
                "negative",
                "regression",
                "metamorphic",
            ],
            "semantic_tag_examples": [
                "operation_specific",
                "invalid_illegal_input",
                "width_sensitive",
                "ambiguity_preserving",
            ],
            "category_vs_scenario_examples": [
                {
                    "category": "basic",
                    "scenario_kind": "write_then_readback",
                    "goal": "Write then read back while keeping a coarse basic category.",
                },
                {
                    "category": "protocol",
                    "scenario_kind": "fsm_transition_path",
                    "goal": "Exercise a transition-path protocol scenario while keeping category protocol.",
                },
            ],
            "allowed_actions": {
                "baseline_case_enrichments": "Append or refine only the documented case fields; never change case_id/category/dependencies.",
                "additional_cases": "coarse category only; use semantic_tags for richer subtypes",
            },
            "structured_scenarios": {
                "scenario_kind_allowed": [
                    "single_operation",
                    "boundary_vector",
                    "write_then_readback",
                    "fsm_transition_path",
                    "protocol_acceptance",
                    "backpressure_wait",
                    "back_to_back_pair",
                    "metamorphic_pair",
                    "reference_model_lite",
                    "grouped_valid_closure",
                    "gapped_valid_group",
                    "multi_group_stream",
                    "reset_mid_progress",
                ],
                "stimulus_program_rules": [
                    "Use only structured steps: drive, wait_for_settle, wait_cycles, record_inputs, record_note.",
                    "Drive only known input signals.",
                    "Drive values and cycles must be concrete deterministic literals or integers.",
                    "Never emit placeholders such as rand64, random, arbitrary, any_value, or symbolic generator tokens.",
                    "cycles fields must be concrete JSON integers, never arithmetic expressions.",
                    "record_inputs captures only already-applied input signal values, never outputs.",
                    "When a valid-like control is asserted for a finite scenario, add an explicit cleanup drive that deasserts it before the case ends unless the scenario requires it to remain high.",
                ],
            },
            "family_expectations": [
                "For grouped valid-gated accumulation, add at least one case that completes a full group and can produce one externally visible output event.",
                "For grouped valid-gated accumulation, add at least one gapped-valid case when valid-like gating exists.",
                "For repeated stream families, prefer a finite multi-group stream over a one-token smoke case only.",
            ],
            "forbidden": [
                "inventing unknown signals",
                "removing baseline cases",
                "changing baseline case category",
                "assuming exact-cycle timing when contract timing is weak or unknown",
                "emitting case_id inside additional_cases",
                "emitting confidence or source bookkeeping fields",
            ],
        },
        "output_schema": {
            "baseline_case_enrichments": [
                {
                    "case_id": "basic_001",
                    "goal": "",
                    "stimulus_intent": [],
                    "timing_assumptions": [],
                    "observed_signals": [],
                    "stimulus_signals": [],
                    "expected_properties": [],
                    "coverage_tags": [],
                    "semantic_tags": [],
                    "scenario_kind": "<scenario_kind_allowed>",
                    "stimulus_program": [{"action": "drive|wait_for_settle|wait_cycles|record_inputs|record_note", "signals": {"known_input": "0x1"}, "cycles": 1, "text": ""}],
                    "settle_requirement": "",
                    "comparison_operands": [],
                    "relation_kind": "",
                    "expected_transition": "",
                    "reference_domain": "",
                    "notes": [],
                    "priority": 1
                }
            ],
            "additional_cases": [
                {
                    "draft_id": "new_case_001",
                    "category": "<coarse_category_enum>",
                    "goal": "required",
                    "preconditions": [],
                    "stimulus_intent": [],
                    "stimulus_signals": [],
                    "expected_properties": [],
                    "observed_signals": [],
                    "timing_assumptions": [],
                    "dependencies": [],
                    "coverage_tags": [],
                    "semantic_tags": [],
                    "scenario_kind": "<scenario_kind_allowed>",
                    "stimulus_program": [{"action": "drive|wait_for_settle|wait_cycles|record_inputs|record_note", "signals": {"known_input": "0x1"}, "cycles": 1, "text": ""}],
                    "settle_requirement": "",
                    "comparison_operands": [],
                    "relation_kind": "",
                    "expected_transition": "",
                    "reference_domain": "",
                    "notes": [],
                    "priority": 5
                }
            ],
            "assumptions": [],
            "unresolved_items": [],
            "planning_notes": [],
        },
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True, ensure_ascii=True)


def build_oracle_system_prompt() -> str:
    """Return the fixed system prompt for Phase 3 oracle augmentation."""
    return (
        "You are generating a conservative oracle augmentation for RTL verification. "
        "Return JSON only. Do not include markdown, prose outside JSON, or code fences. "
        "Keep protocol, functional, and property checks separate. "
        "Never invent signals or reference-model semantics not grounded in the provided contract, plan, or spec. "
        "Prefer ambiguity-preserving checks when the spec or timing is uncertain. "
        "When the plan stimulus is concrete and finite, prefer value-level or relation-level functional checks over generic 'eventual progress' wording whenever the contract/spec supports them. "
        "For grouped sequential streams, express closure semantics such as no output before a full group, output event after a full group, reset-clears-partial-progress, and repeated-group behavior when those semantics are supported by the provided artifact evidence. "
        "Follow the schema exactly. Do not emit check_id, confidence, signal_policies, source, case_id, or oracle_group fields; the merge layer owns those fields."
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
            "preferred_functional_semantics": [
                "Use value-level checks when the plan drives concrete finite inputs and the contract/spec supports the relation.",
                "For valid-gated grouped streams, prefer output-closure or input-history-to-output relations over generic eventual-progress checks.",
                "Avoid exact-cycle timing claims unless the contract explicitly supports them.",
            ],
            "forbidden": [
                "replacing baseline checks",
                "inventing unknown signals",
                "using exact_cycle windows when timing is weak or unknown",
                "pretending spec certainty where ambiguity remains",
                "emitting check_id, confidence, signal_policies, or source fields",
                "emitting case_id or oracle_group for oracle cases",
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


def _compact_contract_for_plan(contract: DUTContract) -> dict[str, Any]:
    return {
        "module_name": contract.module_name,
        "ports": [
            {
                "name": port.name,
                "direction": str(port.direction),
                "width": port.width,
            }
            for port in contract.ports
        ],
        "clocks": [clock.name for clock in contract.clocks],
        "resets": [
            {
                "name": reset.name,
                "active_level": reset.active_level,
            }
            for reset in contract.resets
        ],
        "handshake_groups": [
            {
                "group_name": group.group_name,
                "pattern": group.pattern,
                "signals": group.signals,
            }
            for group in contract.handshake_groups
        ],
        "observable_outputs": list(contract.observable_outputs),
        "handshake_signals": list(contract.handshake_signals),
        "timing": {
            "sequential_kind": str(contract.timing.sequential_kind),
            "latency_model": str(contract.timing.latency_model),
            "confidence": contract.timing.confidence,
        },
        "contract_confidence": contract.contract_confidence,
        "ambiguities": list(contract.ambiguities[:8]),
        "assumptions": list(contract.assumptions[:6]),
    }


def _compact_plan_cases(plan: TestPlan) -> list[dict[str, Any]]:
    return [
        {
            "case_id": case.case_id,
            "category": str(case.category),
            "goal": case.goal,
            "stimulus_signals": list(case.stimulus_signals),
            "observed_signals": list(case.observed_signals),
            "execution_policy": case.execution_policy,
            "scenario_kind": case.scenario_kind,
            "settle_requirement": case.settle_requirement,
            "timing_assumptions": list(case.timing_assumptions[:3]),
            "dependencies": list(case.dependencies),
            "coverage_tags": list(case.coverage_tags),
            "semantic_tags": list(case.semantic_tags),
            "comparison_operands": list(case.comparison_operands),
            "relation_kind": case.relation_kind,
            "expected_transition": case.expected_transition,
            "reference_domain": case.reference_domain,
        }
        for case in plan.cases
    ]


def _compact_plan_spec_text(spec_text: str | None) -> str:
    return _trim_text(spec_text, _MAX_PLAN_SPEC_CHARS)


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
