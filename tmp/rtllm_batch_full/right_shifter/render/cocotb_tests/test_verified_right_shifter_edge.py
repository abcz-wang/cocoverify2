"""Rendered edge cocotb tests for `verified_right_shifter`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .verified_right_shifter_env import PLAN_CASES, VerifiedRightShifterEnv
from .verified_right_shifter_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Check that input transitions close to the clock edge are still reflected in q after the edge, under conservative timing assumptions. Note: Conservative: assume synchronous capture on the rising edge without modeling setup/hold windows."""
    # Plan category: edge
    # Coverage tags: edge, timing
    # Timing assumption: Assume the design samples d on the rising edge of clk.
    # Conservative rendering: no concrete value-level functional oracle was emitted for this case.
    # Unresolved: No functional oracle was generated for plan case 'edge_001' because no observable non-control outputs were available.
    # Unresolved: Property oracle for case 'edge_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = VerifiedRightShifterEnv(dut)
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

