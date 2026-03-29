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
    """Explore the module's behavior under the ambiguous valid_ready‑like interface where only valid signals are present. Note: The contract flags missing ready signals; this case verifies that operation proceeds safely under that ambiguity."""
    # Plan category: protocol
    # Execution policy: deterministic
    # Coverage tags: handshake_ambiguity, valid_ready_like
    # Timing assumption: Do not assume a fixed number of cycles between the two inputs; monitor for eventual valid_out assertion.
    # Unresolved: Property oracle for case 'protocol_001' is acting as a guardrail because stronger functional semantics are not yet justified.
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

