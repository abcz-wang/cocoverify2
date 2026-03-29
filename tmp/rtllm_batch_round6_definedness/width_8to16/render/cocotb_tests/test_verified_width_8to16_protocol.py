"""Rendered protocol cocotb tests for `verified_width_8to16`.

Protocol-focused tests rendered conservatively from handshake-oriented plan cases.
"""

from __future__ import annotations

import cocotb

from .verified_width_8to16_env import PLAN_CASES, VerifiedWidth8to16Env
from .verified_width_8to16_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_protocol_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `protocol_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_protocol_001 case_id=protocol_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_protocol_001 case_id=protocol_001


@cocotb.test()
async def test_protocol_001(dut):
    """Confirm correct sequencing of two‑cycle width conversion under conservative timing. Note: The exact latency between second valid_in and valid_out is not assumed; observation window spans up to three cycles."""
    # Plan category: protocol
    # Execution policy: deterministic
    # Coverage tags: handshake, sequencing
    # Timing assumption: Allow up to three clock cycles after second valid_in to see valid_out.
    env = VerifiedWidth8to16Env(dut)
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

