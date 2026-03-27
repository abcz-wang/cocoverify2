"""Rendered edge cocotb tests for `valid_ready`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .valid_ready_env import PLAN_CASES, ValidReadyEnv
from .valid_ready_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

@cocotb.test()
async def test_edge_001(dut):
    """Exercise boundary-value and width-sensitive input patterns. Note: Edge coverage remains value-oriented and avoids fixed-latency assumptions."""
    # Plan category: edge
    # Coverage tags: edge, boundary
    # Timing assumption: Do not assume fixed latency.
    # Timing assumption: Use reset-safe or protocol-safe observation windows only.
    # Conservative rendering: no concrete value-level functional oracle was emitted for this case.
    # Unresolved: Value-level functional oracle for case 'edge_001' is intentionally deferred because timing or interface confidence is too weak.
    # Unresolved: Property oracle for case 'edge_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = ValidReadyEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'edge_001',
        PLAN_CASES['edge_001']["category"],
        list(PLAN_CASES['edge_001'].get("coverage_tags", [])),
    )
    await env.exercise_case('edge_001')
    results = await run_linked_plan_case(env, 'edge_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('edge_001') == [result["case_id"] for result in results]

