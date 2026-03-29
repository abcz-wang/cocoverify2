"""Rendered basic cocotb tests for `verified_parallel2serial`.

Basic, reset, negative, and repeated-operation tests rendered from the plan.
"""

from __future__ import annotations

import cocotb

from .verified_parallel2serial_env import PLAN_CASES, VerifiedParallel2serialEnv
from .verified_parallel2serial_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

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
    env = VerifiedParallel2serialEnv(dut)
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
    """Verify that a single parallel load produces the correct serial stream and associated valid_out timing Note: Case intent is conservative when the contract is weak or timing is unresolved. Note: Assumes the internal counter resets on load; does not rely on exact cycle numbers beyond observable valid_out high period"""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: basic, sanity, seq, valid_pulse, serial_sequence
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    # Timing assumption: Observe over at least five clock cycles after stimulus to capture the full serial sequence
    env = VerifiedParallel2serialEnv(dut)
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
    env = VerifiedParallel2serialEnv(dut)
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


async def _testcase_setup_basic_002(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_002`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_002 case_id=basic_002
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_002 case_id=basic_002


@cocotb.test()
async def test_basic_002(dut):
    """Confirm that the valid_out pulse duration matches the four-bit serialization period"""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: valid_timing, pulse_width
    # Timing assumption: Conservative observation; do not assume exact cycle alignment, only that the high period spans at least four cycles
    env = VerifiedParallel2serialEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'basic_002',
        PLAN_CASES['basic_002']["category"],
        list(PLAN_CASES['basic_002'].get("coverage_tags", [])),
    )
    await _testcase_setup_basic_002(env)
    await env.exercise_case('basic_002')
    results = await run_linked_plan_case(env, 'basic_002')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('basic_002') == [result["case_id"] for result in results]


async def _testcase_setup_reset_002(env) -> None:
    """Optional LLM-fill setup hook for plan case `reset_002`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_reset_002 case_id=reset_002
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_reset_002 case_id=reset_002


@cocotb.test()
async def test_reset_002(dut):
    """Ensure the module initializes to a defined state after reset release"""
    # Plan category: reset
    # Execution policy: deterministic
    # Coverage tags: reset, stability
    # Timing assumption: Observe for at least two clock cycles after reset release
    env = VerifiedParallel2serialEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'reset_002',
        PLAN_CASES['reset_002']["category"],
        list(PLAN_CASES['reset_002'].get("coverage_tags", [])),
    )
    await _testcase_setup_reset_002(env)
    await env.exercise_case('reset_002')
    results = await run_linked_plan_case(env, 'reset_002')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('reset_002') == [result["case_id"] for result in results]

