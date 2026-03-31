"""Rendered protocol cocotb tests for `verified_multi_16bit`.

Protocol-focused tests rendered conservatively from handshake-oriented plan cases.
"""

from __future__ import annotations

import cocotb

from .verified_multi_16bit_env import PLAN_CASES, VerifiedMulti16bitEnv
from .verified_multi_16bit_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_protocol_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `protocol_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_protocol_001 case_id=protocol_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_protocol_001 case_id=protocol_001


@cocotb.test()
async def test_protocol_001(dut):
    """Observe whether start eventually leads to externally visible completion. Note: Completion is checked conservatively because the contract does not guarantee exact latency."""
    # Plan category: protocol
    # Execution policy: deterministic
    # Coverage tags: protocol, start_done, completion
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    # Timing assumption: Avoid fixed-cycle acceptance or completion checks unless the contract explicitly provides them.
    # Unresolved: Property oracle for case 'protocol_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = VerifiedMulti16bitEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'protocol_001',
        PLAN_CASES['protocol_001']["category"],
        list(PLAN_CASES['protocol_001'].get("coverage_tags", [])),
    )
    await _testcase_setup_protocol_001(env)
    await env.exercise_case('protocol_001')
    results = await run_linked_plan_case(env, 'protocol_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('protocol_001') == [result["case_id"] for result in results]


async def _testcase_setup_protocol_002(env) -> None:
    """Optional LLM-fill setup hook for plan case `protocol_002`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_protocol_002 case_id=protocol_002
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_protocol_002 case_id=protocol_002


@cocotb.test()
async def test_protocol_002(dut):
    """Use gaps in valid-like gating and confirm that only asserted valid cycles contribute to grouped accumulation. Note: Valid-gap case is finite and deterministic; it checks acceptance semantics rather than exact pipeline latency."""
    # Plan category: protocol
    # Execution policy: deterministic
    # Coverage tags: protocol, valid_gated_stream, group_closure
    # Timing assumption: Advance through conservative clocked observations.
    # Timing assumption: Do not assume completion before it becomes externally visible.
    # Timing assumption: Gap cycles are treated as non-accepting observation points.
    # Unresolved: Property oracle for case 'protocol_002' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = VerifiedMulti16bitEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'protocol_002',
        PLAN_CASES['protocol_002']["category"],
        list(PLAN_CASES['protocol_002'].get("coverage_tags", [])),
    )
    await _testcase_setup_protocol_002(env)
    await env.exercise_case('protocol_002')
    results = await run_linked_plan_case(env, 'protocol_002')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('protocol_002') == [result["case_id"] for result in results]

