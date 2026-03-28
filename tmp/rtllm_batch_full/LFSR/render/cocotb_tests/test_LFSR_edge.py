"""Rendered edge cocotb tests for `LFSR`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .LFSR_env import PLAN_CASES, LfsrEnv
from .LFSR_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Validate the edge behavior of the feedback calculation across a clock transition. Note: Assumes the LFSR starts from the known reset state (0000)."""
    # Plan category: edge
    # Coverage tags: edge, feedback_logic, xor_inversion
    # Timing assumption: Capture out one clock cycle after the rising edge.
    # Conservative rendering: no concrete value-level functional oracle was emitted for this case.
    # Unresolved: Value-level functional oracle for case 'edge_001' is intentionally deferred because timing or interface confidence is too weak.
    # Unresolved: Property oracle for case 'edge_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = LfsrEnv(dut)
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

