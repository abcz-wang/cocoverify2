"""Rendered edge cocotb tests for `verified_JC_counter`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .verified_JC_counter_env import PLAN_CASES, VerifiedJcCounterEnv
from .verified_JC_counter_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Validate that the 64‑bit Johnson counter cycles back to zero after a full period. Note: The case does not assume a fixed latency per transition; it observes the natural progression over many cycles."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: wrap_around, boundary
    # Timing assumption: Observations are made on rising edges of clk; exact cycle count is not assumed beyond the 65‑cycle window.
    env = VerifiedJcCounterEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'edge_001',
        PLAN_CASES['edge_001']["category"],
        list(PLAN_CASES['edge_001'].get("coverage_tags", [])),
    )
    await _testcase_setup_edge_001(env)
    await env.exercise_case('edge_001')
    results = await run_linked_plan_case(env, 'edge_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('edge_001') == [result["case_id"] for result in results]

