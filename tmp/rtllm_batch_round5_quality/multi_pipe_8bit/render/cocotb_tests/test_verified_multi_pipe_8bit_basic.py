"""Rendered basic cocotb tests for `verified_multi_pipe_8bit`.

Basic, reset, negative, and repeated-operation tests rendered from the plan.
"""

from __future__ import annotations

import cocotb

from .verified_multi_pipe_8bit_env import PLAN_CASES, VerifiedMultiPipe8bitEnv
from .verified_multi_pipe_8bit_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_reset_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `reset_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_reset_001 case_id=reset_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_reset_001 case_id=reset_001


@cocotb.test()
async def test_reset_001(dut):
    """Establish a stable post-reset baseline before functional checking. Note: Reset polarity may still be heuristic if the contract marks it ambiguous."""
    # Plan category: reset
    # Execution policy: deterministic
    # Coverage tags: reset, initialization, stability
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    env = VerifiedMultiPipe8bitEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'reset_001',
        PLAN_CASES['reset_001']["category"],
        list(PLAN_CASES['reset_001'].get("coverage_tags", [])),
    )
    await _testcase_setup_reset_001(env)
    await env.exercise_case('reset_001')
    results = await run_linked_plan_case(env, 'reset_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('reset_001') == [result["case_id"] for result in results]


async def _testcase_setup_basic_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_001 case_id=basic_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_001 case_id=basic_001


@cocotb.test()
async def test_basic_001(dut):
    """Validate that a single multiplication operation propagates correctly to mul_en_out and mul_out after a conservative observation window. Note: Case intent is conservative when the contract is weak or timing is unresolved. Note: No assumption on exact pipeline depth; observation window extended until mul_en_out toggles."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: basic, sanity, seq, operation_specific
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    # Timing assumption: Observe over multiple clock cycles until mul_en_out asserts, then capture mul_out.
    env = VerifiedMultiPipe8bitEnv(dut)
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
    """Observe repeated or back-to-back legal operations under conservative timing assumptions. Note: When timing is unresolved, this case stays unresolved-safe and does not require deterministic overlap behavior."""
    # Plan category: back_to_back
    # Execution policy: deterministic
    # Coverage tags: back_to_back, repeated_operation
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    env = VerifiedMultiPipe8bitEnv(dut)
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


async def _testcase_setup_negative_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `negative_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_negative_001 case_id=negative_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_negative_001 case_id=negative_001


@cocotb.test(skip=True)
async def test_negative_001(dut):
    """Confirm that disabling the input enable prevents any output activity despite input changes. Note: Ensures that the design correctly gates pipeline registers with mul_en_in. Note: Negative cases require stronger structured illegal-input semantics than the current contract provides."""
    # Plan category: negative
    # Execution policy: deferred
    # Coverage tags: illegal_input, output_stability
    # Deferred reason: Negative cases require stronger structured illegal-input semantics than the current contract provides.
    # Timing assumption: Allow sufficient cycles for any latent pipeline stages to settle after input changes.
    env = VerifiedMultiPipe8bitEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'negative_001',
        PLAN_CASES['negative_001']["category"],
        list(PLAN_CASES['negative_001'].get("coverage_tags", [])),
    )
    await _testcase_setup_negative_001(env)
    await env.exercise_case('negative_001')
    results = await run_linked_plan_case(env, 'negative_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('negative_001') == [result["case_id"] for result in results]

