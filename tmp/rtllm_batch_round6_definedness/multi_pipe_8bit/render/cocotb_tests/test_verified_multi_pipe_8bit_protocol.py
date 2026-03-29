"""Rendered protocol cocotb tests for `verified_multi_pipe_8bit`.

Protocol-focused tests rendered conservatively from handshake-oriented plan cases.
"""

from __future__ import annotations

import cocotb

from .verified_multi_pipe_8bit_env import PLAN_CASES, VerifiedMultiPipe8bitEnv
from .verified_multi_pipe_8bit_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_protocol_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `protocol_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_protocol_001 case_id=protocol_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_protocol_001 case_id=protocol_001


@cocotb.test()
async def test_protocol_001(dut):
    """Check that the pipeline maintains input‑to‑output ordering under consecutive enable pulses. Note: No fixed latency is assumed; ordering is the key property. Note: Case relies on deterministic clock-driven observation because no non-control inputs were resolved."""
    # Plan category: protocol
    # Execution policy: deterministic
    # Coverage tags: handshake_like
    # Timing assumption: Allow an unspecified number of cycles between input and output pulses; verify ordering rather than exact timing.
    env = VerifiedMultiPipe8bitEnv(dut)
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

