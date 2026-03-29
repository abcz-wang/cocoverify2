"""Rendered protocol cocotb tests for `verified_adder_64bit`.

Protocol-focused tests rendered conservatively from handshake-oriented plan cases.
"""

from __future__ import annotations

import cocotb

from .verified_adder_64bit_env import PLAN_CASES, VerifiedAdder64bitEnv
from .verified_adder_64bit_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_protocol_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `protocol_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_protocol_001 case_id=protocol_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_protocol_001 case_id=protocol_001


@cocotb.test()
async def test_protocol_001(dut):
    """Validate ordering between input enable (i_en) and output enable (o_en) under unknown pipeline latency. Note: Latency is unspecified; the check only requires correct ordering, not a fixed cycle count."""
    # Plan category: protocol
    # Execution policy: deterministic
    # Coverage tags: protocol, enable_flow
    # Timing assumption: Do not assume a fixed number of cycles between i_en assertion and o_en high; allow any non‑negative latency.
    env = VerifiedAdder64bitEnv(dut)
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

