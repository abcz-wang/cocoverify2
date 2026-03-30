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
    """Apply a simple ADD operation with zero operands to verify basic combinational behavior. Note: Case intent is conservative when the contract is weak or timing is unresolved."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: basic, sanity, comb, operation_specific, add_zero
    # Timing assumption: Observe outputs after input stabilization.
    # Timing assumption: Do not infer internal state or undocumented storage.
    # Timing assumption: Outputs are expected to be stable after a single delta cycle.
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
    """Verify flag output for signed less‑than (SLT) operation."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: operation_specific, slti
    # Timing assumption: Outputs are expected to be stable after a single delta cycle.
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
    """Verify flag output for unsigned less‑than (SLTU) operation."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: operation_specific, sltui
    # Timing assumption: Outputs are expected to be stable after a single delta cycle.
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

