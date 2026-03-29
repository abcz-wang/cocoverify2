"""Rendered edge cocotb tests for `verified_signal_generator`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .verified_signal_generator_env import PLAN_CASES, VerifiedSignalGeneratorEnv
from .verified_signal_generator_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Validate that the generator correctly switches from incrementing to decrementing at the upper bound of the 5‑bit waveform. Note: Relies on the contract's sequential nature; exact cycle count is not assumed."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: upper_bound_transition, wave_maximum
    # Timing assumption: Observe over a conservative number of clock edges; no fixed‑latency assumption.
    env = VerifiedSignalGeneratorEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'edge_001',
        PLAN_CASES['edge_001']["category"],
        list(PLAN_CASES['edge_001'].get("coverage_tags", [])),
    )
    await _testcase_setup_edge_001(env)
    await env.exercise_case('edge_001')
    results = await run_linked_plan_case(env, 'edge_001')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('edge_001') == [result["case_id"] for result in results]


async def _testcase_setup_edge_002(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_002`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_002 case_id=edge_002
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_002 case_id=edge_002


@cocotb.test()
async def test_edge_002(dut):
    """Confirm that the design correctly initializes wave to zero on reset release. Note: Tests reset polarity and synchronous/asynchronous behavior as hinted by the contract."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: reset_recovery, wave_initialization
    # Timing assumption: Do not assume exact cycle latency for reset recovery; observe after a few cycles.
    env = VerifiedSignalGeneratorEnv(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        'edge_002',
        PLAN_CASES['edge_002']["category"],
        list(PLAN_CASES['edge_002'].get("coverage_tags", [])),
    )
    await _testcase_setup_edge_002(env)
    await env.exercise_case('edge_002')
    results = await run_linked_plan_case(env, 'edge_002')
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case('edge_002') == [result["case_id"] for result in results]

