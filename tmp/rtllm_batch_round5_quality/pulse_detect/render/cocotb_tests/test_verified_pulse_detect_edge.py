"""Rendered edge cocotb tests for `verified_pulse_detect`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .verified_pulse_detect_env import PLAN_CASES, VerifiedPulseDetectEnv
from .verified_pulse_detect_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Exercise boundary-value and width-sensitive input patterns. Note: Edge coverage remains value-oriented and avoids fixed-latency assumptions."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: edge, boundary
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    env = VerifiedPulseDetectEnv(dut)
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
    """Check detection of back‑to‑back pulses with one‑cycle separation. Note: Uses the pattern 01010 on data_in to create two overlapping pulses."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: pulse_edge, consecutive
    # Timing assumption: Observe data_out after each three‑cycle window conservatively.
    env = VerifiedPulseDetectEnv(dut)
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

