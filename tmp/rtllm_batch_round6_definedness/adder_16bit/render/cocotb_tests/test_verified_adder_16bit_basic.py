"""Rendered basic cocotb tests for `verified_adder_16bit`.

Basic, reset, negative, and repeated-operation tests rendered from the plan.
"""

from __future__ import annotations

import cocotb

from .verified_adder_16bit_env import PLAN_CASES, VerifiedAdder16bitEnv
from .verified_adder_16bit_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_basic_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_001 case_id=basic_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_001 case_id=basic_001


@cocotb.test()
async def test_basic_001(dut):
    """Confirm basic functional mapping for random legal inputs. Note: Case intent is conservative when the contract is weak or timing is unresolved. Note: Randomized stimulus covers typical usage across the full operand range."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: basic, sanity, comb, operation_specific
    # Timing assumption: Observe outputs after input stabilization.
    # Timing assumption: Do not infer internal state or undocumented storage.
    # Timing assumption: Observe outputs after input stabilization; no explicit latency assumed.
    env = VerifiedAdder16bitEnv(dut)
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
    """Validate that rapid successive input changes do not cause glitches beyond combinational propagation. Note: Since the adder is combinational, outputs should settle to each new input without internal state."""
    # Plan category: back_to_back
    # Execution policy: deterministic
    # Coverage tags: back_to_back, comb
    # Timing assumption: Observe outputs after each input vector stabilizes; no clock needed.
    env = VerifiedAdder16bitEnv(dut)
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


async def _testcase_setup_metamorphic_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `metamorphic_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_metamorphic_001 case_id=metamorphic_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_metamorphic_001 case_id=metamorphic_001


@cocotb.test(skip=True)
async def test_metamorphic_001(dut):
    """Check commutative property of addition. Note: Ensures functional correctness independent of operand ordering. Note: Advanced derived cases were downgraded because the contract does not yet justify deterministic mainline semantics."""
    # Plan category: metamorphic
    # Execution policy: deferred
    # Coverage tags: commutative, property
    # Deferred reason: Advanced derived cases were downgraded because the contract does not yet justify deterministic mainline semantics.
    # Timing assumption: Observe outputs after each vector stabilizes.
    env = VerifiedAdder16bitEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'metamorphic_001',
        PLAN_CASES['metamorphic_001']["category"],
        list(PLAN_CASES['metamorphic_001'].get("coverage_tags", [])),
    )
    await _testcase_setup_metamorphic_001(env)
    await env.exercise_case('metamorphic_001')
    results = await run_linked_plan_case(env, 'metamorphic_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('metamorphic_001') == [result["case_id"] for result in results]

