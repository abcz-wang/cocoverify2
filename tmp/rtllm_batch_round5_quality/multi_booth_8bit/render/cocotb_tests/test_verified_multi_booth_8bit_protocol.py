"""Rendered protocol cocotb tests for `verified_multi_booth_8bit`.

Protocol-focused tests rendered conservatively from handshake-oriented plan cases.
"""

from __future__ import annotations

import cocotb

from .verified_multi_booth_8bit_env import PLAN_CASES, VerifiedMultiBooth8bitEnv
from .verified_multi_booth_8bit_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_protocol_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `protocol_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_protocol_001 case_id=protocol_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_protocol_001 case_id=protocol_001


@cocotb.test()
async def test_protocol_001(dut):
    """Confirm that the ready signal asserts within an expected bound after inputs are presented Note: Since latency is unknown, use an upper bound of 20 cycles (twice the counter maximum). Note: Case relies on deterministic clock-driven observation because no non-control inputs were resolved."""
    # Plan category: protocol
    # Execution policy: deterministic
    # Coverage tags: latency, ready_signal
    # Timing assumption: Observe for up to 20 cycles after inputs are applied
    env = VerifiedMultiBooth8bitEnv(dut)
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

