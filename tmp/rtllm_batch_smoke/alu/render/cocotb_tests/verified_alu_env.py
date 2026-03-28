"""Environment helpers for `verified_alu`.

This file is rendered from contract, plan, and oracle artifacts. It stays thin on
purpose: the environment only coordinates helpers and preserves unresolved items.

Environment notes:
# - none
"""

from __future__ import annotations

from pprint import pformat

import cocotb
from cocotb.triggers import ReadOnly, ReadWrite, RisingEdge, Timer

from .verified_alu_coverage import VerifiedAluCoverage
from .verified_alu_interface import VerifiedAluInterface
from .verified_alu_runtime import normalize_driven_value, normalize_sampled_value

PLAN_CASES = {'basic_001': {'category': 'basic',
               'coverage_tags': ['basic',
                                 'sanity',
                                 'comb',
                                 'operation_specific'],
               'dependencies': [],
               'goal': 'Validate correct combinational behavior for all '
                       'defined opcodes with representative operands',
               'notes': ['Case intent is conservative when the contract is '
                         'weak or timing is unresolved.',
                         'Conservative stimulus; does not assume any internal '
                         'pipeline or latency'],
               'semantic_tags': ['ambiguity_preserving', 'operation_specific'],
               'stimulus_intent': ['Drive a representative legal input pattern '
                                   "across known inputs: ['a', 'b', 'aluc']",
                                   'Drive a, b, and aluc with typical legal '
                                   'values covering each opcode'],
               'stimulus_signals': ['a', 'b', 'aluc'],
               'timing_assumptions': ['Observe outputs after input '
                                      'stabilization.',
                                      'Do not infer internal state or '
                                      'undocumented storage.',
                                      'Outputs are sampled after inputs '
                                      'settle; no clock edge required']},
 'basic_002': {'category': 'basic',
               'coverage_tags': ['operation_specific'],
               'dependencies': ['basic_001'],
               'goal': 'Targeted verification of ADD and ADDU behavior across '
                       'representative operand values',
               'notes': ['Focuses on signed vs unsigned addition semantics'],
               'semantic_tags': ['operation_specific'],
               'stimulus_intent': ['Drive a and b with positive, negative, and '
                                   'zero values while aluc is set to ADD or '
                                   'ADDU'],
               'stimulus_signals': ['a', 'b', 'aluc'],
               'timing_assumptions': ['Observe outputs after inputs have '
                                      'stabilized; no clock required']},
 'edge_001': {'category': 'edge',
              'coverage_tags': ['edge', 'boundary', 'width_sensitive'],
              'dependencies': ['basic_001'],
              'goal': 'Exercise boundary‑value and width‑sensitive scenarios '
                      'for arithmetic and shift operations',
              'notes': ['Edge coverage remains value-oriented and avoids '
                        'fixed-latency assumptions.',
                        'Focuses on extreme operand values and shift amounts '
                        'without assuming timing'],
              'semantic_tags': ['width_sensitive'],
              'stimulus_intent': ['Use zero-like, one-like, and boundary '
                                  "patterns on ['a', 'b', 'aluc']",
                                  'Apply zero, all‑ones, max/min signed, and '
                                  'max shift amounts to a, b, and aluc'],
              'stimulus_signals': ['a', 'b', 'aluc'],
              'timing_assumptions': ['Observe outputs after input '
                                     'stabilization.',
                                     'Do not infer internal state or '
                                     'undocumented storage.',
                                     'Observe outputs after inputs have '
                                     'stabilized; combinational latency '
                                     'abstracted']},
 'edge_002': {'category': 'edge',
              'coverage_tags': ['boundary'],
              'dependencies': ['edge_001'],
              'goal': 'Edge verification of carry and overflow generation for '
                      'extreme operand values',
              'notes': ['Uses max/min signed and unsigned values to provoke '
                        'boundary conditions'],
              'semantic_tags': ['width_sensitive'],
              'stimulus_intent': ['Apply max unsigned, min signed, and max '
                                  'signed operand pairs with ADD and SUB '
                                  'opcodes'],
              'stimulus_signals': ['a', 'b', 'aluc'],
              'timing_assumptions': ['Observe outputs after inputs have '
                                     'stabilized; combinational latency is '
                                     'abstracted']},
 'negative_001': {'category': 'negative',
                  'coverage_tags': ['invalid_illegal_input'],
                  'dependencies': [],
                  'goal': 'Validate ALU response to undefined opcode values',
                  'notes': ['Ensures that the default case of the ALU produces '
                            'high‑impedance outputs as specified'],
                  'semantic_tags': ['invalid_illegal_input'],
                  'stimulus_intent': ['Drive aluc with values outside the '
                                      'defined opcode set while providing '
                                      'arbitrary a and b'],
                  'stimulus_signals': ['a', 'b', 'aluc'],
                  'timing_assumptions': ['Observe outputs after inputs have '
                                         'stabilized; no sequential timing '
                                         'assumed']}}
UNRESOLVED_ITEMS = []
SIGNAL_WIDTHS = {'a': 32,
 'aluc': 6,
 'b': 32,
 'carry': 1,
 'flag': 1,
 'negative': 1,
 'overflow': 1,
 'r': 32,
 'zero': 1}
BUSINESS_OUTPUTS = ['r', 'zero', 'carry', 'negative', 'overflow', 'flag']


class VerifiedAluEnv:
    """Thin environment container rendered from structured artifacts."""

    def __init__(self, dut) -> None:
        self.dut = dut
        self.interface = VerifiedAluInterface(dut)
        self.coverage = VerifiedAluCoverage()
        self.observation_log: list[dict[str, object]] = []
        self.case_inputs: dict[str, dict[str, object]] = {}
        self.case_notes: dict[str, list[str]] = {}
        self._last_driven_inputs: dict[str, object] = {}

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

    def signal_width(self, signal_name: str) -> int | None:
        """Return the rendered signal width when it is statically known."""
        width = SIGNAL_WIDTHS.get(signal_name)
        return int(width) if isinstance(width, int) else None

    async def drive_inputs(self, **signals) -> None:
        """Drive one or more known business inputs onto the DUT."""
        try:
            await ReadWrite()
        except RuntimeError as exc:
            if "ReadOnly phase" not in str(exc):
                raise
            # LLM-filled stimulus blocks may sample outputs before issuing the next
            # drive. Advance one simulator step so writes resume from a legal phase.
            await Timer(1, unit="step")
            await ReadWrite()
        applied: dict[str, object] = {}
        for signal_name, raw_value in signals.items():
            signal = self.interface.get_signal(signal_name)
            if signal is None:
                raise AssertionError(f"Unknown or unbound input signal: {signal_name}")
            normalized_value = normalize_driven_value(raw_value, self.signal_width(signal_name))
            signal.value = normalized_value
            applied[signal_name] = normalized_value
        if applied:
            self._last_driven_inputs.update(applied)

    async def wait_for_settle(self) -> None:
        """Take one conservative settle step after driving inputs."""
        await self.wait_event_based(label="settle")

    def record_case_inputs(self, case_id: str, signals: dict[str, object]) -> None:
        """Persist the concrete inputs that were applied for a rendered case."""
        self.case_inputs[case_id] = dict(signals)

    def get_case_inputs(self, case_id: str) -> dict[str, object]:
        """Return the recorded applied inputs for a plan case."""
        return dict(self.case_inputs.get(case_id, {}))

    def record_case_note(self, case_id: str, text: str) -> None:
        """Attach a lightweight note to a rendered case execution."""
        self.case_notes.setdefault(case_id, []).append(str(text))

    async def sample_outputs(self, names=None) -> dict[str, object]:
        """Sample the current output values into int-or-string form."""
        selected_names = list(names or BUSINESS_OUTPUTS)
        observed: dict[str, object] = {}
        for signal_name in selected_names:
            signal = self.interface.get_signal(signal_name)
            if signal is None:
                continue
            observed[signal_name] = normalize_sampled_value(signal.value, self.signal_width(signal_name))
        return observed

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
        self._last_driven_inputs = {}
        await self._apply_stimulus_todo(case_id)
        if case_id not in self.case_inputs and self._last_driven_inputs:
            self.record_case_inputs(case_id, self._last_driven_inputs)
        await self.safe_observe(case_id)

    async def _apply_stimulus_todo(self, case_id: str) -> None:
        """Dispatch per-case LLM-fill stimulus hooks."""
        if case_id == 'basic_001':
            await self._todo_stimulus_basic_001()
            return
        if case_id == 'edge_001':
            await self._todo_stimulus_edge_001()
            return
        if case_id == 'basic_002':
            await self._todo_stimulus_basic_002()
            return
        if case_id == 'edge_002':
            await self._todo_stimulus_edge_002()
            return
        if case_id == 'negative_001':
            await self._todo_stimulus_negative_001()
            return

    async def _todo_stimulus_basic_001(self) -> None:
        """LLM-fill stimulus hook for plan case `basic_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_001 case_id=basic_001
        # Inputs: a, b, aluc
        # Stimulus signals: a, b, aluc
        # Goal: Validate correct combinational behavior for all defined opcodes with representative operands
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_001 case_id=basic_001

    async def _todo_stimulus_edge_001(self) -> None:
        """LLM-fill stimulus hook for plan case `edge_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_edge_001 case_id=edge_001
        # Inputs: a, b, aluc
        # Stimulus signals: a, b, aluc
        # Goal: Exercise boundary‑value and width‑sensitive scenarios for arithmetic and shift operations
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_edge_001 case_id=edge_001

    async def _todo_stimulus_basic_002(self) -> None:
        """LLM-fill stimulus hook for plan case `basic_002`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_002 case_id=basic_002
        # Inputs: a, b, aluc
        # Stimulus signals: a, b, aluc
        # Goal: Targeted verification of ADD and ADDU behavior across representative operand values
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_002 case_id=basic_002

    async def _todo_stimulus_edge_002(self) -> None:
        """LLM-fill stimulus hook for plan case `edge_002`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_edge_002 case_id=edge_002
        # Inputs: a, b, aluc
        # Stimulus signals: a, b, aluc
        # Goal: Edge verification of carry and overflow generation for extreme operand values
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_edge_002 case_id=edge_002

    async def _todo_stimulus_negative_001(self) -> None:
        """LLM-fill stimulus hook for plan case `negative_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_negative_001 case_id=negative_001
        # Inputs: a, b, aluc
        # Stimulus signals: a, b, aluc
        # Goal: Validate ALU response to undefined opcode values
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_negative_001 case_id=negative_001

    def note_oracle_result(self, result: dict[str, object]) -> None:
        """Keep rendered oracle observations for later phases."""
        self.observation_log.append({"kind": "oracle_result", **result})
