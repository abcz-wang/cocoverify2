"""Rendered edge cocotb tests for `verified_calendar`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .verified_calendar_env import PLAN_CASES, VerifiedCalendarEnv
from .verified_calendar_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Validate correct wrap‑around behavior at the second, minute, and hour boundaries. Note: Stimulus drives the clock long enough to reach 23:59:58, then observes the next two cycles. Note: No assumptions about exact number of cycles to reach the boundary; the test monitors values until the condition is met."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: boundary, wrap_around, hour_rollover
    # Timing assumption: Observe over a sufficient number of clock edges; no fixed‑cycle latency is assumed for the rollovers.
    # Conservative rendering: no concrete value-level functional oracle was emitted for this case.
    # Unresolved: Value-level functional oracle for case 'edge_001' is intentionally deferred because timing or interface confidence is too weak.
    # Unresolved: Property oracle for case 'edge_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = VerifiedCalendarEnv(dut)
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

