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
    """Exercise representative legal input combinations and observe output mapping across a mix of arithmetic, logical, and shift operations. Note: Case intent is conservative when the contract is weak or timing is unresolved. Note: Preserves the original conservative intent while explicitly noting inclusion of shift‑type opcodes."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: basic, sanity, comb, operation_coverage, ambiguity_preserving
    # Timing assumption: Observe outputs after input stabilization.
    # Timing assumption: Do not infer internal state or undocumented storage.
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
    """Validate functional correctness of every documented ALU opcode using representative operand values. Note: One representative vector per opcode is used; operands are chosen to exercise signed/unsigned behavior and edge conditions (e.g., max/min values). Note: The case remains combinational‑only, respecting the unknown latency model."""
    # Plan category: basic
    # Execution policy: deterministic
    # Coverage tags: operation_specific
    # Timing assumption: Observe outputs after inputs have stabilized; no cycle‑accurate timing is assumed.
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

