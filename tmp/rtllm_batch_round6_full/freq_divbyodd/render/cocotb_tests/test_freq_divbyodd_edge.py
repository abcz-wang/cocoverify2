"""Rendered edge cocotb tests for `freq_divbyodd`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .freq_divbyodd_env import PLAN_CASES, FreqDivbyoddEnv
from .freq_divbyodd_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Validate correct handling of an asynchronous active‑low reset asserted during normal operation. Note: Reset polarity for rst_n is known (active low) from the contract; the reset for clk is ambiguous and therefore not used."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: reset_asynchronous, stability
    # Timing assumption: Observe at least 10 clk cycles after reset release before concluding stability.
    env = FreqDivbyoddEnv(dut)
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

