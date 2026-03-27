"""Rendered protocol cocotb tests for `valid_ready`.

Protocol-focused tests rendered conservatively from handshake-oriented plan cases.
"""

from __future__ import annotations

import cocotb

from .valid_ready_env import PLAN_CASES, ValidReadyEnv
from .valid_ready_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

@cocotb.test()
async def test_protocol_001(dut):
    """Observe basic in valid/ready handshake acceptance. Note: Protocol case is intentionally acceptance-oriented, not latency-committing."""
    # Plan category: protocol
    # Coverage tags: protocol, valid_ready, acceptance, in
    # Timing assumption: Do not assume fixed latency.
    # Timing assumption: Use reset-safe or protocol-safe observation windows only.
    # Timing assumption: Avoid fixed-cycle acceptance or completion checks unless the contract explicitly provides them.
    # Unresolved: Property oracle for case 'protocol_001' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = ValidReadyEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'protocol_001',
        PLAN_CASES['protocol_001']["category"],
        list(PLAN_CASES['protocol_001'].get("coverage_tags", [])),
    )
    await env.exercise_case('protocol_001')
    results = await run_linked_plan_case(env, 'protocol_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('protocol_001') == [result["case_id"] for result in results]


@cocotb.test()
async def test_protocol_002(dut):
    """Observe in backpressure behavior when ready is low. Note: Backpressure case is protocol-safe and avoids precise throughput claims."""
    # Plan category: protocol
    # Coverage tags: protocol, valid_ready, backpressure, in
    # Timing assumption: Do not assume fixed latency.
    # Timing assumption: Use reset-safe or protocol-safe observation windows only.
    # Timing assumption: Avoid fixed-cycle acceptance or completion checks unless the contract explicitly provides them.
    # Unresolved: Property oracle for case 'protocol_002' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = ValidReadyEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'protocol_002',
        PLAN_CASES['protocol_002']["category"],
        list(PLAN_CASES['protocol_002'].get("coverage_tags", [])),
    )
    await env.exercise_case('protocol_002')
    results = await run_linked_plan_case(env, 'protocol_002')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('protocol_002') == [result["case_id"] for result in results]


@cocotb.test()
async def test_protocol_003(dut):
    """Observe safe valid persistence or safe-source behavior for in traffic. Note: This case is intentionally unresolved-safe when the contract does not define source obligations exactly."""
    # Plan category: protocol
    # Coverage tags: protocol, valid_ready, persistence, in
    # Timing assumption: Do not assume fixed latency.
    # Timing assumption: Use reset-safe or protocol-safe observation windows only.
    # Timing assumption: Avoid fixed-cycle acceptance or completion checks unless the contract explicitly provides them.
    # Unresolved: Property oracle for case 'protocol_003' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = ValidReadyEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'protocol_003',
        PLAN_CASES['protocol_003']["category"],
        list(PLAN_CASES['protocol_003'].get("coverage_tags", [])),
    )
    await env.exercise_case('protocol_003')
    results = await run_linked_plan_case(env, 'protocol_003')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('protocol_003') == [result["case_id"] for result in results]


@cocotb.test()
async def test_protocol_004(dut):
    """Observe basic out valid/ready handshake acceptance. Note: Protocol case is intentionally acceptance-oriented, not latency-committing."""
    # Plan category: protocol
    # Coverage tags: protocol, valid_ready, acceptance, out
    # Timing assumption: Do not assume fixed latency.
    # Timing assumption: Use reset-safe or protocol-safe observation windows only.
    # Timing assumption: Avoid fixed-cycle acceptance or completion checks unless the contract explicitly provides them.
    # Unresolved: Property oracle for case 'protocol_004' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = ValidReadyEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'protocol_004',
        PLAN_CASES['protocol_004']["category"],
        list(PLAN_CASES['protocol_004'].get("coverage_tags", [])),
    )
    await env.exercise_case('protocol_004')
    results = await run_linked_plan_case(env, 'protocol_004')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('protocol_004') == [result["case_id"] for result in results]


@cocotb.test()
async def test_protocol_005(dut):
    """Observe out backpressure behavior when ready is low. Note: Backpressure case is protocol-safe and avoids precise throughput claims."""
    # Plan category: protocol
    # Coverage tags: protocol, valid_ready, backpressure, out
    # Timing assumption: Do not assume fixed latency.
    # Timing assumption: Use reset-safe or protocol-safe observation windows only.
    # Timing assumption: Avoid fixed-cycle acceptance or completion checks unless the contract explicitly provides them.
    # Unresolved: Property oracle for case 'protocol_005' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = ValidReadyEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'protocol_005',
        PLAN_CASES['protocol_005']["category"],
        list(PLAN_CASES['protocol_005'].get("coverage_tags", [])),
    )
    await env.exercise_case('protocol_005')
    results = await run_linked_plan_case(env, 'protocol_005')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('protocol_005') == [result["case_id"] for result in results]


@cocotb.test()
async def test_protocol_006(dut):
    """Observe safe valid persistence or safe-source behavior for out traffic. Note: This case is intentionally unresolved-safe when the contract does not define source obligations exactly."""
    # Plan category: protocol
    # Coverage tags: protocol, valid_ready, persistence, out
    # Timing assumption: Do not assume fixed latency.
    # Timing assumption: Use reset-safe or protocol-safe observation windows only.
    # Timing assumption: Avoid fixed-cycle acceptance or completion checks unless the contract explicitly provides them.
    # Unresolved: Property oracle for case 'protocol_006' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = ValidReadyEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'protocol_006',
        PLAN_CASES['protocol_006']["category"],
        list(PLAN_CASES['protocol_006'].get("coverage_tags", [])),
    )
    await env.exercise_case('protocol_006')
    results = await run_linked_plan_case(env, 'protocol_006')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('protocol_006') == [result["case_id"] for result in results]


@cocotb.test()
async def test_protocol_007(dut):
    """Observe whether start eventually leads to externally visible completion. Note: Completion is checked conservatively because the contract does not guarantee exact latency."""
    # Plan category: protocol
    # Coverage tags: protocol, start_done, completion
    # Timing assumption: Do not assume fixed latency.
    # Timing assumption: Use reset-safe or protocol-safe observation windows only.
    # Timing assumption: Avoid fixed-cycle acceptance or completion checks unless the contract explicitly provides them.
    # Unresolved: Property oracle for case 'protocol_007' is acting as a guardrail because stronger functional semantics are not yet justified.
    env = ValidReadyEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'protocol_007',
        PLAN_CASES['protocol_007']["category"],
        list(PLAN_CASES['protocol_007'].get("coverage_tags", [])),
    )
    await env.exercise_case('protocol_007')
    results = await run_linked_plan_case(env, 'protocol_007')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('protocol_007') == [result["case_id"] for result in results]

