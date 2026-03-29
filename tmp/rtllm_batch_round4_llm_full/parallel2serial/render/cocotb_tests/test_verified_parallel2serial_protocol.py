"""Rendered protocol cocotb tests for `verified_parallel2serial`.

Protocol-focused tests rendered conservatively from handshake-oriented plan cases.
"""

from __future__ import annotations

import cocotb

from .verified_parallel2serial_env import PLAN_CASES, VerifiedParallel2serialEnv
from .verified_parallel2serial_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_protocol_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `protocol_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_protocol_001 case_id=protocol_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_protocol_001 case_id=protocol_001


@cocotb.test()
async def test_protocol_001(dut):
    """Validate the implicit valid‑ready protocol implied by valid_out without assuming a ready signal. Note: The test drives a second d value two cycles after the first word start to check that valid_out does not pulse prematurely."""
    # Plan category: protocol
    # Execution policy: deterministic
    # Coverage tags: valid_pulse_protocol
    # Timing assumption: Sample valid_out and dout each rising edge; do not assume a fixed latency for the second word's valid_out.
    # Unresolved: Property oracle for case 'protocol_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = VerifiedParallel2serialEnv(dut)
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

