"""Rendered basic cocotb tests for `square_wave`.

Basic, reset, negative, and repeated-operation tests rendered from the plan.
"""

from __future__ import annotations

import cocotb

from .square_wave_env import PLAN_CASES, SquareWaveEnv
from .square_wave_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_basic_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_001 case_id=basic_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_001 case_id=basic_001


@cocotb.test()
async def test_basic_001(dut):
    """Apply one legal operation and observe stable post‑operation behavior. Note: Case intent is conservative when the contract is weak or timing is unresolved."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: basic, sanity, seq
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    env = SquareWaveEnv(dut)
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
    """Observe repeated or back‑to‑back legal operations under conservative timing assumptions. Note: When timing is unresolved, this case stays unresolved-safe and does not require deterministic overlap behavior. Note: When timing is unresolved, this case stays unresolved‑safe and does not require deterministic overlap behavior."""
    # Plan category: back_to_back
    # Execution policy: deterministic
    # Coverage tags: back_to_back, repeated_operation
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    env = SquareWaveEnv(dut)
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


async def _testcase_setup_regression_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `regression_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_regression_001 case_id=regression_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_regression_001 case_id=regression_001


@cocotb.test()
async def test_regression_001(dut):
    """Verify that updating the frequency control while the counter is running updates the toggle period correctly."""
    # Plan category: regression
    # Execution policy: deterministic
    # Coverage tags: regression, mid_operation_change
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    env = SquareWaveEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'regression_001',
        PLAN_CASES['regression_001']["category"],
        list(PLAN_CASES['regression_001'].get("coverage_tags", [])),
    )
    await _testcase_setup_regression_001(env)
    await env.exercise_case('regression_001')
    results = await run_linked_plan_case(env, 'regression_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('regression_001') == [result["case_id"] for result in results]

