"""Helpers for rendering cocotb environment modules."""

from __future__ import annotations

from pprint import pformat

from cocoverify2.core.models import DUTContract, TestPlan


def render_env_module(
    contract: DUTContract,
    plan: TestPlan,
    *,
    temporal_modes_used: list[str],
    interface_module: str,
    coverage_module: str,
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
            "timing_assumptions": case.timing_assumptions,
            "dependencies": case.dependencies,
            "notes": case.notes,
            "coverage_tags": case.coverage_tags,
        }
        for case in plan.cases
    }
    unresolved_items = _deduped(contract.ambiguities + plan.unresolved_items)
    helper_comment = "\n".join(f"# - {item}" for item in unresolved_items[:8]) or "# - none"
    wait_methods = ["wait_event_based", "wait_bounded_safe", "wait_unbounded_safe"]
    exact_cycle_block = ""
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
    content = f'''"""Environment helpers for `{contract.module_name}`.

This file is rendered from contract, plan, and oracle artifacts. It stays thin on
purpose: the environment only coordinates helpers and preserves unresolved items.

Environment notes:
{helper_comment}
"""

from __future__ import annotations

from pprint import pformat

import cocotb
from cocotb.triggers import ReadOnly, RisingEdge, Timer

from .{coverage_module} import {coverage_class}
from .{interface_module} import {interface_class}

PLAN_CASES = {pformat(plan_cases, sort_dicts=True)}
UNRESOLVED_ITEMS = {pformat(unresolved_items)}


class {class_name}:
    """Thin environment container rendered from structured artifacts."""

    def __init__(self, dut) -> None:
        self.dut = dut
        self.interface = {interface_class}(dut)
        self.coverage = {coverage_class}()
        self.observation_log: list[dict[str, object]] = []

    async def initialize(self) -> None:
        """Bind interface signals before any case is exercised."""
        self.interface.bind_signals()

    async def apply_reset_if_available(self) -> None:
        """Use the inferred reset conservatively when one exists."""
        reset_name = self.interface.reset_name()
        if reset_name is None or not self.interface.signal_exists(reset_name):
            return
        reset_signal = self.interface.get_signal(reset_name)
        if reset_signal is None:
            return
        active_level = 0 if reset_name.endswith("n") or reset_name.endswith("_n") else 1
        reset_signal.value = active_level
        await self.wait_event_based(label="reset_assert")
        reset_signal.value = 1 - active_level
        await self.wait_event_based(label="reset_release")

{exact_cycle_block}    async def wait_event_based(self, label: str = "event_based") -> None:
        """Use event-based waiting as the default conservative observation path."""
        clock_name = self.interface.clock_name()
        if clock_name and self.interface.signal_exists(clock_name):
            clock_signal = self.interface.get_signal(clock_name)
            await RisingEdge(clock_signal)
        else:
            await Timer(1, unit="ns")
        await ReadOnly()

    async def wait_bounded_safe(self, max_cycles: int | None, label: str = "bounded_safe") -> None:
        """Advance through a bounded-safe observation window without assuming exact semantics."""
        steps = max(1, int(max_cycles or 1))
        for _ in range(steps):
            await self.wait_event_based(label=label)

    async def wait_unbounded_safe(self, label: str = "unbounded_safe") -> None:
        """Use one conservative observation step for a safety-style wait."""
        await self.wait_event_based(label=label)

    async def wait_for_window(self, temporal_window: dict[str, object], label: str = "window") -> None:
        """Dispatch to the rendered wait helper that matches the oracle temporal mode."""
        mode = temporal_window.get("mode", "event_based")
        if mode == "bounded_range":
            await self.wait_bounded_safe(temporal_window.get("max_cycles"), label=label)
            return
        if mode == "unbounded_safe":
            await self.wait_unbounded_safe(label=label)
            return
'''
    if "exact_cycle" in temporal_modes_used:
        content += '''        if mode == "exact_cycle":
            await self.wait_exact_cycle(int(temporal_window.get("max_cycles") or temporal_window.get("min_cycles") or 1), label=label)
            return
'''
    content += '''        await self.wait_event_based(label=label)

    async def safe_observe(self, case_id: str) -> None:
        """Record timing assumptions and take one conservative observation step."""
        case = PLAN_CASES[case_id]
        self.observation_log.append({
            "kind": "timing_assumptions",
            "case_id": case_id,
            "timing_assumptions": list(case.get("timing_assumptions", [])),
        })
        await self.wait_event_based(label=case_id)

    async def exercise_case(self, case_id: str) -> None:
        """Record the rendered stimulus intent without inventing new semantics."""
        case = PLAN_CASES[case_id]
        if case.get("category") == "reset" or "reset_001" in case.get("dependencies", []):
            await self.apply_reset_if_available()
        for intent in case.get("stimulus_intent", []):
            self.observation_log.append({
                "kind": "stimulus_intent",
                "case_id": case_id,
                "intent": intent,
            })
        await self.safe_observe(case_id)

    def note_oracle_result(self, result: dict[str, object]) -> None:
        """Keep rendered oracle observations for later phases."""
        self.observation_log.append({"kind": "oracle_result", **result})
'''
    summary = {
        "class_name": class_name,
        "wait_helpers": wait_methods,
        "has_reset_helper": bool(contract.resets),
        "case_count": len(plan.cases),
        "unresolved_items": unresolved_items,
    }
    return content, summary


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
