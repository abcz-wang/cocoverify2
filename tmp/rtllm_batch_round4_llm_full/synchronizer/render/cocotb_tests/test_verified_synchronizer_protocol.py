"""Rendered protocol cocotb tests for `verified_synchronizer`.

Protocol-focused tests rendered conservatively from handshake-oriented plan cases.
"""

from __future__ import annotations

import cocotb

from .verified_synchronizer_env import PLAN_CASES, VerifiedSynchronizerEnv
from .verified_synchronizer_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_protocol_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `protocol_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_protocol_001 case_id=protocol_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_protocol_001 case_id=protocol_001


@cocotb.test()
async def test_protocol_001(dut):
    """Validate cross-domain synchronization timing without assuming exact latency. Note: Observes that dataout may change after variable latency due to unknown pipeline depth."""
    # Plan category: protocol
    # Execution policy: deterministic
    # Coverage tags: timing, synchronization
    # Timing assumption: Allow up to 8 clk_b cycles after deassertion of data_en to see dataout update.
    # Unresolved: Property oracle for case 'protocol_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = VerifiedSynchronizerEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'protocol_001',
        PLAN_CASES['protocol_001']["category"],
        list(PLAN_CASES['protocol_001'].get("coverage_tags", [])),
    )
    await _testcase_setup_protocol_001(env)
    await env.exercise_case('protocol_001')
    results = await run_linked_plan_case(env, 'protocol_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('protocol_001') == [result["case_id"] for result in results]

