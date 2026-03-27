"""Helpers for rendering structured oracle modules."""

from __future__ import annotations

import json
from collections import defaultdict
from pprint import pformat

from cocoverify2.core.models import DUTContract, OracleCase, OracleSpec


def render_oracle_module(contract: DUTContract, oracle: OracleSpec) -> tuple[str, dict[str, object]]:
    """Render the `<dut>_oracle.py` module content and summary."""
    module_name = contract.module_name
    control_signals = {clock.name for clock in contract.clocks} | {reset.name for reset in contract.resets}
    protocol_payload = [_sanitize_oracle_case(case, control_signals) for case in oracle.protocol_oracles]
    functional_payload = [_sanitize_oracle_case(case, control_signals) for case in oracle.functional_oracles]
    property_payload = [_sanitize_oracle_case(case, control_signals) for case in oracle.property_oracles]
    by_plan_case: dict[str, list[dict[str, object]]] = defaultdict(list)
    temporal_modes: set[str] = set()
    empty_functional_cases: list[str] = []

    for group_name, cases in (
        ("protocol", protocol_payload),
        ("functional", functional_payload),
        ("property", property_payload),
    ):
        for case in cases:
            case_copy = dict(case)
            case_copy["oracle_group"] = group_name
            by_plan_case[case["linked_plan_case_id"]].append(case_copy)
            for check in case["checks"]:
                temporal_modes.add(check["temporal_window"]["mode"])
            if group_name == "functional" and not case["checks"]:
                empty_functional_cases.append(case["linked_plan_case_id"])

    unresolved_items = _deduped(oracle.unresolved_items)
    content = f'''"""Oracle helpers for `{module_name}`.

This file is rendered from the structured oracle artifact. It intentionally keeps
checks conservative: timing windows are preserved, unresolved items stay visible,
and control signals are never reintroduced as business outputs.
"""

from __future__ import annotations

import json
from typing import Any

CONTROL_SIGNALS = {pformat(sorted(control_signals))}
ORACLE_SPEC = json.loads({json.dumps(json.dumps(_build_oracle_payload(protocol_payload, functional_payload, property_payload), indent=2, sort_keys=True))})
ORACLE_CASES_BY_PLAN = json.loads({json.dumps(json.dumps(dict(by_plan_case), indent=2, sort_keys=True))})
TEMPORAL_MODES = {pformat(sorted(temporal_modes))}
UNRESOLVED_ITEMS = {pformat(unresolved_items)}


def linked_oracle_case_ids_for_plan_case(plan_case_id: str) -> list[str]:
    """Return rendered oracle-case ids linked to a plan case."""
    return [case["case_id"] for case in ORACLE_CASES_BY_PLAN.get(plan_case_id, [])]


async def run_linked_plan_case(env, plan_case_id: str) -> list[dict[str, Any]]:
    """Invoke all oracle helpers associated with a rendered test-plan case."""
    results: list[dict[str, Any]] = []
    for oracle_case in ORACLE_CASES_BY_PLAN.get(plan_case_id, []):
        results.append(await _run_oracle_case(env, oracle_case))
    return results


async def _run_oracle_case(env, oracle_case: dict[str, Any]) -> dict[str, Any]:
    """Run the rendered checks for one oracle case."""
    case_results: list[dict[str, Any]] = []
    for check in oracle_case.get("checks", []):
        case_results.append(await _evaluate_check(env, oracle_case["case_id"], check))
    return {{
        "case_id": oracle_case["case_id"],
        "linked_plan_case_id": oracle_case["linked_plan_case_id"],
        "oracle_group": oracle_case.get("oracle_group", "unknown"),
        "check_count": len(case_results),
        "results": case_results,
        "unresolved_items": list(oracle_case.get("unresolved_items", [])),
        "notes": list(oracle_case.get("notes", [])),
    }}


async def _evaluate_check(env, oracle_case_id: str, check: dict[str, Any]) -> dict[str, Any]:
    """Apply the rendered wait/observation helper that matches one oracle check."""
    temporal_window = dict(check.get("temporal_window", {{}}))
    await env.wait_for_window(temporal_window, label=check["check_id"])
    observed_signals = [signal for signal in check.get("observed_signals", []) if signal not in CONTROL_SIGNALS]
    env.coverage.record_oracle_check(check["check_id"], check["check_type"], check["strictness"])
    result = {{
        "oracle_case_id": oracle_case_id,
        "check_id": check["check_id"],
        "check_type": check["check_type"],
        "strictness": check["strictness"],
        "description": check["description"],
        "trigger_condition": check.get("trigger_condition", ""),
        "pass_condition": check.get("pass_condition", ""),
        "observed_signals": observed_signals,
        "temporal_window": temporal_window,
        "status": "rendered_check_invoked",
        "notes": list(check.get("notes", [])),
    }}
    env.note_oracle_result(result)
    return result
'''
    summary = {
        "protocol_case_count": len(protocol_payload),
        "functional_case_count": len(functional_payload),
        "property_case_count": len(property_payload),
        "temporal_modes": sorted(temporal_modes),
        "empty_functional_cases": empty_functional_cases,
        "unresolved_items": unresolved_items,
    }
    return content, summary


def _build_oracle_payload(
    protocol_payload: list[dict[str, object]],
    functional_payload: list[dict[str, object]],
    property_payload: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "protocol_oracles": protocol_payload,
        "functional_oracles": functional_payload,
        "property_oracles": property_payload,
    }


def _sanitize_oracle_case(case: OracleCase, control_signals: set[str]) -> dict[str, object]:
    payload = case.model_dump(mode="json")
    for check in payload["checks"]:
        check["observed_signals"] = [signal for signal in check["observed_signals"] if signal not in control_signals]
    return payload


def _deduped(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items
