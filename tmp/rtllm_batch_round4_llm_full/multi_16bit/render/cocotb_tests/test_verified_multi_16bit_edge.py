"""Rendered edge cocotb tests for `verified_multi_16bit`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .verified_multi_16bit_env import PLAN_CASES, VerifiedMulti16bitEnv
from .verified_multi_16bit_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Exercise multiplication with extreme operand values to verify width‑sensitive behavior. Note: Edge coverage remains value-oriented and avoids fixed-latency assumptions. Note: Test patterns include: (ain=0x0000, bin=0x0000), (ain=0xFFFF, bin=0xFFFF), (ain=0x0000, bin=0xFFFF), and (ain=0xFFFF, bin=0x0000)."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: edge, boundary, width_sensitive, ambiguity_preserving
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    # Timing assumption: Conservative observation: wait for done to become high before checking yout for each pattern.
    # Unresolved: Property oracle for case 'edge_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = VerifiedMulti16bitEnv(dut)
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

