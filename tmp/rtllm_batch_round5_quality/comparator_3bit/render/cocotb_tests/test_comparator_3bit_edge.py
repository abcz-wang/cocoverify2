"""Rendered edge cocotb tests for `comparator_3bit`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .comparator_3bit_env import PLAN_CASES, Comparator3bitEnv
from .comparator_3bit_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Validate edge behavior of the comparator Note: Edge coverage remains value-oriented and avoids fixed-latency assumptions. Note: Covers min (0) and max (7) values for both operands"""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: edge, boundary, boundary_extremes
    # Timing assumption: Observe outputs after input stabilization.
    # Timing assumption: Do not infer internal state or undocumented storage.
    # Timing assumption: Observe after inputs settle
    env = Comparator3bitEnv(dut)
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


async def _testcase_setup_edge_002(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_002`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_002 case_id=edge_002
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_002 case_id=edge_002


@cocotb.test()
async def test_edge_002(dut):
    """Validate extreme boundary conditions of the comparator Note: Test cases include A=0,B=0; A=7,B=7; A=0,B=7; A=7,B=0"""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: min_max
    # Timing assumption: Observe outputs after inputs settle
    env = Comparator3bitEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'edge_002',
        PLAN_CASES['edge_002']["category"],
        list(PLAN_CASES['edge_002'].get("coverage_tags", [])),
    )
    await _testcase_setup_edge_002(env)
    await env.exercise_case('edge_002')
    results = await run_linked_plan_case(env, 'edge_002')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('edge_002') == [result["case_id"] for result in results]

