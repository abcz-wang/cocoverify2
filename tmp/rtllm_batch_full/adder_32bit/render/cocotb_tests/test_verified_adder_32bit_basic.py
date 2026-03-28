"""Rendered basic cocotb tests for `verified_adder_32bit`.

Basic, reset, negative, and repeated-operation tests rendered from the plan.
"""

from __future__ import annotations

import cocotb

from .verified_adder_32bit_env import PLAN_CASES, VerifiedAdder32bitEnv
from .verified_adder_32bit_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_basic_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_001 case_id=basic_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_001 case_id=basic_001


@cocotb.test()
async def test_basic_001(dut):
    """Exercise representative legal input combinations and observe output mapping Note: Case intent is conservative when the contract is weak or timing is unresolved. Note: Conservative case due to unknown port directions and lack of timing guarantees."""
    # Plan category: basic
    # Coverage tags: basic, sanity, comb, ambiguity_preserving
    # Timing assumption: Observe outputs after input stabilization.
    # Timing assumption: Do not infer internal state or undocumented storage.
    # Timing assumption: Observe outputs after input stabilization; no cycle‑accurate timing inferred.
    # Unresolved: Property oracle for case 'basic_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = VerifiedAdder32bitEnv(dut)
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


async def _testcase_setup_back_to_back_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `back_to_back_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_back_to_back_001 case_id=back_to_back_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_back_to_back_001 case_id=back_to_back_001


@cocotb.test()
async def test_back_to_back_001(dut):
    """Check combinational independence across successive stimulus applications Note: Apply two distinct input vectors sequentially without inserting explicit delays."""
    # Plan category: back_to_back
    # Coverage tags: throughput, back_to_back
    # Timing assumption: No timing assumptions beyond combinational stabilization between vectors.
    # Unresolved: Property oracle for case 'back_to_back_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = VerifiedAdder32bitEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'back_to_back_001',
        PLAN_CASES['back_to_back_001']["category"],
        list(PLAN_CASES['back_to_back_001'].get("coverage_tags", [])),
    )
    await _testcase_setup_back_to_back_001(env)
    await env.exercise_case('back_to_back_001')
    results = await run_linked_plan_case(env, 'back_to_back_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('back_to_back_001') == [result["case_id"] for result in results]

