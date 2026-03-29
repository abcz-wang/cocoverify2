"""Rendered edge cocotb tests for `square_wave`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .square_wave_env import PLAN_CASES, SquareWaveEnv
from .square_wave_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Exercise boundary‑value freq patterns without relying on hidden latency. Note: Edge coverage remains value-oriented and avoids fixed-latency assumptions. Note: Edge coverage remains value‑oriented; the design should handle both extremes safely."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: edge, boundary, freq_min_max
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    # Timing assumption: Conservative observation over multiple clock cycles for each boundary value.
    env = SquareWaveEnv(dut)
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

