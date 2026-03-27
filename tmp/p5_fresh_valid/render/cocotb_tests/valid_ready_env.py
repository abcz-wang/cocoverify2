"""Environment helpers for `valid_ready`.

This file is rendered from contract, plan, and oracle artifacts. It stays thin on
purpose: the environment only coordinates helpers and preserves unresolved items.

Environment notes:
# - Combinational body constructs were found, but detected clock/reset or handshake structure makes the timing model ambiguous.
# - Reset polarity for 'aresetn' is inferred heuristically from the signal name or sensitivity list.
# - Timing model is unresolved; generated cases avoid fixed-latency checks.
# - Contract strength is limited; generated cases favor safe observation over precise timing assumptions.
# - Negative or illegal-input behavior is not planned because the contract does not provide reliable constraints.
"""

from __future__ import annotations

from pprint import pformat

import cocotb
from cocotb.triggers import ReadOnly, RisingEdge, Timer

from .valid_ready_coverage import ValidReadyCoverage
from .valid_ready_interface import ValidReadyInterface

PLAN_CASES = {'back_to_back_001': {'category': 'back_to_back',
                      'coverage_tags': ['back_to_back', 'repeated_operation'],
                      'dependencies': ['basic_001'],
                      'goal': 'Observe repeated or back-to-back legal '
                              'operations under conservative timing '
                              'assumptions.',
                      'notes': ['When timing is unresolved, this case stays '
                                'unresolved-safe and does not require '
                                'deterministic overlap behavior.'],
                      'stimulus_intent': ['Apply two legal operations with '
                                          'minimal idle spacing that remains '
                                          'safe for the current contract '
                                          'strength.'],
                      'timing_assumptions': ['Do not assume fixed latency.',
                                             'Use reset-safe or protocol-safe '
                                             'observation windows only.']},
 'basic_001': {'category': 'basic',
               'coverage_tags': ['basic', 'sanity', 'unknown'],
               'dependencies': ['reset_001'],
               'goal': 'Apply one legal operation or transaction and observe '
                       'any externally visible progress.',
               'notes': ['Case intent is conservative when the contract is '
                         'weak or timing is unresolved.'],
               'stimulus_intent': ['Drive a representative legal input pattern '
                                   "across known inputs: ['aclk', 'aresetn', "
                                   "'in_valid', 'in_data', 'out_ready', "
                                   "'start']"],
               'timing_assumptions': ['Do not assume fixed latency.',
                                      'Use reset-safe or protocol-safe '
                                      'observation windows only.']},
 'edge_001': {'category': 'edge',
              'coverage_tags': ['edge', 'boundary'],
              'dependencies': ['basic_001'],
              'goal': 'Exercise boundary-value and width-sensitive input '
                      'patterns.',
              'notes': ['Edge coverage remains value-oriented and avoids '
                        'fixed-latency assumptions.'],
              'stimulus_intent': ['Use zero-like, one-like, and boundary '
                                  "patterns on ['in_data']"],
              'timing_assumptions': ['Do not assume fixed latency.',
                                     'Use reset-safe or protocol-safe '
                                     'observation windows only.']},
 'protocol_001': {'category': 'protocol',
                  'coverage_tags': ['protocol',
                                    'valid_ready',
                                    'acceptance',
                                    'in'],
                  'dependencies': ['reset_001'],
                  'goal': 'Observe basic in valid/ready handshake acceptance.',
                  'notes': ['Protocol case is intentionally '
                            'acceptance-oriented, not latency-committing.'],
                  'stimulus_intent': ['Drive in_valid with a legal transaction '
                                      'while allowing in_ready to indicate '
                                      'acceptance.'],
                  'timing_assumptions': ['Do not assume fixed latency.',
                                         'Use reset-safe or protocol-safe '
                                         'observation windows only.',
                                         'Avoid fixed-cycle acceptance or '
                                         'completion checks unless the '
                                         'contract explicitly provides them.']},
 'protocol_002': {'category': 'protocol',
                  'coverage_tags': ['protocol',
                                    'valid_ready',
                                    'backpressure',
                                    'in'],
                  'dependencies': ['basic_001'],
                  'goal': 'Observe in backpressure behavior when ready is low.',
                  'notes': ['Backpressure case is protocol-safe and avoids '
                            'precise throughput claims.'],
                  'stimulus_intent': ['Attempt a transaction while in_ready '
                                      'remains low or unavailable for '
                                      'acceptance.'],
                  'timing_assumptions': ['Do not assume fixed latency.',
                                         'Use reset-safe or protocol-safe '
                                         'observation windows only.',
                                         'Avoid fixed-cycle acceptance or '
                                         'completion checks unless the '
                                         'contract explicitly provides them.']},
 'protocol_003': {'category': 'protocol',
                  'coverage_tags': ['protocol',
                                    'valid_ready',
                                    'persistence',
                                    'in'],
                  'dependencies': ['protocol_001'],
                  'goal': 'Observe safe valid persistence or safe-source '
                          'behavior for in traffic.',
                  'notes': ['This case is intentionally unresolved-safe when '
                            'the contract does not define source obligations '
                            'exactly.'],
                  'stimulus_intent': ['Maintain or re-assert in_valid across '
                                      'conservative observation windows until '
                                      'acceptance is visible.'],
                  'timing_assumptions': ['Do not assume fixed latency.',
                                         'Use reset-safe or protocol-safe '
                                         'observation windows only.',
                                         'Avoid fixed-cycle acceptance or '
                                         'completion checks unless the '
                                         'contract explicitly provides them.']},
 'protocol_004': {'category': 'protocol',
                  'coverage_tags': ['protocol',
                                    'valid_ready',
                                    'acceptance',
                                    'out'],
                  'dependencies': ['reset_001'],
                  'goal': 'Observe basic out valid/ready handshake acceptance.',
                  'notes': ['Protocol case is intentionally '
                            'acceptance-oriented, not latency-committing.'],
                  'stimulus_intent': ['Drive out_valid with a legal '
                                      'transaction while allowing out_ready to '
                                      'indicate acceptance.'],
                  'timing_assumptions': ['Do not assume fixed latency.',
                                         'Use reset-safe or protocol-safe '
                                         'observation windows only.',
                                         'Avoid fixed-cycle acceptance or '
                                         'completion checks unless the '
                                         'contract explicitly provides them.']},
 'protocol_005': {'category': 'protocol',
                  'coverage_tags': ['protocol',
                                    'valid_ready',
                                    'backpressure',
                                    'out'],
                  'dependencies': ['basic_001'],
                  'goal': 'Observe out backpressure behavior when ready is '
                          'low.',
                  'notes': ['Backpressure case is protocol-safe and avoids '
                            'precise throughput claims.'],
                  'stimulus_intent': ['Attempt a transaction while out_ready '
                                      'remains low or unavailable for '
                                      'acceptance.'],
                  'timing_assumptions': ['Do not assume fixed latency.',
                                         'Use reset-safe or protocol-safe '
                                         'observation windows only.',
                                         'Avoid fixed-cycle acceptance or '
                                         'completion checks unless the '
                                         'contract explicitly provides them.']},
 'protocol_006': {'category': 'protocol',
                  'coverage_tags': ['protocol',
                                    'valid_ready',
                                    'persistence',
                                    'out'],
                  'dependencies': ['protocol_001'],
                  'goal': 'Observe safe valid persistence or safe-source '
                          'behavior for out traffic.',
                  'notes': ['This case is intentionally unresolved-safe when '
                            'the contract does not define source obligations '
                            'exactly.'],
                  'stimulus_intent': ['Maintain or re-assert out_valid across '
                                      'conservative observation windows until '
                                      'acceptance is visible.'],
                  'timing_assumptions': ['Do not assume fixed latency.',
                                         'Use reset-safe or protocol-safe '
                                         'observation windows only.',
                                         'Avoid fixed-cycle acceptance or '
                                         'completion checks unless the '
                                         'contract explicitly provides them.']},
 'protocol_007': {'category': 'protocol',
                  'coverage_tags': ['protocol', 'start_done', 'completion'],
                  'dependencies': ['basic_001'],
                  'goal': 'Observe whether start eventually leads to '
                          'externally visible completion.',
                  'notes': ['Completion is checked conservatively because the '
                            'contract does not guarantee exact latency.'],
                  'stimulus_intent': ['Pulse or assert start conservatively '
                                      'and watch for done or related output '
                                      'progress.'],
                  'timing_assumptions': ['Do not assume fixed latency.',
                                         'Use reset-safe or protocol-safe '
                                         'observation windows only.',
                                         'Avoid fixed-cycle acceptance or '
                                         'completion checks unless the '
                                         'contract explicitly provides them.']},
 'reset_001': {'category': 'reset',
               'coverage_tags': ['reset', 'initialization', 'stability'],
               'dependencies': [],
               'goal': 'Establish a stable post-reset baseline before '
                       'functional checking.',
               'notes': ['Reset polarity may still be heuristic if the '
                         'contract marks it ambiguous.'],
               'stimulus_intent': ['Assert the detected reset using the '
                                   'inferred polarity.',
                                   'Release reset conservatively and observe '
                                   'interface stabilization.'],
               'timing_assumptions': ['Do not assume fixed latency.',
                                      'Use reset-safe or protocol-safe '
                                      'observation windows only.']}}
UNRESOLVED_ITEMS = ['Combinational body constructs were found, but detected clock/reset or '
 'handshake structure makes the timing model ambiguous.',
 "Reset polarity for 'aresetn' is inferred heuristically from the signal name "
 'or sensitivity list.',
 'Timing model is unresolved; generated cases avoid fixed-latency checks.',
 'Contract strength is limited; generated cases favor safe observation over '
 'precise timing assumptions.',
 'Negative or illegal-input behavior is not planned because the contract does '
 'not provide reliable constraints.']


class ValidReadyEnv:
    """Thin environment container rendered from structured artifacts."""

    def __init__(self, dut) -> None:
        self.dut = dut
        self.interface = ValidReadyInterface(dut)
        self.coverage = ValidReadyCoverage()
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
        await self.safe_observe(case_id)

    def note_oracle_result(self, result: dict[str, object]) -> None:
        """Keep rendered oracle observations for later phases."""
        self.observation_log.append({"kind": "oracle_result", **result})
