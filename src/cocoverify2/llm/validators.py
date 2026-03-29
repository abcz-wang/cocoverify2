"""Validation helpers for Phase 2/3 hybrid LLM payloads."""

from __future__ import annotations

import ast
import json
import re
from copy import deepcopy
from typing import Any

from cocoverify2.core.models import DUTContract, LLMTodoBlock, OracleSpec, TestPlan
from cocoverify2.core.types import OracleStrictness, SequentialKind, TemporalWindowMode
from cocoverify2.llm.schemas import (
    AdditionalOracleCase,
    AdditionalPlanCase,
    LLMOracleCheck,
    OracleAugmentation,
    OracleCaseEnrichment,
    PlanAugmentation,
    PlanCaseEnrichment,
    TodoFillResponse,
)

_ORACLE_CLASSES = {"protocol", "functional", "property"}
_STRICTNESS_THRESHOLD = 0.75
_SAFE_BUILTIN_CALLS = {"abs", "bool", "dict", "hex", "int", "len", "list", "max", "min", "range"}
_SAFE_DICT_METHODS = {"get", "items", "keys", "values"}
_DANGEROUS_CALLS = {
    "compile",
    "delattr",
    "dir",
    "eval",
    "exec",
    "getattr",
    "globals",
    "input",
    "locals",
    "open",
    "setattr",
    "vars",
    "__import__",
}
_FORBIDDEN_AST_NODES = (
    ast.AsyncFunctionDef,
    ast.ClassDef,
    ast.Delete,
    ast.FunctionDef,
    ast.Global,
    ast.Import,
    ast.ImportFrom,
    ast.Lambda,
    ast.Nonlocal,
    ast.Raise,
    ast.Try,
    ast.While,
    ast.With,
    ast.AsyncWith,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.Yield,
    ast.YieldFrom,
)
_STIMULUS_METHOD_CALLS = {"drive_inputs", "wait_for_settle", "record_case_inputs", "record_case_note", "sample_outputs"}
_ORACLE_METHOD_CALLS = {"get_case_inputs", "sample_outputs", "record_case_note", "signal_width"}
_ORACLE_HELPER_CALLS = {"assert_equal", "assert_true", "to_sint", "to_uint", "mask_width", "is_high_impedance", "is_unknown"}


def parse_plan_augmentation(raw_text: str) -> PlanAugmentation:
    """Parse raw JSON text into a validated Phase 2 augmentation model."""
    payload = extract_json_payload(raw_text)
    normalized, _ = normalize_plan_augmentation_payload(payload)
    return PlanAugmentation.model_validate(normalized)


def parse_oracle_augmentation(raw_text: str) -> OracleAugmentation:
    """Parse raw JSON text into a validated Phase 3 augmentation model."""
    payload = extract_json_payload(raw_text)
    normalized, _ = normalize_oracle_augmentation_payload(payload)
    return OracleAugmentation.model_validate(normalized)


def parse_todo_fill_response(raw_text: str) -> TodoFillResponse:
    """Parse raw JSON text into a validated block-level fill response."""
    payload = extract_json_payload(raw_text)
    return TodoFillResponse.model_validate(payload)


def extract_json_payload(raw_text: str) -> dict[str, Any]:
    """Extract a JSON object payload from raw model text."""
    payload = json.loads(extract_json_text(raw_text))
    if not isinstance(payload, dict):
        raise ValueError("LLM response JSON root must be an object.")
    return payload


def extract_json_text(raw_text: str) -> str:
    """Extract the most likely JSON object from a model response."""
    text = str(raw_text or "").strip()
    if not text:
        raise ValueError("LLM response was empty.")

    fence_match = re.search(r"```(?:json)?\s*(\{[\s\S]*\})\s*```", text, re.IGNORECASE)
    if fence_match:
        return fence_match.group(1).strip()

    start = text.find("{")
    if start < 0:
        raise ValueError("LLM response did not contain a JSON object.")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1].strip()
    raise ValueError("LLM response contained an unterminated JSON object.")


def normalize_plan_augmentation_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply conservative, semantics-preserving normalization for near-miss plan payloads."""
    normalized = deepcopy(payload)
    report: dict[str, Any] = {
        "renamed_fields": [],
        "stripped_fields": [],
    }
    allowed_top_level = {
        "baseline_case_enrichments",
        "additional_cases",
        "assumptions",
        "unresolved_items",
        "planning_notes",
    }
    _strip_known_top_level_extras(normalized, allowed_top_level, report=report, location="plan")
    normalized.setdefault("baseline_case_enrichments", [])
    normalized.setdefault("additional_cases", [])
    normalized.setdefault("assumptions", [])
    normalized.setdefault("unresolved_items", [])
    normalized.setdefault("planning_notes", [])

    for index, case in enumerate(_iter_mapping_list(normalized, "additional_cases")):
        location = f"additional_cases[{index}]"
        if "draft_id" not in case and "case_id" in case and isinstance(case.get("case_id"), str):
            case["draft_id"] = case.pop("case_id")
            report["renamed_fields"].append(
                {"location": location, "from": "case_id", "to": "draft_id"}
            )
        _strip_known_extras(
            case,
            allowed={
                "draft_id",
                "category",
                "goal",
                "preconditions",
                "stimulus_intent",
                "stimulus_signals",
                "expected_properties",
                "observed_signals",
                "timing_assumptions",
                "dependencies",
                "coverage_tags",
                "semantic_tags",
                "notes",
                "priority",
            },
            safe_extras={"case_id", "confidence", "source"},
            report=report,
            location=location,
        )

    for index, enrichment in enumerate(_iter_mapping_list(normalized, "baseline_case_enrichments")):
        _strip_known_extras(
            enrichment,
            allowed={
                "case_id",
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
            },
            safe_extras={"confidence", "source", "draft_id"},
            report=report,
            location=f"baseline_case_enrichments[{index}]",
        )

    return normalized, report


def normalize_oracle_augmentation_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Apply conservative, semantics-preserving normalization for near-miss oracle payloads."""
    normalized = deepcopy(payload)
    report: dict[str, Any] = {
        "renamed_fields": [],
        "stripped_fields": [],
    }
    allowed_top_level = {
        "case_enrichments",
        "additional_oracle_cases",
        "assumptions",
        "unresolved_items",
        "oracle_notes",
    }
    _strip_known_top_level_extras(normalized, allowed_top_level, report=report, location="oracle")
    normalized.setdefault("case_enrichments", [])
    normalized.setdefault("additional_oracle_cases", [])
    normalized.setdefault("assumptions", [])
    normalized.setdefault("unresolved_items", [])
    normalized.setdefault("oracle_notes", [])

    for bucket_name in ("case_enrichments", "additional_oracle_cases"):
        for index, oracle_case in enumerate(_iter_mapping_list(normalized, bucket_name)):
            location = f"{bucket_name}[{index}]"
            if "oracle_class" not in oracle_case and "oracle_group" in oracle_case and isinstance(oracle_case.get("oracle_group"), str):
                oracle_case["oracle_class"] = oracle_case.pop("oracle_group")
                report["renamed_fields"].append(
                    {"location": location, "from": "oracle_group", "to": "oracle_class"}
                )
            _strip_known_extras(
                oracle_case,
                allowed={
                    "linked_plan_case_id",
                    "oracle_class",
                    "checks",
                    "assumptions",
                    "unresolved_items",
                    "notes",
                },
                safe_extras={"case_id", "confidence", "source", "category", "oracle_group"},
                report=report,
                location=location,
            )
            for check_index, check in enumerate(_iter_mapping_list(oracle_case, "checks")):
                _strip_known_extras(
                    check,
                    allowed={
                        "check_type",
                        "description",
                        "observed_signals",
                        "trigger_condition",
                        "pass_condition",
                        "temporal_window",
                        "strictness",
                        "semantic_tags",
                        "notes",
                    },
                    safe_extras={"check_id", "confidence", "signal_policies", "source"},
                    report=report,
                    location=f"{location}.checks[{check_index}]",
                )
    return normalized, report


def _iter_mapping_list(container: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = container.get(key, [])
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def _strip_known_top_level_extras(
    payload: dict[str, Any],
    allowed: set[str],
    *,
    report: dict[str, Any],
    location: str,
) -> None:
    for extra_key in list(payload.keys()):
        if extra_key not in allowed:
            payload.pop(extra_key)
            report["stripped_fields"].append({"location": location, "field": extra_key})


def _strip_known_extras(
    item: dict[str, Any],
    *,
    allowed: set[str],
    safe_extras: set[str],
    report: dict[str, Any],
    location: str,
) -> None:
    for extra_key in list(item.keys()):
        if extra_key in allowed:
            continue
        if extra_key in safe_extras:
            item.pop(extra_key)
            report["stripped_fields"].append({"location": location, "field": extra_key})


def validate_plan_augmentation(
    augmentation: PlanAugmentation,
    *,
    contract: DUTContract,
    baseline_plan: TestPlan,
) -> tuple[PlanAugmentation, dict[str, Any]]:
    """Normalize and semantically validate a parsed Phase 2 augmentation."""
    known_case_ids = {case.case_id for case in baseline_plan.cases}
    known_input_signals = {
        port.name for port in contract.ports if str(port.direction) == "input"
    }
    known_observed_signals = _known_contract_signal_names(contract) | {
        signal for case in baseline_plan.cases for signal in case.observed_signals
    }

    report: dict[str, Any] = {
        "dropped_baseline_case_enrichments": [],
        "dropped_additional_cases": [],
        "signal_normalization_warnings": [],
    }
    valid_enrichments: list[PlanCaseEnrichment] = []
    for enrichment in augmentation.baseline_case_enrichments:
        if enrichment.case_id not in known_case_ids:
            report["dropped_baseline_case_enrichments"].append(
                {"case_id": enrichment.case_id, "reason": "unknown_case_id"}
            )
            continue
        normalized = enrichment.model_copy(deep=True)
        normalized.stimulus_intent = _normalize_text_list(normalized.stimulus_intent)
        normalized.timing_assumptions = _normalize_text_list(normalized.timing_assumptions)
        normalized.expected_properties = _normalize_text_list(normalized.expected_properties)
        normalized.coverage_tags = _normalize_tag_list(normalized.coverage_tags)
        normalized.semantic_tags = _normalize_tag_list(normalized.semantic_tags)
        normalized.notes = _normalize_text_list(normalized.notes)
        observed, observed_dropped = _filter_known_signals(normalized.observed_signals, known_observed_signals)
        stimulus, stimulus_dropped = _filter_known_signals(normalized.stimulus_signals, known_input_signals)
        normalized.observed_signals = observed
        normalized.stimulus_signals = stimulus
        if observed_dropped or stimulus_dropped:
            report["signal_normalization_warnings"].append(
                {
                    "case_id": enrichment.case_id,
                    "dropped_observed_signals": observed_dropped,
                    "dropped_stimulus_signals": stimulus_dropped,
                }
            )
        valid_enrichments.append(normalized)

    draft_ids = {case.draft_id for case in augmentation.additional_cases}
    valid_additional_cases: list[AdditionalPlanCase] = []
    for case in augmentation.additional_cases:
        normalized = case.model_copy(deep=True)
        normalized.preconditions = _normalize_text_list(normalized.preconditions)
        normalized.stimulus_intent = _normalize_text_list(normalized.stimulus_intent)
        normalized.expected_properties = _normalize_text_list(normalized.expected_properties)
        normalized.timing_assumptions = _normalize_text_list(normalized.timing_assumptions)
        normalized.coverage_tags = _normalize_tag_list(normalized.coverage_tags)
        normalized.semantic_tags = _normalize_tag_list(normalized.semantic_tags)
        normalized.notes = _normalize_text_list(normalized.notes)
        observed, observed_dropped = _filter_known_signals(normalized.observed_signals, known_observed_signals)
        stimulus, stimulus_dropped = _filter_known_signals(normalized.stimulus_signals, known_input_signals)
        normalized.observed_signals = observed
        normalized.stimulus_signals = stimulus
        normalized.dependencies = [
            dependency
            for dependency in _normalize_text_list(normalized.dependencies)
            if dependency in known_case_ids or dependency in draft_ids
        ]
        if not normalized.stimulus_intent or not normalized.expected_properties:
            report["dropped_additional_cases"].append(
                {"draft_id": case.draft_id, "reason": "missing_required_lists"}
            )
            continue
        if observed_dropped or stimulus_dropped:
            report["signal_normalization_warnings"].append(
                {
                    "draft_id": case.draft_id,
                    "dropped_observed_signals": observed_dropped,
                    "dropped_stimulus_signals": stimulus_dropped,
                }
            )
        valid_additional_cases.append(normalized)

    validated = PlanAugmentation(
        baseline_case_enrichments=valid_enrichments,
        additional_cases=valid_additional_cases,
        assumptions=_normalize_text_list(augmentation.assumptions),
        unresolved_items=_normalize_text_list(augmentation.unresolved_items),
        planning_notes=_normalize_text_list(augmentation.planning_notes),
    )
    return validated, report


def validate_oracle_augmentation(
    augmentation: OracleAugmentation,
    *,
    contract: DUTContract,
    plan: TestPlan,
    baseline_oracle: OracleSpec,
) -> tuple[OracleAugmentation, dict[str, Any]]:
    """Normalize and semantically validate a parsed Phase 3 augmentation."""
    del baseline_oracle
    known_plan_case_ids = {case.case_id for case in plan.cases}
    known_signals = _known_contract_signal_names(contract) | {
        signal for case in plan.cases for signal in case.observed_signals
    }
    weak_timing = (
        contract.timing.sequential_kind == SequentialKind.UNKNOWN
        or contract.contract_confidence < _STRICTNESS_THRESHOLD
        or plan.plan_confidence < _STRICTNESS_THRESHOLD
    )

    report: dict[str, Any] = {
        "dropped_case_enrichments": [],
        "dropped_additional_oracle_cases": [],
        "check_adjustments": [],
    }

    valid_enrichments: list[OracleCaseEnrichment] = []
    for enrichment in augmentation.case_enrichments:
        normalized = _normalize_oracle_enrichment(
            enrichment,
            known_plan_case_ids=known_plan_case_ids,
            known_signals=known_signals,
            weak_timing=weak_timing,
            report=report,
            item_key="linked_plan_case_id",
            drop_bucket="dropped_case_enrichments",
        )
        if normalized is not None:
            valid_enrichments.append(normalized)

    valid_additional_cases: list[AdditionalOracleCase] = []
    for oracle_case in augmentation.additional_oracle_cases:
        normalized = _normalize_additional_oracle_case(
            oracle_case,
            known_plan_case_ids=known_plan_case_ids,
            known_signals=known_signals,
            weak_timing=weak_timing,
            report=report,
        )
        if normalized is not None:
            valid_additional_cases.append(normalized)

    validated = OracleAugmentation(
        case_enrichments=valid_enrichments,
        additional_oracle_cases=valid_additional_cases,
        assumptions=_normalize_text_list(augmentation.assumptions),
        unresolved_items=_normalize_text_list(augmentation.unresolved_items),
        oracle_notes=_normalize_text_list(augmentation.oracle_notes),
    )
    return validated, report


def _normalize_oracle_enrichment(
    enrichment: OracleCaseEnrichment,
    *,
    known_plan_case_ids: set[str],
    known_signals: set[str],
    weak_timing: bool,
    report: dict[str, Any],
    item_key: str,
    drop_bucket: str,
) -> OracleCaseEnrichment | None:
    if enrichment.linked_plan_case_id not in known_plan_case_ids:
        report[drop_bucket].append(
            {item_key: enrichment.linked_plan_case_id, "reason": "unknown_plan_case_id"}
        )
        return None
    oracle_class = _normalize_oracle_class(enrichment.oracle_class)
    if oracle_class is None:
        report[drop_bucket].append(
            {item_key: enrichment.linked_plan_case_id, "reason": "unknown_oracle_class"}
        )
        return None
    checks = _normalize_oracle_checks(
        enrichment.checks,
        known_signals=known_signals,
        weak_timing=weak_timing,
        report=report,
        context_key=item_key,
        context_value=enrichment.linked_plan_case_id,
    )
    return OracleCaseEnrichment(
        linked_plan_case_id=enrichment.linked_plan_case_id,
        oracle_class=oracle_class,
        checks=checks,
        assumptions=_normalize_text_list(enrichment.assumptions),
        unresolved_items=_normalize_text_list(enrichment.unresolved_items),
        notes=_normalize_text_list(enrichment.notes),
    )


def _normalize_additional_oracle_case(
    oracle_case: AdditionalOracleCase,
    *,
    known_plan_case_ids: set[str],
    known_signals: set[str],
    weak_timing: bool,
    report: dict[str, Any],
) -> AdditionalOracleCase | None:
    if oracle_case.linked_plan_case_id not in known_plan_case_ids:
        report["dropped_additional_oracle_cases"].append(
            {"linked_plan_case_id": oracle_case.linked_plan_case_id, "reason": "unknown_plan_case_id"}
        )
        return None
    oracle_class = _normalize_oracle_class(oracle_case.oracle_class)
    if oracle_class is None:
        report["dropped_additional_oracle_cases"].append(
            {"linked_plan_case_id": oracle_case.linked_plan_case_id, "reason": "unknown_oracle_class"}
        )
        return None
    checks = _normalize_oracle_checks(
        oracle_case.checks,
        known_signals=known_signals,
        weak_timing=weak_timing,
        report=report,
        context_key="linked_plan_case_id",
        context_value=oracle_case.linked_plan_case_id,
    )
    if not checks:
        report["dropped_additional_oracle_cases"].append(
            {"linked_plan_case_id": oracle_case.linked_plan_case_id, "reason": "no_valid_checks"}
        )
        return None
    return AdditionalOracleCase(
        linked_plan_case_id=oracle_case.linked_plan_case_id,
        oracle_class=oracle_class,
        checks=checks,
        assumptions=_normalize_text_list(oracle_case.assumptions),
        unresolved_items=_normalize_text_list(oracle_case.unresolved_items),
        notes=_normalize_text_list(oracle_case.notes),
    )


def _normalize_oracle_checks(
    checks: list[LLMOracleCheck],
    *,
    known_signals: set[str],
    weak_timing: bool,
    report: dict[str, Any],
    context_key: str,
    context_value: str,
) -> list[LLMOracleCheck]:
    normalized_checks: list[LLMOracleCheck] = []
    for check in checks:
        normalized = check.model_copy(deep=True)
        observed, dropped = _filter_known_signals(normalized.observed_signals, known_signals)
        normalized.observed_signals = observed
        normalized.semantic_tags = _normalize_tag_list(normalized.semantic_tags)
        normalized.notes = _normalize_text_list(normalized.notes)

        if weak_timing and normalized.temporal_window.mode == TemporalWindowMode.EXACT_CYCLE:
            normalized.temporal_window.mode = TemporalWindowMode.EVENT_BASED
            if not normalized.temporal_window.anchor:
                normalized.temporal_window.anchor = "externally_visible_progress"
            report["check_adjustments"].append(
                {
                    context_key: context_value,
                    "description": normalized.description,
                    "adjustment": "downgraded_exact_cycle_to_event_based",
                }
            )

        if normalized.strictness == OracleStrictness.STRICT and weak_timing:
            normalized.strictness = OracleStrictness.CONSERVATIVE
            report["check_adjustments"].append(
                {
                    context_key: context_value,
                    "description": normalized.description,
                    "adjustment": "downgraded_strictness_to_conservative",
                }
            )

        if dropped:
            report["check_adjustments"].append(
                {
                    context_key: context_value,
                    "description": normalized.description,
                    "adjustment": "dropped_unknown_observed_signals",
                    "signals": dropped,
                }
            )
        normalized_checks.append(normalized)
    return normalized_checks


def _normalize_oracle_class(value: str) -> str | None:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in _ORACLE_CLASSES else None


def _known_contract_signal_names(contract: DUTContract) -> set[str]:
    port_names = {port.name for port in contract.ports}
    clock_names = {clock.name for clock in contract.clocks}
    reset_names = {reset.name for reset in contract.resets}
    return port_names | clock_names | reset_names | set(contract.observable_outputs) | set(contract.handshake_signals)


def _normalize_text_list(values: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        item = str(value or "").strip()
        if not item or item in seen:
            continue
        seen.add(item)
        normalized.append(item)
    return normalized


def _normalize_tag_list(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        tag = normalize_tag(value)
        if not tag or tag in seen:
            continue
        seen.add(tag)
        normalized.append(tag)
    return normalized


def normalize_tag(value: str) -> str:
    """Normalize a free-form tag into a lowercase snake_case token."""
    lowered = re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return lowered[:64]


def _filter_known_signals(values: list[str], allowed: set[str]) -> tuple[list[str], list[str]]:
    kept: list[str] = []
    dropped: list[str] = []
    seen: set[str] = set()
    for value in values:
        signal = str(value or "").strip()
        if not signal or signal in seen:
            continue
        if signal in allowed:
            seen.add(signal)
            kept.append(signal)
        else:
            dropped.append(signal)
    return kept, dropped


def validate_todo_fill_response(
    response: TodoFillResponse,
    *,
    block: LLMTodoBlock,
) -> tuple[TodoFillResponse, dict[str, Any]]:
    """Validate one parsed block-level fill response."""
    if response.block_id != block.block_id:
        raise ValueError(f"Fill response block_id mismatch: expected {block.block_id!r}, got {response.block_id!r}.")

    normalized_code = [line.rstrip() for line in response.code_lines if str(line).strip()]
    if not normalized_code:
        raise ValueError(f"Fill response for block {block.block_id!r} did not include any executable code lines.")

    allowed_method_calls = _STIMULUS_METHOD_CALLS if block.fill_kind == "stimulus" else _ORACLE_METHOD_CALLS
    allowed_function_calls = set(_SAFE_BUILTIN_CALLS)
    if block.fill_kind == "oracle_check":
        allowed_function_calls.update(_ORACLE_HELPER_CALLS)
    used_helper_calls = _validate_fill_ast(
        code_lines=normalized_code,
        fill_kind=block.fill_kind,
        allowed_method_calls=allowed_method_calls,
        allowed_function_calls=allowed_function_calls,
    )
    normalized = TodoFillResponse(
        block_id=response.block_id,
        code_lines=normalized_code,
        helper_calls=_normalize_text_list(response.helper_calls),
        assumptions=_normalize_text_list(response.assumptions),
        unresolved_items=_normalize_text_list(response.unresolved_items),
    )
    return normalized, {
        "used_helper_calls": sorted(used_helper_calls),
    }


def _validate_fill_ast(
    *,
    code_lines: list[str],
    fill_kind: str,
    allowed_method_calls: set[str],
    allowed_function_calls: set[str],
) -> set[str]:
    source = "\n".join(code_lines)
    tree = ast.parse(source, mode="exec")
    used_helpers: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, _FORBIDDEN_AST_NODES):
            raise ValueError(f"Unsupported AST node in {fill_kind} fill block: {node.__class__.__name__}.")
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise ValueError(f"Dunder attribute access is not allowed in {fill_kind} fill blocks: {node.attr!r}.")
        if isinstance(node, ast.Call):
            helper_name = _validate_call_node(
                node,
                fill_kind=fill_kind,
                allowed_method_calls=allowed_method_calls,
                allowed_function_calls=allowed_function_calls,
            )
            if helper_name:
                used_helpers.add(helper_name)
    return used_helpers


def _validate_call_node(
    node: ast.Call,
    *,
    fill_kind: str,
    allowed_method_calls: set[str],
    allowed_function_calls: set[str],
) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        if func.id in _DANGEROUS_CALLS:
            raise ValueError(f"Dangerous call is not allowed in {fill_kind} fill blocks: {func.id!r}.")
        if func.id not in allowed_function_calls:
            raise ValueError(f"Unsupported function call in {fill_kind} fill blocks: {func.id!r}.")
        return func.id

    if isinstance(func, ast.Attribute):
        owner = func.value
        if isinstance(owner, ast.Name) and owner.id in {"self", "env"}:
            if func.attr not in allowed_method_calls:
                raise ValueError(
                    f"Unsupported method call in {fill_kind} fill blocks: {owner.id}.{func.attr}()."
                )
            return func.attr
        if isinstance(owner, ast.Name) and func.attr in _SAFE_DICT_METHODS:
            return func.attr
        raise ValueError(f"Unsupported attribute call in {fill_kind} fill blocks: {ast.unparse(func)!r}.")

    raise ValueError(f"Unsupported callable form in {fill_kind} fill blocks: {ast.dump(func)}.")
