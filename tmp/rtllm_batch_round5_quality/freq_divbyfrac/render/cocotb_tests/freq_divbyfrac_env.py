"""Environment helpers for `freq_divbyfrac`.

This file is rendered from contract, plan, and oracle artifacts. It stays thin on
purpose: the environment only coordinates helpers and preserves unresolved items.

Environment notes:
# - Golden interface described clock 'clk_div', but the RTL port is not a scalar input-like signal.
# - Reset polarity for 'clk' is unresolved.
"""

from __future__ import annotations

from pprint import pformat

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, ReadWrite, RisingEdge, Timer

from .freq_divbyfrac_coverage import FreqDivbyfracCoverage
from .freq_divbyfrac_interface import FreqDivbyfracInterface
from .freq_divbyfrac_runtime import normalize_driven_value, normalize_sampled_value

PLAN_CASES = {'basic_001': {'category': 'basic',
               'coverage_tags': ['basic',
                                 'sanity',
                                 'seq',
                                 'fractional_division',
                                 'duty_cycle',
                                 'stability'],
               'defer_reason': '',
               'dependencies': ['reset_001'],
               'deterministic_stimulus_steps': [{'action': 'record_note',
                                                 'text': 'Deterministic '
                                                         'mainline case relies '
                                                         'on clock-driven '
                                                         'observation because '
                                                         'no non-control '
                                                         'inputs were '
                                                         'resolved.'},
                                                {'action': 'wait_cycles',
                                                 'cycles': 2},
                                                {'action': 'record_inputs',
                                                 'signals': {'__clock_progress__': 2}}],
               'execution_policy': 'deterministic',
               'goal': 'Validate fractional division behavior and duty cycle '
                       'of clk_div',
               'notes': ['Case intent is conservative when the contract is '
                         'weak or timing is unresolved.',
                         'Case relies on deterministic clock-driven '
                         'observation because no non-control inputs were '
                         'resolved.',
                         'Observe over multiple division periods to capture '
                         'half-cycle behavior'],
               'semantic_tags': ['ambiguity_preserving', 'operation_specific'],
               'stimulus_intent': ['Release reset if present and observe a '
                                   'small number of conservative clock edges '
                                   'for externally visible progress.',
                                   'Release reset and let the module run for '
                                   'sufficient cycles'],
               'stimulus_signals': [],
               'timing_assumptions': ['Advance through conservative clocked '
                                      'observations.',
                                      'Do not assume completion before it '
                                      'becomes externally visible.',
                                      'Observe for at least 14 input clock '
                                      'cycles (two full division cycles)']},
 'basic_002': {'category': 'basic',
               'coverage_tags': ['reset_pulse', 'robustness'],
               'defer_reason': '',
               'dependencies': ['reset_001'],
               'deterministic_stimulus_steps': [{'action': 'record_note',
                                                 'text': 'Deterministic '
                                                         'mainline case relies '
                                                         'on clock-driven '
                                                         'observation because '
                                                         'no non-control '
                                                         'inputs were '
                                                         'resolved.'},
                                                {'action': 'wait_cycles',
                                                 'cycles': 2},
                                                {'action': 'record_inputs',
                                                 'signals': {'__clock_progress__': 2}}],
               'execution_policy': 'deterministic',
               'goal': "Test module's ability to handle brief reset pulses",
               'notes': ['Case relies on deterministic clock-driven '
                         'observation because no non-control inputs were '
                         'resolved.'],
               'semantic_tags': ['ambiguity_preserving'],
               'stimulus_intent': ['Apply a short low pulse on rst_n (active '
                                   'low) then release'],
               'stimulus_signals': [],
               'timing_assumptions': ['Pulse width of 2 clock cycles, observe '
                                      'for 30 cycles after release']},
 'edge_001': {'category': 'edge',
              'coverage_tags': ['reset_edge', 'asynchronous'],
              'defer_reason': '',
              'dependencies': ['reset_001'],
              'deterministic_stimulus_steps': [{'action': 'record_note',
                                                'text': 'Deterministic '
                                                        'mainline case relies '
                                                        'on clock-driven '
                                                        'observation because '
                                                        'no non-control inputs '
                                                        'were resolved.'},
                                               {'action': 'wait_cycles',
                                                'cycles': 2},
                                               {'action': 'record_inputs',
                                                'signals': {'__clock_progress__': 2}}],
              'execution_policy': 'deterministic',
              'goal': 'Verify correct behavior when reset is released off a '
                      'clock edge',
              'notes': ['Helps ensure reset release timing does not cause '
                        'metastability',
                        'Case relies on deterministic clock-driven observation '
                        'because no non-control inputs were resolved.'],
              'semantic_tags': ['ambiguity_preserving'],
              'stimulus_intent': ['Assert reset, then deassert it at a '
                                  'non-clock-aligned moment'],
              'stimulus_signals': [],
              'timing_assumptions': ['Observe for at least 20 input clock '
                                     'cycles after reset release']},
 'reset_001': {'category': 'reset',
               'coverage_tags': ['reset', 'initialization', 'stability'],
               'defer_reason': '',
               'dependencies': [],
               'deterministic_stimulus_steps': [{'action': 'record_inputs',
                                                 'signals': {'__reset_only__': True}}],
               'execution_policy': 'deterministic',
               'goal': 'Establish a stable post-reset baseline before '
                       'functional checking.',
               'notes': ['Reset polarity may still be heuristic if the '
                         'contract marks it ambiguous.'],
               'semantic_tags': ['ambiguity_preserving'],
               'stimulus_intent': ['Assert the detected reset using the '
                                   'inferred polarity.',
                                   'Release reset conservatively and observe '
                                   'interface stabilization.'],
               'stimulus_signals': ['rst_n'],
               'timing_assumptions': ['Advance through conservative clocked '
                                      'observations.',
                                      'Do not assume completion before it '
                                      'becomes externally visible.']}}
UNRESOLVED_ITEMS = ["Golden interface described clock 'clk_div', but the RTL port is not a scalar "
 'input-like signal.',
 "Reset polarity for 'clk' is unresolved."]
SIGNAL_WIDTHS = {'clk': 1, 'clk_div': 1, 'rst_n': 1}
CLOCK_SPECS = [{'confidence': 0.95, 'name': 'clk', 'period_ns_guess': None}]
BUSINESS_OUTPUTS = ['clk_div']


class FreqDivbyfracEnv:
    """Thin environment container rendered from structured artifacts."""

    def __init__(self, dut) -> None:
        self.dut = dut
        self.interface = FreqDivbyfracInterface(dut)
        self.coverage = FreqDivbyfracCoverage()
        self.observation_log: list[dict[str, object]] = []
        self.case_inputs: dict[str, dict[str, object]] = {}
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
        if case_id == 'reset_001':
            await self._todo_stimulus_reset_001()
            return
        if case_id == 'basic_001':
            await self._todo_stimulus_basic_001()
            return
        if case_id == 'edge_001':
            await self._todo_stimulus_edge_001()
            return
        if case_id == 'basic_002':
            await self._todo_stimulus_basic_002()
            return

    async def _todo_stimulus_reset_001(self) -> None:
        """LLM-fill stimulus hook for plan case `reset_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_reset_001 case_id=reset_001
        # Inputs: none
        # Stimulus signals: rst_n
        # Goal: Establish a stable post-reset baseline before functional checking.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_reset_001 case_id=reset_001
        if self.get_case_inputs('reset_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('reset_001')

    async def _todo_stimulus_basic_001(self) -> None:
        """LLM-fill stimulus hook for plan case `basic_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_001 case_id=basic_001
        # Inputs: none
        # Stimulus signals: none
        # Goal: Validate fractional division behavior and duty cycle of clk_div
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_001 case_id=basic_001
        if self.get_case_inputs('basic_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('basic_001')

    async def _todo_stimulus_edge_001(self) -> None:
        """LLM-fill stimulus hook for plan case `edge_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_edge_001 case_id=edge_001
        # Inputs: none
        # Stimulus signals: none
        # Goal: Verify correct behavior when reset is released off a clock edge
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_edge_001 case_id=edge_001
        if self.get_case_inputs('edge_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('edge_001')

    async def _todo_stimulus_basic_002(self) -> None:
        """LLM-fill stimulus hook for plan case `basic_002`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_002 case_id=basic_002
        # Inputs: none
        # Stimulus signals: none
        # Goal: Test module's ability to handle brief reset pulses
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_002 case_id=basic_002
        if self.get_case_inputs('basic_002') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('basic_002')

    def note_oracle_result(self, result: dict[str, object]) -> None:
        """Keep rendered oracle observations for later phases."""
        self.observation_log.append({"kind": "oracle_result", **result})

    async def _apply_deterministic_case(self, case_id: str) -> None:
        """Apply deterministic rule-based stimulus steps rendered for one case."""
        case = PLAN_CASES[case_id]
        for step in case.get("deterministic_stimulus_steps", []):
            action = step.get("action", "")
            if action == "drive":
                await self.drive_inputs(**dict(step.get("signals", {})))
                continue
            if action == "wait_for_settle":
                await self.wait_for_settle()
                continue
            if action == "wait_cycles":
                await self.wait_bounded_safe(int(step.get("cycles") or 1), label=f"{case_id}_stimulus")
                continue
            if action == "record_inputs":
                self.record_case_inputs(case_id, dict(step.get("signals", {})))
                continue
            if action == "record_note":
                self.record_case_note(case_id, str(step.get("text", "")))
