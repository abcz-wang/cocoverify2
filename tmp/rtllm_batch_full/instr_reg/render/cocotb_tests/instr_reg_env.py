"""Environment helpers for `instr_reg`.

This file is rendered from contract, plan, and oracle artifacts. It stays thin on
purpose: the environment only coordinates helpers and preserves unresolved items.

Environment notes:
# - Reset polarity for 'clk' is unresolved.
"""

from __future__ import annotations

from pprint import pformat

import cocotb
from cocotb.triggers import ReadOnly, ReadWrite, RisingEdge, Timer

from .instr_reg_coverage import InstrRegCoverage
from .instr_reg_interface import InstrRegInterface
from .instr_reg_runtime import normalize_driven_value, normalize_sampled_value

PLAN_CASES = {'back_to_back_001': {'category': 'back_to_back',
                      'coverage_tags': ['back_to_back', 'repeated_operation'],
                      'dependencies': ['basic_001'],
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
                      'stimulus_signals': ['clk', 'rst', 'fetch'],
                      'timing_assumptions': ['Advance through conservative '
                                             'clocked observations.',
                                             'Do not assume completion before '
                                             'it becomes externally visible.']},
 'basic_001': {'category': 'basic',
               'coverage_tags': ['basic',
                                 'sanity',
                                 'seq',
                                 'operation_specific'],
               'dependencies': ['reset_001'],
               'goal': 'Confirm that a legal fetch updates the appropriate '
                       'stored instruction and drives correct output fields.',
               'notes': ['Case intent is conservative when the contract is '
                         'weak or timing is unresolved.',
                         'Conservative assumption: output reflects register '
                         'value after the same rising edge.'],
               'semantic_tags': ['ambiguity_preserving', 'operation_specific'],
               'stimulus_intent': ['Drive a representative legal input pattern '
                                   "across known inputs: ['clk', 'rst', "
                                   "'fetch', 'data']",
                                   'Drive a single fetch=01 with a known data '
                                   'pattern, then observe outputs.'],
               'stimulus_signals': ['clk', 'rst', 'fetch', 'data'],
               'timing_assumptions': ['Advance through conservative clocked '
                                      'observations.',
                                      'Do not assume completion before it '
                                      'becomes externally visible.',
                                      'Wait for one rising edge after stimulus '
                                      'before sampling outputs.']},
 'edge_001': {'category': 'edge',
              'coverage_tags': ['edge', 'boundary'],
              'dependencies': ['basic_001'],
              'goal': 'Exercise boundary-value and width-sensitive input '
                      'patterns.',
              'notes': ['Edge coverage remains value-oriented and avoids '
                        'fixed-latency assumptions.'],
              'semantic_tags': ['width_sensitive'],
              'stimulus_intent': ['Use zero-like, one-like, and boundary '
                                  "patterns on ['fetch', 'data']"],
              'stimulus_signals': ['fetch', 'data'],
              'timing_assumptions': ['Advance through conservative clocked '
                                     'observations.',
                                     'Do not assume completion before it '
                                     'becomes externally visible.']},
 'metamorphic_001': {'category': 'metamorphic',
                     'coverage_tags': ['equivalence', 'source_consistency'],
                     'dependencies': ['basic_001'],
                     'goal': 'Check equivalence of instruction representation '
                             'across sources.',
                     'notes': [],
                     'semantic_tags': ['operation_specific', 'width_sensitive'],
                     'stimulus_intent': ['Load an instruction via fetch=01, '
                                         'then load a different instruction '
                                         'via fetch=10, and verify that '
                                         'outputs reflect the most recent '
                                         'source appropriately.'],
                     'stimulus_signals': ['clk', 'rst', 'fetch', 'data'],
                     'timing_assumptions': ['Observe after each rising edge.']},
 'negative_001': {'category': 'negative',
                  'coverage_tags': ['illegal_input', 'reset'],
                  'dependencies': ['basic_001'],
                  'goal': "Verify module's robustness to undefined fetch "
                          'codes.',
                  'notes': ['Contract does not define behavior for '
                            "fetch=2'b11; we conservatively expect no state "
                            'change.'],
                  'semantic_tags': ['invalid_illegal_input',
                                    'ambiguity_preserving'],
                  'stimulus_intent': ['Drive illegal fetch value after a valid '
                                      'load and observe that outputs remain '
                                      'stable.'],
                  'stimulus_signals': ['clk', 'rst', 'fetch', 'data'],
                  'timing_assumptions': ['Observe outputs after at least one '
                                         'rising edge post stimulus.']},
 'regression_001': {'category': 'regression',
                    'coverage_tags': ['stress', 'random'],
                    'dependencies': ['basic_001', 'edge_001'],
                    'goal': 'Stress test with varied legal inputs to catch '
                            'hidden bugs.',
                    'notes': [],
                    'semantic_tags': ['operation_specific'],
                    'stimulus_intent': ['Apply a series of random legal '
                                        'fetch/data pairs across multiple '
                                        'clock cycles.'],
                    'stimulus_signals': ['clk', 'rst', 'fetch', 'data'],
                    'timing_assumptions': ['Allow at least one clock cycle '
                                           'between stimulus changes.']},
 'reset_001': {'category': 'reset',
               'coverage_tags': ['reset', 'initialization', 'stability'],
               'dependencies': [],
               'goal': 'Establish a stable post-reset baseline before '
                       'functional checking.',
               'notes': ['Reset polarity may still be heuristic if the '
                         'contract marks it ambiguous.'],
               'semantic_tags': ['ambiguity_preserving'],
               'stimulus_intent': ['Assert the detected reset using the '
                                   'inferred polarity.',
                                   'Release reset conservatively and observe '
                                   'interface stabilization.'],
               'stimulus_signals': ['rst'],
               'timing_assumptions': ['Advance through conservative clocked '
                                      'observations.',
                                      'Do not assume completion before it '
                                      'becomes externally visible.']}}
UNRESOLVED_ITEMS = ["Reset polarity for 'clk' is unresolved."]
SIGNAL_WIDTHS = {'ad1': 5, 'ad2': 8, 'clk': 1, 'data': 8, 'fetch': 2, 'ins': 3, 'rst': 1}
BUSINESS_OUTPUTS = ['ins', 'ad1', 'ad2']


class InstrRegEnv:
    """Thin environment container rendered from structured artifacts."""

    def __init__(self, dut) -> None:
        self.dut = dut
        self.interface = InstrRegInterface(dut)
        self.coverage = InstrRegCoverage()
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
        if case_id == 'regression_001':
            await self._todo_stimulus_regression_001()
            return
        if case_id == 'metamorphic_001':
            await self._todo_stimulus_metamorphic_001()
            return

    async def _todo_stimulus_reset_001(self) -> None:
        """LLM-fill stimulus hook for plan case `reset_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_reset_001 case_id=reset_001
        # Inputs: fetch, data
        # Stimulus signals: rst
        # Goal: Establish a stable post-reset baseline before functional checking.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_reset_001 case_id=reset_001

    async def _todo_stimulus_basic_001(self) -> None:
        """LLM-fill stimulus hook for plan case `basic_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_001 case_id=basic_001
        # Inputs: fetch, data
        # Stimulus signals: clk, rst, fetch, data
        # Goal: Confirm that a legal fetch updates the appropriate stored instruction and drives correct output fields.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_001 case_id=basic_001

    async def _todo_stimulus_edge_001(self) -> None:
        """LLM-fill stimulus hook for plan case `edge_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_edge_001 case_id=edge_001
        # Inputs: fetch, data
        # Stimulus signals: fetch, data
        # Goal: Exercise boundary-value and width-sensitive input patterns.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_edge_001 case_id=edge_001

    async def _todo_stimulus_back_to_back_001(self) -> None:
        """LLM-fill stimulus hook for plan case `back_to_back_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_back_to_back_001 case_id=back_to_back_001
        # Inputs: fetch, data
        # Stimulus signals: clk, rst, fetch
        # Goal: Observe repeated or back-to-back legal operations under conservative timing assumptions.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_back_to_back_001 case_id=back_to_back_001

    async def _todo_stimulus_negative_001(self) -> None:
        """LLM-fill stimulus hook for plan case `negative_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_negative_001 case_id=negative_001
        # Inputs: fetch, data
        # Stimulus signals: clk, rst, fetch, data
        # Goal: Verify module's robustness to undefined fetch codes.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_negative_001 case_id=negative_001

    async def _todo_stimulus_regression_001(self) -> None:
        """LLM-fill stimulus hook for plan case `regression_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_regression_001 case_id=regression_001
        # Inputs: fetch, data
        # Stimulus signals: clk, rst, fetch, data
        # Goal: Stress test with varied legal inputs to catch hidden bugs.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_regression_001 case_id=regression_001

    async def _todo_stimulus_metamorphic_001(self) -> None:
        """LLM-fill stimulus hook for plan case `metamorphic_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_metamorphic_001 case_id=metamorphic_001
        # Inputs: fetch, data
        # Stimulus signals: clk, rst, fetch, data
        # Goal: Check equivalence of instruction representation across sources.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_metamorphic_001 case_id=metamorphic_001

    def note_oracle_result(self, result: dict[str, object]) -> None:
        """Keep rendered oracle observations for later phases."""
        self.observation_log.append({"kind": "oracle_result", **result})
