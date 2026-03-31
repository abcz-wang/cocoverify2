"""Environment helpers for `adder_bcd`.

This file is rendered from contract, plan, and oracle artifacts. It stays thin on
purpose: the environment only coordinates helpers and preserves unresolved items.

Environment notes:
# - Hybrid LLM plan augmentation failed; retained baseline rule-based coverage.
"""

from __future__ import annotations

from pprint import pformat

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, ReadWrite, RisingEdge, Timer

from .adder_bcd_coverage import AdderBcdCoverage
from .adder_bcd_interface import AdderBcdInterface
from .adder_bcd_runtime import normalize_driven_value, normalize_sampled_value

PLAN_CASES = {'basic_001': {'category': 'basic',
               'coverage_tags': ['basic', 'sanity', 'comb'],
               'defer_reason': '',
               'dependencies': [],
               'deterministic_stimulus_steps': [{'action': 'drive',
                                                 'signals': {'A': 1,
                                                             'B': 2,
                                                             'Cin': 0}},
                                                {'action': 'wait_for_settle'},
                                                {'action': 'record_inputs',
                                                 'signals': {'A': 1,
                                                             'B': 2,
                                                             'Cin': 0}}],
               'execution_policy': 'deterministic',
               'goal': 'Exercise representative legal input combinations and '
                       'observe output mapping.',
               'notes': ['Case intent is conservative when the contract is '
                         'weak or timing is unresolved.'],
               'scenario_kind': '',
               'semantic_tags': ['ambiguity_preserving'],
               'stimulus_intent': ['Drive a representative legal input pattern '
                                   "across known non-control inputs: ['A', "
                                   "'B', 'Cin']"],
               'stimulus_program': [],
               'stimulus_signals': ['A', 'B', 'Cin'],
               'timing_assumptions': ['Observe outputs after input '
                                      'stabilization.',
                                      'Do not infer internal state or '
                                      'undocumented storage.']},
 'edge_001': {'category': 'edge',
              'coverage_tags': ['edge', 'boundary'],
              'defer_reason': '',
              'dependencies': ['basic_001'],
              'deterministic_stimulus_steps': [{'action': 'drive',
                                                'signals': {'A': 15, 'B': 15}},
                                               {'action': 'wait_for_settle'},
                                               {'action': 'record_inputs',
                                                'signals': {'A': 15, 'B': 15}}],
              'execution_policy': 'deterministic',
              'goal': 'Exercise boundary-value and width-sensitive input '
                      'patterns.',
              'notes': ['Edge coverage remains value-oriented and avoids '
                        'fixed-latency assumptions.'],
              'scenario_kind': '',
              'semantic_tags': ['width_sensitive'],
              'stimulus_intent': ['Use zero-like, one-like, and boundary '
                                  "patterns on ['A', 'B']"],
              'stimulus_program': [],
              'stimulus_signals': ['A', 'B'],
              'timing_assumptions': ['Observe outputs after input '
                                     'stabilization.',
                                     'Do not infer internal state or '
                                     'undocumented storage.']}}
UNRESOLVED_ITEMS = ['Hybrid LLM plan augmentation failed; retained baseline rule-based coverage.']
SIGNAL_WIDTHS = {'A': 4, 'B': 4, 'Cin': 1, 'Cout': 1, 'Sum': 4}
CLOCK_SPECS = []
BUSINESS_OUTPUTS = ['Sum', 'Cout']


class AdderBcdEnv:
    """Thin environment container rendered from structured artifacts."""

    def __init__(self, dut) -> None:
        self.dut = dut
        self.interface = AdderBcdInterface(dut)
        self.coverage = AdderBcdCoverage()
        self.observation_log: list[dict[str, object]] = []
        self.case_inputs: dict[str, dict[str, object]] = {}
        self.case_stimulus_history: dict[str, list[dict[str, object]]] = {}
        self.case_observation_history: dict[str, list[dict[str, object]]] = {}
        self.case_notes: dict[str, list[str]] = {}
        self._last_driven_inputs: dict[str, object] = {}
        self._clock_tasks: list[object] = []

    async def initialize(self) -> None:
        """Bind interface signals before any case is exercised."""
        self.interface.bind_signals()
        await self._start_background_clocks()

    async def _start_background_clocks(self) -> None:
        """Start deterministic background clocks for resolved input clocks."""
        if self._clock_tasks:
            return
        for index, clock_spec in enumerate(CLOCK_SPECS):
            signal_name = str(clock_spec.get("name", ""))
            if not signal_name or not self.interface.signal_exists(signal_name):
                continue
            signal = self.interface.get_signal(signal_name)
            if signal is None:
                continue
            period_guess = clock_spec.get("period_ns_guess")
            period_ns = float(period_guess) if period_guess else float(10 + 2 * index)
            self._clock_tasks.append(cocotb.start_soon(Clock(signal, period_ns, unit="ns").start(start_high=False)))

    async def apply_reset_if_available(self) -> str | None:
        """Use all inferred resets conservatively when they exist."""
        reset_names = [
            signal_name
            for signal_name in self.interface.reset_names()
            if self.interface.signal_exists(signal_name) and self.interface.get_signal(signal_name) is not None
        ]
        if not reset_names:
            return None
        assert_values: dict[str, object] = {}
        release_values: dict[str, object] = {}
        for signal_name in self.interface.business_input_names():
            lowered = signal_name.lower()
            if lowered in {"en", "enable", "ce"} or lowered.endswith("_en"):
                assert_values[signal_name] = 1
                release_values[signal_name] = 1
        for reset_name in reset_names:
            active_level = 0 if reset_name.endswith("n") or reset_name.endswith("_n") else 1
            assert_values[reset_name] = active_level
            release_values[reset_name] = 1 - active_level
        await self.drive_inputs(**assert_values)
        await self.wait_event_based(label="reset_assert")
        await self.drive_inputs(**release_values)
        await self.wait_event_based(label="reset_release")
        return ",".join(reset_names)

    async def wait_event_based(self, label: str = "event_based") -> None:
        """Use event-based waiting as the default conservative observation path."""
        clock_names = [
            signal_name
            for signal_name in self.interface.clock_names()
            if self.interface.signal_exists(signal_name) and self.interface.get_signal(signal_name) is not None
        ]
        if clock_names:
            for clock_name in clock_names:
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

    def record_case_stimulus_step(self, case_id: str, step: dict[str, object]) -> None:
        """Persist a deterministic stimulus step so semantic checks can inspect input history."""
        signals = step.get("signals")
        normalized_step = {"action": str(step.get("action", ""))}
        if isinstance(signals, dict):
            normalized_step["signals"] = dict(signals)
        if "cycles" in step:
            normalized_step["cycles"] = int(step.get("cycles") or 1)
        if "text" in step:
            normalized_step["text"] = str(step.get("text") or "")
        self.case_stimulus_history.setdefault(case_id, []).append(normalized_step)

    def get_case_stimulus_history(self, case_id: str) -> list[dict[str, object]]:
        """Return the deterministic step history recorded for a plan case."""
        return [dict(step) for step in self.case_stimulus_history.get(case_id, [])]

    def record_case_observation(
        self,
        case_id: str,
        *,
        step_index: int,
        action: str,
        sampled_outputs: dict[str, object],
        cycle_index: int | None = None,
    ) -> None:
        """Persist sampled outputs taken during deterministic stimulus execution."""
        observation = {
            "step_index": int(step_index),
            "action": str(action),
            "sampled_outputs": dict(sampled_outputs),
            "driven_inputs": dict(self._last_driven_inputs),
        }
        if cycle_index is not None:
            observation["cycle_index"] = int(cycle_index)
        self.case_observation_history.setdefault(case_id, []).append(observation)

    def get_case_observation_history(self, case_id: str) -> list[dict[str, object]]:
        """Return sampled outputs collected during deterministic case execution."""
        return [dict(item) for item in self.case_observation_history.get(case_id, [])]

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
            reset_name = await self.apply_reset_if_available()
            if case.get("category") == "reset":
                self.record_case_inputs(case_id, {"__reset_signal__": reset_name or "none"})
        for intent in case.get("stimulus_intent", []):
            self.observation_log.append({
                "kind": "stimulus_intent",
                "case_id": case_id,
                "intent": intent,
            })
        if case.get("execution_policy") != "deterministic":
            self.record_case_note(case_id, case.get("defer_reason", "Case was rendered as non-executable in the deterministic mainline path."))
            return
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

    async def _todo_stimulus_basic_001(self) -> None:
        """LLM-fill stimulus hook for plan case `basic_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_001 case_id=basic_001
        # Inputs: A, B, Cin
        # Stimulus signals: A, B, Cin
        # Goal: Exercise representative legal input combinations and observe output mapping.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_001 case_id=basic_001
        if self.get_case_inputs('basic_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('basic_001')

    async def _todo_stimulus_edge_001(self) -> None:
        """LLM-fill stimulus hook for plan case `edge_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_edge_001 case_id=edge_001
        # Inputs: A, B, Cin
        # Stimulus signals: A, B
        # Goal: Exercise boundary-value and width-sensitive input patterns.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_edge_001 case_id=edge_001
        if self.get_case_inputs('edge_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('edge_001')

    def note_oracle_result(self, result: dict[str, object]) -> None:
        """Keep rendered oracle observations for later phases."""
        self.observation_log.append({"kind": "oracle_result", **result})

    async def _apply_deterministic_case(self, case_id: str) -> None:
        """Apply deterministic rule-based stimulus steps rendered for one case."""
        case = PLAN_CASES[case_id]
        for step_index, step in enumerate(case.get("deterministic_stimulus_steps", [])):
            action = step.get("action", "")
            self.record_case_stimulus_step(case_id, dict(step))
            if action == "drive":
                await self.drive_inputs(**dict(step.get("signals", {})))
                continue
            if action == "wait_for_settle":
                await self.wait_for_settle()
                self.record_case_observation(
                    case_id,
                    step_index=step_index,
                    action=action,
                    sampled_outputs=await self.sample_outputs(),
                )
                continue
            if action == "wait_cycles":
                cycles = int(step.get("cycles") or 1)
                for cycle_index in range(max(1, cycles)):
                    await self.wait_event_based(label=f"{case_id}_stimulus")
                    self.record_case_observation(
                        case_id,
                        step_index=step_index,
                        action=action,
                        cycle_index=cycle_index,
                        sampled_outputs=await self.sample_outputs(),
                    )
                continue
            if action == "record_inputs":
                self.record_case_inputs(case_id, dict(step.get("signals", {})))
                continue
            if action == "record_note":
                self.record_case_note(case_id, str(step.get("text", "")))
