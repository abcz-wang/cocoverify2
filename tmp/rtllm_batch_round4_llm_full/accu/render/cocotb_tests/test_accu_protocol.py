"""Rendered protocol cocotb tests for `accu`.

Protocol-focused tests rendered conservatively from handshake-oriented plan cases.
"""

from __future__ import annotations

import cocotb

from .accu_env import PLAN_CASES, AccuEnv
from .accu_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_protocol_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `protocol_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_protocol_001 case_id=protocol_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_protocol_001 case_id=protocol_001


@cocotb.test()
async def test_protocol_001(dut):
    """Verify that the module asserts valid_out for a single cycle after accumulating four valid inputs and that data_out reflects the correct sum. Note: Valid_ready handshake is ambiguous; test focuses on observable valid_out pulse."""
    # Plan category: protocol
    # Execution policy: deterministic
    # Coverage tags: valid_out_pulse, accumulation
    # Timing assumption: Observe over multiple clock cycles; do not assume fixed latency beyond the requirement that valid_out appears after the fourth input.
    env = AccuEnv(dut)
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

