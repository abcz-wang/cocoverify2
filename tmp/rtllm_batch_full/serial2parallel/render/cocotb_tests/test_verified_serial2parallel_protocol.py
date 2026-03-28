"""Rendered protocol cocotb tests for `verified_serial2parallel`.

Protocol-focused tests rendered conservatively from handshake-oriented plan cases.
"""

from __future__ import annotations

import cocotb

from .verified_serial2parallel_env import PLAN_CASES, VerifiedSerial2parallelEnv
from .verified_serial2parallel_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_protocol_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `protocol_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_protocol_001 case_id=protocol_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_protocol_001 case_id=protocol_001


@cocotb.test()
async def test_protocol_001(dut):
    """Exercise the implicit valid‑only protocol and verify correct assertion/deassertion of dout_valid. Note: Addresses the contract ambiguity regarding missing ready signals."""
    # Plan category: protocol
    # Coverage tags: handshake, valid_ready_ambiguity
    # Timing assumption: Do not assume a fixed latency; monitor dout_valid for the first time it becomes high after each 8‑bit group.
    # Unresolved: Property oracle for case 'protocol_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = VerifiedSerial2parallelEnv(dut)
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

