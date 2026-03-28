"""Rendered edge cocotb tests for `verified_edge_detect`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .verified_edge_detect_env import PLAN_CASES, VerifiedEdgeDetectEnv
from .verified_edge_detect_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Exercise extreme and rapid edge patterns to confirm correct one‑cycle pulse generation for both edges. Note: Edge coverage remains value-oriented and avoids fixed-latency assumptions. Note: Rapid back‑to‑back edges are allowed because the spec only requires detection on the next clock after the edge appears."""
    # Plan category: edge
    # Coverage tags: edge, boundary, value_exploration
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    # Timing assumption: Conservative clocked observation: check outputs on each rising edge of clk.
    env = VerifiedEdgeDetectEnv(dut)
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

