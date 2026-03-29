"""Rendered basic cocotb tests for `multi_8bit`.

Basic, reset, negative, and repeated-operation tests rendered from the plan.
"""

from __future__ import annotations

import cocotb

from .multi_8bit_env import PLAN_CASES, Multi8bitEnv
from .multi_8bit_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_basic_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_001 case_id=basic_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_001 case_id=basic_001


@cocotb.test()
async def test_basic_001(dut):
    """Observe that the multiplier produces the correct product for a single deterministic input pair, respecting reset‑safe observation windows. Note: Case intent is conservative when the contract is weak or timing is unresolved. Note: Conservative case due to unknown timing; only external visibility is checked."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: basic, sanity, unknown, operation_specific, ambiguity_preserving
    # Timing assumption: Do not assume fixed latency.
    # Timing assumption: Use reset-safe or protocol-safe observation windows only.
    # Timing assumption: Do not assume fixed latency; use a window of several cycles after stimulus
    # Unresolved: Value-level functional oracle for case 'basic_001' is intentionally deferred because timing or interface confidence is too weak.
    # Unresolved: Property oracle for case 'basic_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = Multi8bitEnv(dut)
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
    """Verify correct operation when multiple input vectors are presented consecutively without intervening reset. Note: Stimulus is deterministic; observation windows are sized conservatively to avoid fixed‑latency assumptions."""
    # Plan category: back_to_back
    # Execution policy: deterministic
    # Coverage tags: back_to_back, throughput
    # Timing assumption: Use a reset‑safe or protocol‑safe observation window that is long enough to capture the product after each stimulus, without assuming a fixed number of cycles
    # Unresolved: Property oracle for case 'back_to_back_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = Multi8bitEnv(dut)
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

