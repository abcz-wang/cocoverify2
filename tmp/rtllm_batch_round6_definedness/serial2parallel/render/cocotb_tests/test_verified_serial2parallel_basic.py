"""Rendered basic cocotb tests for `verified_serial2parallel`.

Basic, reset, negative, and repeated-operation tests rendered from the plan.
"""

from __future__ import annotations

import cocotb

from .verified_serial2parallel_env import PLAN_CASES, VerifiedSerial2parallelEnv
from .verified_serial2parallel_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

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
    env = VerifiedSerial2parallelEnv(dut)
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
    """Validate that a single 8‑bit word is correctly assembled and flagged valid. Note: Case intent is conservative when the contract is weak or timing is unresolved. Note: Assumes synchronous capture on rising clk edge; no timing assumptions beyond observable clocked behavior."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: basic, sanity, seq, validity_logic
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    # Timing assumption: Observe outputs after each rising edge; do not assume fixed latency beyond the eight‑cycle capture.
    env = VerifiedSerial2parallelEnv(dut)
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
    env = VerifiedSerial2parallelEnv(dut)
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
    """Verify that the module ignores serial data when din_valid is low. Note: Ensures that the valid control signal gates data capture. Note: Negative cases require stronger structured illegal-input semantics than the current contract provides."""
    # Plan category: negative
    # Execution policy: deferred
    # Coverage tags: negative, illegal_input
    # Deferred reason: Negative cases require stronger structured illegal-input semantics than the current contract provides.
    # Timing assumption: Observe outputs on each rising edge of clk after stimulus application.
    env = VerifiedSerial2parallelEnv(dut)
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


async def _testcase_setup_basic_002(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_002`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_002 case_id=basic_002
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_002 case_id=basic_002


@cocotb.test()
async def test_basic_002(dut):
    """Confirm correct serial-to-parallel conversion for a single 8‑bit word. Note: Uses a deterministic pattern to make expected parallel value easy to verify."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: basic, sanity
    # Timing assumption: Check dout_valid and dout_parallel on the clock edge following the eighth valid bit.
    env = VerifiedSerial2parallelEnv(dut)
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

