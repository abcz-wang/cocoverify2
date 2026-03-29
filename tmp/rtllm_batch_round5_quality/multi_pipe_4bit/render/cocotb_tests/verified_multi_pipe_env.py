"""Environment helpers for `verified_multi_pipe`.

This file is rendered from contract, plan, and oracle artifacts. It stays thin on
purpose: the environment only coordinates helpers and preserves unresolved items.

Environment notes:
# - none
"""

from __future__ import annotations

from pprint import pformat

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ReadOnly, ReadWrite, RisingEdge, Timer

from .verified_multi_pipe_coverage import VerifiedMultiPipeCoverage
from .verified_multi_pipe_interface import VerifiedMultiPipeInterface
from .verified_multi_pipe_runtime import normalize_driven_value, normalize_sampled_value

PLAN_CASES = {'back_to_back_001': {'category': 'back_to_back',
                      'coverage_tags': ['back_to_back', 'repeated_operation'],
                      'defer_reason': '',
                      'dependencies': ['basic_001'],
                      'deterministic_stimulus_steps': [{'action': 'drive',
                                                        'signals': {'mul_a': 0,
                                                                    'mul_b': 1}},
                                                       {'action': 'wait_cycles',
                                                        'cycles': 1},
                                                       {'action': 'drive',
                                                        'signals': {'mul_a': 1,
                                                                    'mul_b': 1}},
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
                      'stimulus_signals': ['mul_a', 'mul_b'],
                      'timing_assumptions': ['Advance through conservative '
                                             'clocked observations.',
                                             'Do not assume completion before '
                                             'it becomes externally visible.']},
 'basic_001': {'category': 'basic',
               'coverage_tags': ['basic', 'sanity', 'seq', 'functional'],
               'defer_reason': '',
               'dependencies': ['reset_001'],
               'deterministic_stimulus_steps': [{'action': 'drive',
                                                 'signals': {'mul_a': 0,
                                                             'mul_b': 1}},
                                                {'action': 'wait_cycles'}],
               'execution_policy': 'deterministic',
               'goal': 'Validate functional correctness of the multiplier for '
                       'a random legal input pair',
               'notes': ['Case intent is conservative when the contract is '
                         'weak or timing is unresolved.',
                         'Uses random stimulus within the defined input width',
                         'Observes mul_out until it stabilizes after the '
                         'operation'],
               'semantic_tags': ['ambiguity_preserving', 'operation_specific'],
               'stimulus_intent': ['Drive a representative legal input pattern '
                                   "across known non-control inputs: ['mul_a', "
                                   "'mul_b']",
                                   'Drive random values to mul_a and mul_b and '
                                   'monitor mul_out for correct product'],
               'stimulus_signals': ['mul_a', 'mul_b'],
               'timing_assumptions': ['Advance through conservative clocked '
                                      'observations.',
                                      'Do not assume completion before it '
                                      'becomes externally visible.',
                                      'Allow multiple clock cycles after '
                                      'stimulus before checking mul_out '
                                      'stability']},
 'edge_001': {'category': 'edge',
              'coverage_tags': ['edge', 'boundary'],
              'defer_reason': '',
              'dependencies': ['basic_001'],
              'deterministic_stimulus_steps': [{'action': 'drive',
                                                'signals': {'mul_a': 1,
                                                            'mul_b': 1}},
                                               {'action': 'wait_cycles'}],
              'execution_policy': 'deterministic',
              'goal': 'Exercise boundary-value and width-sensitive input '
                      'patterns.',
              'notes': ['Edge coverage remains value-oriented and avoids '
                        'fixed-latency assumptions.'],
              'semantic_tags': ['width_sensitive'],
              'stimulus_intent': ['Use zero-like, one-like, and boundary '
                                  "patterns on ['mul_a', 'mul_b']"],
              'stimulus_signals': ['mul_a', 'mul_b'],
              'timing_assumptions': ['Advance through conservative clocked '
                                     'observations.',
                                     'Do not assume completion before it '
                                     'becomes externally visible.']},
 'metamorphic_001': {'category': 'metamorphic',
                     'coverage_tags': ['metamorphic', 'commutative'],
                     'defer_reason': '',
                     'dependencies': ['basic_001'],
                     'deterministic_stimulus_steps': [{'action': 'drive',
                                                       'signals': {'mul_a': 0,
                                                                   'mul_b': 1}},
                                                      {'action': 'wait_cycles'}],
                     'execution_policy': 'deterministic',
                     'goal': 'Validate the commutative property of unsigned '
                             'multiplication',
                     'notes': ['Uses two input pairs that are permutations of '
                               'each other'],
                     'semantic_tags': ['operation_specific'],
                     'stimulus_intent': ['Apply (mul_a = A, mul_b = B), '
                                         'capture mul_out, then apply (mul_a = '
                                         'B, mul_b = A) and compare outputs'],
                     'stimulus_signals': ['mul_a', 'mul_b'],
                     'timing_assumptions': ['Allow sufficient clock cycles '
                                            'after each stimulus for mul_out '
                                            'to stabilize before comparison']},
 'negative_001': {'category': 'negative',
                  'coverage_tags': ['negative', 'robustness'],
                  'defer_reason': 'Negative cases require stronger structured '
                                  'illegal-input semantics than the current '
                                  'contract provides.',
                  'dependencies': ['basic_001'],
                  'deterministic_stimulus_steps': [],
                  'execution_policy': 'deferred',
                  'goal': 'Check handling of unknown/invalid input values on '
                          'mul_a and mul_b',
                  'notes': ['Contract does not define illegal input behavior; '
                            'this case probes implementation robustness',
                            'Negative cases require stronger structured '
                            'illegal-input semantics than the current contract '
                            'provides.'],
                  'semantic_tags': ['invalid_illegal_input'],
                  'stimulus_intent': ['Drive X (unknown) to mul_a while '
                                      'providing a valid value to mul_b'],
                  'stimulus_signals': ['mul_a', 'mul_b'],
                  'timing_assumptions': ['Observe mul_out over several clock '
                                         'cycles to see if it reflects the '
                                         'unknown input']},
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
UNRESOLVED_ITEMS = []
SIGNAL_WIDTHS = {'clk': 1, 'mul_a': None, 'mul_b': None, 'mul_out': None, 'rst_n': 1}
CLOCK_SPECS = [{'confidence': 0.95, 'name': 'clk', 'period_ns_guess': None}]
BUSINESS_OUTPUTS = ['mul_out']


class VerifiedMultiPipeEnv:
    """Thin environment container rendered from structured artifacts."""

    def __init__(self, dut) -> None:
        self.dut = dut
        self.interface = VerifiedMultiPipeInterface(dut)
        self.coverage = VerifiedMultiPipeCoverage()
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
        if case_id == 'back_to_back_001':
            await self._todo_stimulus_back_to_back_001()
            return
        if case_id == 'negative_001':
            await self._todo_stimulus_negative_001()
            return
        if case_id == 'metamorphic_001':
            await self._todo_stimulus_metamorphic_001()
            return

    async def _todo_stimulus_reset_001(self) -> None:
        """LLM-fill stimulus hook for plan case `reset_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_reset_001 case_id=reset_001
        # Inputs: mul_a, mul_b
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
        # Inputs: mul_a, mul_b
        # Stimulus signals: mul_a, mul_b
        # Goal: Validate functional correctness of the multiplier for a random legal input pair
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_001 case_id=basic_001
        if self.get_case_inputs('basic_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('basic_001')

    async def _todo_stimulus_edge_001(self) -> None:
        """LLM-fill stimulus hook for plan case `edge_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_edge_001 case_id=edge_001
        # Inputs: mul_a, mul_b
        # Stimulus signals: mul_a, mul_b
        # Goal: Exercise boundary-value and width-sensitive input patterns.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_edge_001 case_id=edge_001
        if self.get_case_inputs('edge_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('edge_001')

    async def _todo_stimulus_back_to_back_001(self) -> None:
        """LLM-fill stimulus hook for plan case `back_to_back_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_back_to_back_001 case_id=back_to_back_001
        # Inputs: mul_a, mul_b
        # Stimulus signals: mul_a, mul_b
        # Goal: Observe repeated or back-to-back legal operations under conservative timing assumptions.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_back_to_back_001 case_id=back_to_back_001
        if self.get_case_inputs('back_to_back_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('back_to_back_001')

    async def _todo_stimulus_negative_001(self) -> None:
        """LLM-fill stimulus hook for plan case `negative_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_negative_001 case_id=negative_001
        # Inputs: mul_a, mul_b
        # Stimulus signals: mul_a, mul_b
        # Goal: Check handling of unknown/invalid input values on mul_a and mul_b
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_negative_001 case_id=negative_001
        if self.get_case_inputs('negative_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('negative_001')

    async def _todo_stimulus_metamorphic_001(self) -> None:
        """LLM-fill stimulus hook for plan case `metamorphic_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_metamorphic_001 case_id=metamorphic_001
        # Inputs: mul_a, mul_b
        # Stimulus signals: mul_a, mul_b
        # Goal: Validate the commutative property of unsigned multiplication
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_metamorphic_001 case_id=metamorphic_001
        if self.get_case_inputs('metamorphic_001') or self._last_driven_inputs:
            return
        await self._apply_deterministic_case('metamorphic_001')

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
