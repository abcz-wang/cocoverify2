"""Environment helpers for `verified_alu`.

This file is rendered from contract, plan, and oracle artifacts. It stays thin on
purpose: the environment only coordinates helpers and preserves unresolved items.

Environment notes:
# - none
"""

from __future__ import annotations

from pprint import pformat

import cocotb
from cocotb.triggers import ReadOnly, RisingEdge, Timer

from .verified_alu_coverage import VerifiedAluCoverage
from .verified_alu_interface import VerifiedAluInterface

PLAN_CASES = {'basic_001': {'category': 'basic',
               'coverage_tags': ['basic', 'sanity', 'comb'],
               'dependencies': [],
               'goal': 'Exercise representative legal input combinations and '
                       'observe output mapping.',
               'notes': ['Case intent is conservative when the contract is '
                         'weak or timing is unresolved.'],
               'stimulus_intent': ['Drive a representative legal input pattern '
                                   "across known inputs: ['a', 'b', 'aluc']"],
               'timing_assumptions': ['Observe outputs after input '
                                      'stabilization.',
                                      'Do not infer internal state or '
                                      'undocumented storage.']},
 'edge_001': {'category': 'edge',
              'coverage_tags': ['edge', 'boundary'],
              'dependencies': ['basic_001'],
              'goal': 'Exercise boundary-value and width-sensitive input '
                      'patterns.',
              'notes': ['Edge coverage remains value-oriented and avoids '
                        'fixed-latency assumptions.'],
              'stimulus_intent': ['Use zero-like, one-like, and boundary '
                                  "patterns on ['a', 'b', 'aluc']"],
              'timing_assumptions': ['Observe outputs after input '
                                     'stabilization.',
                                     'Do not infer internal state or '
                                     'undocumented storage.']}}
UNRESOLVED_ITEMS = []


class VerifiedAluEnv:
    """Thin environment container rendered from structured artifacts."""

    def __init__(self, dut) -> None:
        self.dut = dut
        self.interface = VerifiedAluInterface(dut)
        self.coverage = VerifiedAluCoverage()
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

    async def wait_event_based(self, label: str = "event_based") -> None:
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
        await self.wait_event_based(label=label)

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
        await self._apply_stimulus_todo(case_id)
        await self.safe_observe(case_id)

    async def _apply_stimulus_todo(self, case_id: str) -> None:
        """Dispatch per-case LLM-fill stimulus hooks."""
        if case_id == 'basic_001':
            await self._todo_stimulus_basic_001()
            return
        if case_id == 'edge_001':
            await self._todo_stimulus_edge_001()
            return

    async def _todo_stimulus_basic_001(self) -> None:
        """LLM-fill stimulus hook for plan case `basic_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_001 case_id=basic_001
        # Inputs: a, b, aluc
        # Goal: Exercise representative legal input combinations and observe output mapping.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_001 case_id=basic_001

    async def _todo_stimulus_edge_001(self) -> None:
        """LLM-fill stimulus hook for plan case `edge_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_edge_001 case_id=edge_001
        # Inputs: a, b, aluc
        # Goal: Exercise boundary-value and width-sensitive input patterns.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_edge_001 case_id=edge_001

    def note_oracle_result(self, result: dict[str, object]) -> None:
        """Keep rendered oracle observations for later phases."""
        self.observation_log.append({"kind": "oracle_result", **result})
