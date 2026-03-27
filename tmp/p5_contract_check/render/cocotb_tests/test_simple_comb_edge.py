"""Rendered edge cocotb tests for `simple_comb`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .simple_comb_env import PLAN_CASES, SimpleCombEnv
from .simple_comb_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

@cocotb.test()
async def test_edge_001(dut):
    """Exercise boundary-value and width-sensitive input patterns. Note: Edge coverage remains value-oriented and avoids fixed-latency assumptions."""
    # Plan category: edge
    # Coverage tags: edge, boundary
    # Timing assumption: Observe outputs after input stabilization.
    # Timing assumption: Do not infer internal state or undocumented storage.
    env = SimpleCombEnv(dut)
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

