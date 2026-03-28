"""Rendered basic cocotb tests for `barrel_shifter`.

Basic, reset, negative, and repeated-operation tests rendered from the plan.
"""

from __future__ import annotations

import cocotb

from .barrel_shifter_env import PLAN_CASES, BarrelShifterEnv
from .barrel_shifter_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_basic_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_001 case_id=basic_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_001 case_id=basic_001


@cocotb.test()
async def test_basic_001(dut):
    """Verify that a single legal operation (one ctrl pattern) produces a visibly shifted output. Note: Case intent is conservative when the contract is weak or timing is unresolved. Note: Preserves ambiguity about direction (rotate vs logical shift) and timing; only checks observable output change."""
    # Plan category: basic
    # Coverage tags: basic, sanity, unknown, ambiguity_preserving
    # Timing assumption: Do not assume fixed latency.
    # Timing assumption: Use reset-safe or protocol-safe observation windows only.
    # Timing assumption: Do not assume fixed latency; use a protocol‑safe observation window.
    # Conservative rendering: no concrete value-level functional oracle was emitted for this case.
    # Unresolved: Value-level functional oracle for case 'basic_001' is intentionally deferred because timing or interface confidence is too weak.
    # Unresolved: Property oracle for case 'basic_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = BarrelShifterEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'basic_001',
        PLAN_CASES['basic_001']["category"],
        list(PLAN_CASES['basic_001'].get("coverage_tags", [])),
    )
    await _testcase_setup_basic_001(env)
    await env.exercise_case('basic_001')
    results = await run_linked_plan_case(env, 'basic_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('basic_001') == [result["case_id"] for result in results]

