"""Environment helpers for `verified_RAM`.

This file is rendered from contract, plan, and oracle artifacts. It stays thin on
purpose: the environment only coordinates helpers and preserves unresolved items.

Environment notes:
# - Reset polarity for 'clk' is unresolved.
# - Reset polarity for 'clk' remains ambiguous; tests assume active‑low reset on rst_n and treat clk as a regular clock without reset polarity.
"""

from __future__ import annotations

from pprint import pformat

import cocotb
from cocotb.triggers import ReadOnly, ReadWrite, RisingEdge, Timer

from .verified_RAM_coverage import VerifiedRamCoverage
from .verified_RAM_interface import VerifiedRamInterface
from .verified_RAM_runtime import normalize_driven_value, normalize_sampled_value

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
                      'stimulus_signals': ['clk', 'rst_n', 'write_en'],
                      'timing_assumptions': ['Advance through conservative '
                                             'clocked observations.',
                                             'Do not assume completion before '
                                             'it becomes externally visible.']},
 'basic_001': {'category': 'basic',
               'coverage_tags': ['basic', 'sanity', 'seq', 'concurrent_rw'],
               'dependencies': ['reset_001'],
               'goal': 'Apply representative legal operations, including '
                       'simultaneous but independent read and write, and '
                       'verify stable post‑operation behavior.',
               'notes': ['Case intent is conservative when the contract is '
                         'weak or timing is unresolved.',
                         'The enrichment adds explicit focus on concurrent '
                         'read/write to distinct addresses while preserving '
                         'the original basic intent.'],
               'semantic_tags': ['ambiguity_preserving', 'operation_specific'],
               'stimulus_intent': ['Drive a representative legal input pattern '
                                   "across known inputs: ['clk', 'rst_n', "
                                   "'write_en', 'write_addr', 'write_data', "
                                   "'read_en', 'read_addr']",
                                   'Drive a write transaction to a chosen '
                                   'address while concurrently driving a read '
                                   'transaction to a different address, then '
                                   'observe read_data after one clock edge.'],
               'stimulus_signals': ['clk',
                                    'rst_n',
                                    'write_en',
                                    'write_addr',
                                    'write_data',
                                    'read_en',
                                    'read_addr'],
               'timing_assumptions': ['Advance through conservative clocked '
                                      'observations.',
                                      'Do not assume completion before it '
                                      'becomes externally visible.',
                                      'Observe read_data after one clock edge '
                                      'following stimulus; do not assume any '
                                      'fixed latency beyond this conservative '
                                      'window.']},
 'basic_002': {'category': 'basic',
               'coverage_tags': ['concurrent_rw'],
               'dependencies': ['basic_001'],
               'goal': 'Validate behavior of simultaneous read and write '
                       'operations to the same address under ambiguous timing.',
               'notes': ['The contract does not specify write‑before‑read or '
                         'read‑before‑write ordering, so the check is limited '
                         'to stability and absence of X.'],
               'semantic_tags': ['operation_specific', 'ambiguity_preserving'],
               'stimulus_intent': ['Assert write_en=1 and read_en=1 with '
                                   'identical write_addr and read_addr, '
                                   'cycling write_data through distinct '
                                   'patterns.'],
               'stimulus_signals': ['clk',
                                    'rst_n',
                                    'write_en',
                                    'write_addr',
                                    'write_data',
                                    'read_en',
                                    'read_addr'],
               'timing_assumptions': ['Observe read_data after one clock edge '
                                      'following stimulus; no fixed‑cycle '
                                      'latency is assumed.']},
 'edge_001': {'category': 'edge',
              'coverage_tags': ['edge', 'boundary'],
              'dependencies': ['basic_001'],
              'goal': 'Exercise boundary-value and width-sensitive input '
                      'patterns.',
              'notes': ['Edge coverage remains value-oriented and avoids '
                        'fixed-latency assumptions.'],
              'semantic_tags': ['width_sensitive'],
              'stimulus_intent': ['Use zero-like, one-like, and boundary '
                                  "patterns on ['write_addr', 'write_data', "
                                  "'read_addr']"],
              'stimulus_signals': ['write_addr', 'write_data', 'read_addr'],
              'timing_assumptions': ['Advance through conservative clocked '
                                     'observations.',
                                     'Do not assume completion before it '
                                     'becomes externally visible.']},
 'edge_002': {'category': 'edge',
              'coverage_tags': ['address_boundary'],
              'dependencies': ['edge_001'],
              'goal': 'Exercise address extremes for both read and write '
                      'ports.',
              'notes': [],
              'semantic_tags': ['width_sensitive'],
              'stimulus_intent': ['Write distinct data patterns to address 0 '
                                  'and address 7, then read back each '
                                  'address.'],
              'stimulus_signals': ['clk',
                                   'rst_n',
                                   'write_en',
                                   'write_addr',
                                   'write_data',
                                   'read_en',
                                   'read_addr'],
              'timing_assumptions': ['Allow one clock cycle after each write '
                                     'before the corresponding read; no exact '
                                     'latency is assumed.']},
 'negative_001': {'category': 'negative',
                  'coverage_tags': ['illegal_input'],
                  'dependencies': ['basic_001'],
                  'goal': 'Probe behavior with out‑of‑range address values.',
                  'notes': ['The contract does not define illegal address '
                            'handling, so the property is limited to absence '
                            'of Xs.'],
                  'semantic_tags': ['invalid_illegal_input'],
                  'stimulus_intent': ["Assert write_en=1 with write_addr=8'hFF "
                                      'and a non‑zero write_data, then '
                                      'read_data after a clock edge.'],
                  'stimulus_signals': ['clk',
                                       'rst_n',
                                       'write_en',
                                       'write_addr',
                                       'write_data',
                                       'read_en',
                                       'read_addr'],
                  'timing_assumptions': ['Observe read_data after one clock '
                                         'edge; no fixed latency is assumed.']},
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
               'stimulus_signals': ['rst_n'],
               'timing_assumptions': ['Advance through conservative clocked '
                                      'observations.',
                                      'Do not assume completion before it '
                                      'becomes externally visible.']}}
UNRESOLVED_ITEMS = ["Reset polarity for 'clk' is unresolved.",
 "Reset polarity for 'clk' remains ambiguous; tests assume active‑low reset on "
 'rst_n and treat clk as a regular clock without reset polarity.']
SIGNAL_WIDTHS = {'clk': 1,
 'read_addr': 8,
 'read_data': 6,
 'read_en': 1,
 'rst_n': 1,
 'write_addr': 8,
 'write_data': 6,
 'write_en': 1}
BUSINESS_OUTPUTS = ['read_data']


class VerifiedRamEnv:
    """Thin environment container rendered from structured artifacts."""

    def __init__(self, dut) -> None:
        self.dut = dut
        self.interface = VerifiedRamInterface(dut)
        self.coverage = VerifiedRamCoverage()
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
        if case_id == 'basic_002':
            await self._todo_stimulus_basic_002()
            return
        if case_id == 'edge_002':
            await self._todo_stimulus_edge_002()
            return
        if case_id == 'negative_001':
            await self._todo_stimulus_negative_001()
            return

    async def _todo_stimulus_reset_001(self) -> None:
        """LLM-fill stimulus hook for plan case `reset_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_reset_001 case_id=reset_001
        # Inputs: write_en, write_addr, write_data, read_en, read_addr
        # Stimulus signals: rst_n
        # Goal: Establish a stable post-reset baseline before functional checking.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_reset_001 case_id=reset_001

    async def _todo_stimulus_basic_001(self) -> None:
        """LLM-fill stimulus hook for plan case `basic_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_001 case_id=basic_001
        # Inputs: write_en, write_addr, write_data, read_en, read_addr
        # Stimulus signals: clk, rst_n, write_en, write_addr, write_data, read_en, read_addr
        # Goal: Apply representative legal operations, including simultaneous but independent read and write, and verify stable post‑operation behavior.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_001 case_id=basic_001

    async def _todo_stimulus_edge_001(self) -> None:
        """LLM-fill stimulus hook for plan case `edge_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_edge_001 case_id=edge_001
        # Inputs: write_en, write_addr, write_data, read_en, read_addr
        # Stimulus signals: write_addr, write_data, read_addr
        # Goal: Exercise boundary-value and width-sensitive input patterns.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_edge_001 case_id=edge_001

    async def _todo_stimulus_back_to_back_001(self) -> None:
        """LLM-fill stimulus hook for plan case `back_to_back_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_back_to_back_001 case_id=back_to_back_001
        # Inputs: write_en, write_addr, write_data, read_en, read_addr
        # Stimulus signals: clk, rst_n, write_en
        # Goal: Observe repeated or back-to-back legal operations under conservative timing assumptions.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_back_to_back_001 case_id=back_to_back_001

    async def _todo_stimulus_basic_002(self) -> None:
        """LLM-fill stimulus hook for plan case `basic_002`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_002 case_id=basic_002
        # Inputs: write_en, write_addr, write_data, read_en, read_addr
        # Stimulus signals: clk, rst_n, write_en, write_addr, write_data, read_en, read_addr
        # Goal: Validate behavior of simultaneous read and write operations to the same address under ambiguous timing.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_002 case_id=basic_002

    async def _todo_stimulus_edge_002(self) -> None:
        """LLM-fill stimulus hook for plan case `edge_002`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_edge_002 case_id=edge_002
        # Inputs: write_en, write_addr, write_data, read_en, read_addr
        # Stimulus signals: clk, rst_n, write_en, write_addr, write_data, read_en, read_addr
        # Goal: Exercise address extremes for both read and write ports.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_edge_002 case_id=edge_002

    async def _todo_stimulus_negative_001(self) -> None:
        """LLM-fill stimulus hook for plan case `negative_001`."""
        # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_negative_001 case_id=negative_001
        # Inputs: write_en, write_addr, write_data, read_en, read_addr
        # Stimulus signals: clk, rst_n, write_en, write_addr, write_data, read_en, read_addr
        # Goal: Probe behavior with out‑of‑range address values.
        # Guidance: Drive concrete legal values onto business inputs here.
        pass
        # TODO(cocoverify2:stimulus) END block_id=stimulus_negative_001 case_id=negative_001

    def note_oracle_result(self, result: dict[str, object]) -> None:
        """Keep rendered oracle observations for later phases."""
        self.observation_log.append({"kind": "oracle_result", **result})
