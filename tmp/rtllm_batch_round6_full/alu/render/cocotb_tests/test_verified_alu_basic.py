"""Rendered basic cocotb tests for `verified_alu`.

Basic, reset, negative, and repeated-operation tests rendered from the plan.
"""

from __future__ import annotations

import cocotb

from .verified_alu_env import PLAN_CASES, VerifiedAluEnv
from .verified_alu_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_basic_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_001 case_id=basic_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_001 case_id=basic_001


@cocotb.test()
async def test_basic_001(dut):
    """Exercise representative legal input combinations and observe output mapping. Note: Case intent is conservative when the contract is weak or timing is unresolved."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: basic, sanity, comb
    # Timing assumption: Observe outputs after input stabilization.
    # Timing assumption: Do not infer internal state or undocumented storage.
    # Timing assumption: Outputs are assumed to be combinational; they become stable shortly after inputs change.
    env = VerifiedAluEnv(dut)
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


async def _testcase_setup_basic_002(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_002`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_002 case_id=basic_002
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_002 case_id=basic_002


@cocotb.test()
async def test_basic_002(dut):
    """Check that the flag output is correctly set for the SLT instruction."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: operation_specific
    # Timing assumption: Outputs are stable after inputs settle; no sequential timing assumed.
    env = VerifiedAluEnv(dut)
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


async def _testcase_setup_basic_003(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_003`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_003 case_id=basic_003
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_003 case_id=basic_003


@cocotb.test()
async def test_basic_003(dut):
    """Validate that the carry flag is asserted for an unsigned addition that overflows."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: operation_specific
    # Timing assumption: Combinational path assumed; outputs reflect inputs after a short settle.
    env = VerifiedAluEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'basic_003',
        PLAN_CASES['basic_003']["category"],
        list(PLAN_CASES['basic_003'].get("coverage_tags", [])),
    )
    await _testcase_setup_basic_003(env)
    await env.exercise_case('basic_003')
    results = await run_linked_plan_case(env, 'basic_003')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('basic_003') == [result["case_id"] for result in results]


async def _testcase_setup_basic_004(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_004`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_004 case_id=basic_004
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_004 case_id=basic_004


@cocotb.test()
async def test_basic_004(dut):
    """Confirm correct behavior of the SLL (shift left logical) operation."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: operation_specific
    # Timing assumption: Outputs are combinational; no sequential timing assumed.
    env = VerifiedAluEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'basic_004',
        PLAN_CASES['basic_004']["category"],
        list(PLAN_CASES['basic_004'].get("coverage_tags", [])),
    )
    await _testcase_setup_basic_004(env)
    await env.exercise_case('basic_004')
    results = await run_linked_plan_case(env, 'basic_004')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('basic_004') == [result["case_id"] for result in results]

