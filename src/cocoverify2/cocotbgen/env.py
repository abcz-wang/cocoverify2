"""Helpers for rendering cocotb environment modules."""

from __future__ import annotations

from pprint import pformat

from cocoverify2.cocotbgen.template_loader import render_template
from cocoverify2.cocotbgen.todo_blocks import build_todo_block
from cocoverify2.core.models import DUTContract, TestPlan
from cocoverify2.core.types import PortDirection

_ENV_TEMPLATE = "env_module.py.tmpl"


def render_env_module(
    contract: DUTContract,
    plan: TestPlan,
    *,
    temporal_modes_used: list[str],
    interface_module: str,
    coverage_module: str,
    runtime_module: str,
) -> tuple[str, dict[str, object]]:
    """Render the `<dut>_env.py` module content and summary."""
    class_name = f"{_camel(contract.module_name)}Env"
    interface_class = f"{_camel(contract.module_name)}Interface"
    coverage_class = f"{_camel(contract.module_name)}Coverage"
    plan_cases = {
        case.case_id: {
            "goal": case.goal,
            "category": case.category,
            "stimulus_intent": case.stimulus_intent,
            "stimulus_signals": case.stimulus_signals,
            "timing_assumptions": case.timing_assumptions,
            "dependencies": case.dependencies,
            "notes": case.notes,
            "coverage_tags": case.coverage_tags,
            "semantic_tags": case.semantic_tags,
        }
        for case in plan.cases
    }
    unresolved_items = _deduped(contract.ambiguities + plan.unresolved_items)
    helper_comment = "\n".join(f"# - {item}" for item in unresolved_items[:8]) or "# - none"
    wait_methods = ["wait_event_based", "wait_bounded_safe", "wait_unbounded_safe"]
    exact_cycle_block = ""
    exact_cycle_dispatch = ""
    if "exact_cycle" in temporal_modes_used:
        wait_methods.insert(0, "wait_exact_cycle")
        exact_cycle_block = '''
    async def wait_exact_cycle(self, cycles: int, label: str = "exact_cycle") -> None:
        """Wait an exact number of cycles only when the oracle explicitly permits it."""
        clock_name = self.interface.clock_name()
        if clock_name and self.interface.signal_exists(clock_name):
            clock_signal = self.interface.get_signal(clock_name)
            for _ in range(max(1, cycles)):
                await RisingEdge(clock_signal)
        else:
            await Timer(max(1, cycles), unit="ns")
        await ReadOnly()
'''
        exact_cycle_dispatch = (
            '        if mode == "exact_cycle":\n'
            '            await self.wait_exact_cycle(\n'
            '                int(temporal_window.get("max_cycles") or temporal_window.get("min_cycles") or 1),\n'
            '                label=label,\n'
            '            )\n'
            '            return\n'
        )

    business_inputs = _business_inputs(contract)
    business_outputs = _business_outputs(contract)
    signal_widths = {
        port.name: port.width if isinstance(port.width, int) else None
        for port in contract.ports
    }
    stimulus_dispatch_lines: list[str] = []
    stimulus_helper_blocks: list[str] = []
    llm_todo_blocks: list[dict[str, object]] = []
    for case in plan.cases:
        method_name = f"_todo_stimulus_{_sanitize_identifier(case.case_id)}"
        stimulus_dispatch_lines.extend(
            [
                f"        if case_id == {case.case_id!r}:",
                f"            await self.{method_name}()",
                "            return",
            ]
        )
        todo_block, todo_metadata = build_todo_block(
            fill_kind="stimulus",
            block_id=f"stimulus_{case.case_id}",
            template_name=_ENV_TEMPLATE,
            comment_lines=_stimulus_comment_lines(case=case, business_inputs=business_inputs),
            instructions=[
                "Drive concrete legal values onto business inputs for this plan case.",
                "Keep edits inside this TODO block so regeneration stays stable.",
                "Preserve conservative timing assumptions when exact behavior is unclear.",
            ],
            context={
                "business_inputs": list(business_inputs),
                "business_outputs": list(business_outputs),
                "case_id": case.case_id,
                "category": case.category,
                "goal": case.goal,
                "stimulus_intent": list(case.stimulus_intent),
                "stimulus_signals": list(case.stimulus_signals),
                "timing_assumptions": list(case.timing_assumptions),
                "semantic_tags": list(case.semantic_tags),
                "signal_widths": dict(signal_widths),
            },
            indent="        ",
            case_id=case.case_id,
        )
        llm_todo_blocks.append(todo_metadata)
        stimulus_helper_blocks.append(
            "\n".join(
                [
                    f"    async def {method_name}(self) -> None:",
                    f'        """LLM-fill stimulus hook for plan case `{case.case_id}`."""',
                    todo_block,
                ]
            )
        )

    if not stimulus_dispatch_lines:
        stimulus_dispatch_lines.append("        return")

    content = render_template(
        _ENV_TEMPLATE,
        module_name=contract.module_name,
        helper_comment=helper_comment,
        coverage_module=coverage_module,
        coverage_class=coverage_class,
        interface_module=interface_module,
        interface_class=interface_class,
        runtime_module=runtime_module,
        plan_cases_literal=pformat(plan_cases, sort_dicts=True),
        unresolved_items_literal=pformat(unresolved_items),
        signal_widths_literal=pformat(signal_widths, sort_dicts=True),
        business_outputs_literal=pformat(business_outputs),
        class_name=class_name,
        exact_cycle_block=exact_cycle_block,
        exact_cycle_dispatch=exact_cycle_dispatch,
        stimulus_dispatch_block="\n".join(stimulus_dispatch_lines),
        stimulus_helper_blocks=("\n\n".join(stimulus_helper_blocks) + "\n\n") if stimulus_helper_blocks else "",
    )
    summary = {
        "class_name": class_name,
        "wait_helpers": wait_methods,
        "has_reset_helper": bool(contract.resets),
        "case_count": len(plan.cases),
        "unresolved_items": unresolved_items,
        "template_name": _ENV_TEMPLATE,
        "llm_todo_blocks": llm_todo_blocks,
    }
    return content, summary


def _business_inputs(contract: DUTContract) -> list[str]:
    control_signals = set(contract.handshake_signals) | {clock.name for clock in contract.clocks} | {reset.name for reset in contract.resets}
    return [
        port.name
        for port in contract.ports
        if port.direction == PortDirection.INPUT and port.name not in control_signals
    ]


def _business_outputs(contract: DUTContract) -> list[str]:
    control_signals = set(contract.handshake_signals) | {clock.name for clock in contract.clocks} | {reset.name for reset in contract.resets}
    return [
        port.name
        for port in contract.ports
        if port.direction in {PortDirection.OUTPUT, PortDirection.INOUT} and port.name not in control_signals
    ]


def _stimulus_comment_lines(*, case, business_inputs: list[str]) -> list[str]:
    return [
        f"Inputs: {', '.join(business_inputs) if business_inputs else 'none'}",
        f"Stimulus signals: {', '.join(case.stimulus_signals) if getattr(case, 'stimulus_signals', None) else 'none'}",
        f"Goal: {case.goal}",
        "Guidance: Drive concrete legal values onto business inputs here.",
    ]


def _camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_")) or "Rendered"


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
