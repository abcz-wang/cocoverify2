"""Helpers for rendering structured oracle modules."""

from __future__ import annotations

import json
from collections import defaultdict
from pprint import pformat

from cocoverify2.cocotbgen.template_loader import render_template
from cocoverify2.cocotbgen.todo_blocks import build_todo_block
from cocoverify2.core.models import DUTContract, OracleCase, OracleSpec

_ORACLE_TEMPLATE = "oracle_module.py.tmpl"


def render_oracle_module(
    contract: DUTContract,
    oracle: OracleSpec,
    *,
    runtime_module: str,
) -> tuple[str, dict[str, object]]:
    """Render the `<dut>_oracle.py` module content and summary."""
    module_name = contract.module_name
    control_signals = {clock.name for clock in contract.clocks} | {reset.name for reset in contract.resets}
    signal_widths = {
        port.name: port.width if isinstance(port.width, int) else None
        for port in contract.ports
    }
    protocol_payload = [_sanitize_oracle_case(case, control_signals) for case in oracle.protocol_oracles]
    functional_payload = [_sanitize_oracle_case(case, control_signals) for case in oracle.functional_oracles]
    property_payload = [_sanitize_oracle_case(case, control_signals) for case in oracle.property_oracles]
    by_plan_case: dict[str, list[dict[str, object]]] = defaultdict(list)
    temporal_modes: set[str] = set()
    empty_functional_cases: list[str] = []
    llm_todo_blocks: list[dict[str, object]] = []
    oracle_dispatch_lines: list[str] = []
    oracle_helper_blocks: list[str] = []

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
                function_name = f"_todo_oracle_{_sanitize_identifier(check['check_id'])}"
                oracle_dispatch_lines.extend(
                    [
                        f"    if check.get(\"check_id\") == {check['check_id']!r}:",
                        f"        await {function_name}(env, plan_case_id, oracle_case_id, check, observed_signals)",
                        "        return",
                    ]
                )
                todo_block, todo_metadata = build_todo_block(
                    fill_kind="oracle_check",
                    block_id=f"oracle_{check['check_id']}",
                    template_name=_ORACLE_TEMPLATE,
                    comment_lines=[
                        f"Observed signals: {', '.join(check['observed_signals']) if check['observed_signals'] else 'none'}",
                        f"Pass condition: {check.get('pass_condition', '')}",
                        "Guidance: Read DUT outputs and add concrete assertions here.",
                    ],
                    instructions=[
                        "Read observable DUT outputs and add concrete assertions for this oracle check.",
                        "Keep edits inside this TODO block so regeneration stays stable.",
                        "Respect the rendered temporal window and strictness metadata.",
                    ],
                    context={
                        "observed_signals": list(check["observed_signals"]),
                        "signal_policies": dict(check.get("signal_policies", {})),
                        "trigger_condition": check.get("trigger_condition", ""),
                        "pass_condition": check.get("pass_condition", ""),
                        "strictness": check.get("strictness", ""),
                        "temporal_window": dict(check.get("temporal_window", {})),
                        "semantic_tags": list(check.get("semantic_tags", [])),
                        "signal_widths": dict(signal_widths),
                    },
                    indent="    ",
                    case_id=case["linked_plan_case_id"],
                    oracle_case_id=case["case_id"],
                    check_id=check["check_id"],
                )
                llm_todo_blocks.append(todo_metadata)
                oracle_helper_blocks.append(
                    "\n".join(
                        [
                            f"async def {function_name}(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:",
                            f'    """LLM-fill oracle hook for check `{check["check_id"]}`."""',
                            todo_block,
                        ]
                    )
                )
            if group_name == "functional" and not case["checks"]:
                empty_functional_cases.append(case["linked_plan_case_id"])

    unresolved_items = _deduped(oracle.unresolved_items)
    if not oracle_dispatch_lines:
        oracle_dispatch_lines.append("    return")

    content = render_template(
        _ORACLE_TEMPLATE,
        module_name=module_name,
        runtime_module=runtime_module,
        control_signals_literal=pformat(sorted(control_signals)),
        signal_widths_literal=pformat(signal_widths, sort_dicts=True),
        oracle_spec_literal=json.dumps(json.dumps(_build_oracle_payload(protocol_payload, functional_payload, property_payload), indent=2, sort_keys=True)),
        oracle_cases_by_plan_literal=json.dumps(json.dumps(dict(by_plan_case), indent=2, sort_keys=True)),
        temporal_modes_literal=pformat(sorted(temporal_modes)),
        unresolved_items_literal=pformat(unresolved_items),
        oracle_dispatch_block="\n".join(oracle_dispatch_lines),
        oracle_helper_blocks="\n\n".join(oracle_helper_blocks),
    )
    summary = {
        "protocol_case_count": len(protocol_payload),
        "functional_case_count": len(functional_payload),
        "property_case_count": len(property_payload),
        "temporal_modes": sorted(temporal_modes),
        "empty_functional_cases": empty_functional_cases,
        "unresolved_items": unresolved_items,
        "template_name": _ORACLE_TEMPLATE,
        "llm_todo_blocks": llm_todo_blocks,
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


def _sanitize_identifier(name: str) -> str:
    sanitized = "".join(char if char.isalnum() or char == "_" else "_" for char in name)
    if sanitized and sanitized[0].isdigit():
        return f"case_{sanitized}"
    return sanitized or "rendered_case"
