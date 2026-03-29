"""Rendered basic cocotb tests for `fixed_point_subtractor`.

Basic, reset, negative, and repeated-operation tests rendered from the plan.
"""

from __future__ import annotations

import cocotb

from .fixed_point_subtractor_env import PLAN_CASES, FixedPointSubtractorEnv
from .fixed_point_subtractor_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_basic_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `basic_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_001 case_id=basic_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_basic_001 case_id=basic_001


@cocotb.test()
async def test_basic_001(dut):
    """Confirm functional correctness for typical operand values. Note: Case intent is conservative when the contract is weak or timing is unresolved. Note: Uses random stimulus within full N‑bit range."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: basic, sanity, comb, unsigned_subtraction
    # Timing assumption: Observe outputs after input stabilization.
    # Timing assumption: Do not infer internal state or undocumented storage.
    # Timing assumption: Allow one delta cycle for combinational propagation after inputs change.
    env = FixedPointSubtractorEnv(dut)
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
    """Validate functional correctness of unsigned subtraction across a broad random set of operand values. Note: Random stimulus covers typical operating points without assuming any internal latency."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: sanity, comb, unsigned_subtraction
    # Timing assumption: Observe c after inputs have stabilized (combinational propagation).
    env = FixedPointSubtractorEnv(dut)
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

