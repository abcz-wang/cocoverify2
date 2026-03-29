"""Environment helpers for `verified_parallel2serial`.

This file is rendered from contract, plan, and oracle artifacts. It stays thin on
purpose: the environment only coordinates helpers and preserves unresolved items.

Environment notes:
# - Detected valid_ready-like signal(s) ['valid_out'] without matching role(s) ['ready'] in group 'out'.
# - Spec/reset hint could not be mapped to a known reset port: The most significant bit of the parallel input is assigned to the serial output (dout). On each clock cycle, if the counter (cnt) is 3, indicating the last bit of the parallel input, the module updates the data register (data) with the parallel input (d), resets the counter (cnt) to 0, and sets the valid signal (valid) to 1.
# - valid_ready ambiguity for valid_out without a matching ready signal.
# - Exact latency of valid_out assertion relative to input d is unspecified.
"""

from __future__ import annotations

from pprint import pformat

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, ReadWrite, RisingEdge, Timer

from .verified_parallel2serial_coverage import VerifiedParallel2serialCoverage
from .verified_parallel2serial_interface import VerifiedParallel2serialInterface
from .verified_parallel2serial_runtime import normalize_driven_value, normalize_sampled_value

PLAN_CASES = {'back_to_back_001': {'category': 'back_to_back',
                      'coverage_tags': ['back_to_back', 'repeated_operation'],
                      'defer_reason': '',
                      'dependencies': ['basic_001'],
                      'deterministic_stimulus_steps': [{'action': 'drive',
                                                        'signals': {'d': 1}},
                                                       {'action': 'wait_cycles',
                                                        'cycles': 1},
                                                       {'action': 'drive',
                                                        'signals': {'d': 15}},
                                                       {'action': 'wait_cycles',
                                                        'cycles': 1}],
                      'execution_policy': 'deterministic',
                      'goal': 'Observe repeated or back-to-back legal '
                              'operations under conservative timing '
                              'assumptions.',
                      'notes': ['When timing is unresolved, this case stays '
                                'unresolved-safe and does not require '
                                'deterministic overlap behavior.'],
                      'semantic_tags': ['operation_specific'],
                      'stimulus_intent': ['Apply two legal operations with '
                                          'minimal idle spacing that remains '
                                          'safe for the current contract '
                                          'strength.'],
                      'stimulus_signals': ['d'],
                      'timing_assumptions': ['Advance through conservative '
                                             'clocked observations.',
                                             'Do not assume completion before '
                                             'it becomes externally visible.']},
 'basic_001': {'category': 'basic',
               'coverage_tags': ['basic', 'sanity', 'seq', 'functional'],
               'defer_reason': '',
               'dependencies': ['reset_001'],
               'deterministic_stimulus_steps': [{'action': 'drive',
                                                 'signals': {'d': 1}},
                                                {'action': 'wait_cycles'}],
               'execution_policy': 'deterministic',
               'goal': 'Confirm that a single legal parallel word produces a '
                       'correct serial stream and a single valid_out pulse '
                       'under conservative timing.',
               'notes': ['Case intent is conservative when the contract is '
                         'weak or timing is unresolved.',
                         'The observation window extends for at least five '
                         'clock cycles after stimulus to capture the full word '
                         'without assuming a fixed latency.'],
               'semantic_tags': ['ambiguity_preserving'],
               'stimulus_intent': ['Drive a representative legal input pattern '
                                   "across known non-control inputs: ['d']",
                                   'Drive a nominal 4‑bit pattern (e.g., '
                                   '0b1010) on d while reset is de‑asserted.'],
               'stimulus_signals': ['d'],
               'timing_assumptions': ['Advance through conservative clocked '
                                      'observations.',
                                      'Do not assume completion before it '
                                      'becomes externally visible.',
                                      'Advance clock cycle‑by‑cycle and sample '
                                      'outputs after each rising edge; do not '
                                      'assume a fixed number of cycles before '
                                      'valid_out appears.']},
 'edge_001': {'category': 'edge',
              'coverage_tags': ['edge', 'boundary', 'value_patterns'],
              'defer_reason': '',
              'dependencies': ['basic_001'],
              'deterministic_stimulus_steps': [{'action': 'drive',
                                                'signals': {'d': 15}},
                                               {'action': 'wait_cycles'}],
              'execution_policy': 'deterministic',
              'goal': 'Exercise extreme and mixed bit‑patterns to verify '
                      'width‑sensitive behavior without relying on exact '
                      'latency.',
              'notes': ['Edge coverage remains value-oriented and avoids '
                        'fixed-latency assumptions.',
                        'Each stimulus is held for enough cycles to allow the '
                        'previous word to finish before the next is applied.'],
              'semantic_tags': ['width_sensitive'],
              'stimulus_intent': ['Use zero-like, one-like, and boundary '
                                  "patterns on ['d']",
                                  'Apply boundary patterns (0x0, 0xF, 0x1, '
                                  '0x8) on d sequentially.'],
              'stimulus_signals': ['d'],
              'timing_assumptions': ['Advance through conservative clocked '
                                     'observations.',
                                     'Do not assume completion before it '
                                     'becomes externally visible.',
                                     'Observe outputs over a conservative '
                                     'window of 6+ clock cycles after each '
                                     'pattern.']},
 'negative_001': {'category': 'negative',
                  'coverage_tags': ['illegal_input'],
                  'defer_reason': 'Negative cases require stronger structured '
                                  'illegal-input semantics than the current '
                                  'contract provides.',
                  'dependencies': ['basic_001'],
                  'deterministic_stimulus_steps': [],
                  'execution_policy': 'deferred',
                  'goal': 'Observe module behavior under illegal/undefined '
                          'input values while respecting contract ambiguity.',
                  'notes': ['The contract does not define illegal input '
                            'constraints; this case explores the natural '
                            'Verilog X‑propagation semantics.',
                            'Negative cases require stronger structured '
                            'illegal-input semantics than the current contract '
                            'provides.'],
                  'semantic_tags': ['invalid_illegal_input'],
                  'stimulus_intent': ['Drive d with a value containing X/Z '
                                      "bits (e.g., 4'b1x0z) and monitor "
                                      'outputs.'],
                  'stimulus_signals': ['d'],
                  'timing_assumptions': ['Observe for at least five clock '
                                         'cycles after stimulus; no fixed '
                                         'latency assumed.']},
 'protocol_001': {'category': 'protocol',
                  'coverage_tags': ['valid_pulse_protocol'],
                  'defer_reason': '',
                  'dependencies': ['basic_001'],
                  'deterministic_stimulus_steps': [{'action': 'drive',
                                                    'signals': {'d': 1}},
                                                   {'action': 'wait_cycles',
                                                    'cycles': 1}],
                  'execution_policy': 'deterministic',
                  'goal': 'Validate the implicit valid‑ready protocol implied '
                          'by valid_out without assuming a ready signal.',
                  'notes': ['The test drives a second d value two cycles after '
                            'the first word start to check that valid_out does '
                            'not pulse prematurely.'],
                  'semantic_tags': ['ambiguity_preserving'],
                  'stimulus_intent': ['Apply first word 0b1100 on d, then '
                                      'after two clock cycles apply second '
                                      'word 0b0011 while the first word is '
                                      'still in progress.'],
                  'stimulus_signals': ['d'],
                  'timing_assumptions': ['Sample valid_out and dout each '
                                         'rising edge; do not assume a fixed '
                                         "latency for the second word's "
                                         'valid_out.']},
 'regression_001': {'category': 'regression',
                    'coverage_tags': ['repeated_sequence'],
                    'defer_reason': 'Advanced derived cases were downgraded '
                                    'because the contract does not yet justify '
                                    'deterministic mainline semantics.',
                    'dependencies': ['back_to_back_001'],
                    'deterministic_stimulus_steps': [],
                    'execution_policy': 'deferred',
                    'goal': 'Stress the design with multiple consecutive words '
                            'to ensure state does not corrupt over time.',
                    'notes': ['The test reuses the stimulus pattern from '
                              'basic_001 but repeats it many times without '
                              'idle cycles.',
                              'Advanced derived cases were downgraded because '
                              'the contract does not yet justify deterministic '
                              'mainline semantics.'],
                    'semantic_tags': ['operation_specific'],
                    'stimulus_intent': ['Apply a series of alternating '
                                        'patterns (0b1010, 0b0101) on d each '
                                        'cycle without gaps.'],
                    'stimulus_signals': ['d'],
                    'timing_assumptions': ['Sample each clock edge; do not '
                                           'assume a fixed latency between '
                                           'words.']},
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
UNRESOLVED_ITEMS = ["Detected valid_ready-like signal(s) ['valid_out'] without matching role(s) "
 "['ready'] in group 'out'.",
 'Spec/reset hint could not be mapped to a known reset port: The most '
 'significant bit of the parallel input is assigned to the serial output '
 '(dout). On each clock cycle, if the counter (cnt) is 3, indicating the last '
 'bit of the parallel input, the module updates the data register (data) with '
 'the parallel input (d), resets the counter (cnt) to 0, and sets the valid '
 'signal (valid) to 1.',
 'valid_ready ambiguity for valid_out without a matching ready signal.',
 'Exact latency of valid_out assertion relative to input d is unspecified.']
SIGNAL_WIDTHS = {'clk': 1, 'd': 4, 'dout': 1, 'rst_n': 1, 'valid_out': 1}
CLOCK_SPECS = [{'confidence': 0.95, 'name': 'clk', 'period_ns_guess': None}]
BUSINESS_OUTPUTS = ['valid_out', 'dout']


class VerifiedParallel2serialEnv:
    """Thin environment container rendered from structured artifacts."""

    def __init__(self, dut) -> None:
        self.dut = dut
        self.interface = VerifiedParallel2serialInterface(dut)
        self.coverage = VerifiedParallel2serialCoverage()
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
        if case_id == 'back_to_back_001':
            await self._todo_stimulus_back_to_back_001()
            return
        if case_id == 'protocol_001':
            await self._todo_stimulus_protocol_001()
            return
        if case_id == 'negative_001':
            await self._todo_stimulus_negative_001()
            return
        if case_id == 'regression_001':
            await self._todo_stimulus_regression_001()
            return

    async def _todo_stimulus_reset_001(self) -> None:
        """LLM-fill stimulus hook for plan case `reset_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_reset_001 case_id=reset_001
        # Inputs: d
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
        # Inputs: d
        # Stimulus signals: d
        # Goal: Confirm that a single legal parallel word produces a correct serial stream and a single valid_out pulse under conservative timing.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_001 case_id=basic_001
        if self.get_case_inputs('basic_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('basic_001')

    async def _todo_stimulus_edge_001(self) -> None:
        """LLM-fill stimulus hook for plan case `edge_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_edge_001 case_id=edge_001
        # Inputs: d
        # Stimulus signals: d
        # Goal: Exercise extreme and mixed bit‑patterns to verify width‑sensitive behavior without relying on exact latency.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_edge_001 case_id=edge_001
        if self.get_case_inputs('edge_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('edge_001')

    async def _todo_stimulus_back_to_back_001(self) -> None:
        """LLM-fill stimulus hook for plan case `back_to_back_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_back_to_back_001 case_id=back_to_back_001
        # Inputs: d
        # Stimulus signals: d
        # Goal: Observe repeated or back-to-back legal operations under conservative timing assumptions.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_back_to_back_001 case_id=back_to_back_001
        if self.get_case_inputs('back_to_back_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('back_to_back_001')

    async def _todo_stimulus_protocol_001(self) -> None:
        """LLM-fill stimulus hook for plan case `protocol_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_protocol_001 case_id=protocol_001
        # Inputs: d
        # Stimulus signals: d
        # Goal: Validate the implicit valid‑ready protocol implied by valid_out without assuming a ready signal.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_protocol_001 case_id=protocol_001
        if self.get_case_inputs('protocol_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('protocol_001')

    async def _todo_stimulus_negative_001(self) -> None:
        """LLM-fill stimulus hook for plan case `negative_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_negative_001 case_id=negative_001
        # Inputs: d
        # Stimulus signals: d
        # Goal: Observe module behavior under illegal/undefined input values while respecting contract ambiguity.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_negative_001 case_id=negative_001
        if self.get_case_inputs('negative_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('negative_001')

    async def _todo_stimulus_regression_001(self) -> None:
        """LLM-fill stimulus hook for plan case `regression_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_regression_001 case_id=regression_001
        # Inputs: d
        # Stimulus signals: d
        # Goal: Stress the design with multiple consecutive words to ensure state does not corrupt over time.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_regression_001 case_id=regression_001
        if self.get_case_inputs('regression_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('regression_001')

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
