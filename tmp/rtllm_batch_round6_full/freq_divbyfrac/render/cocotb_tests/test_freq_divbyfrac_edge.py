"""Rendered edge cocotb tests for `freq_divbyfrac`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .freq_divbyfrac_env import PLAN_CASES, FreqDivbyfracEnv
from .freq_divbyfrac_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Verify that the fractional divider produces a double‑edge toggling pattern on clk_div as described in the specification."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: edge, fractional_division, double_edge
    # Timing assumption: Observe over a minimum of 14 input clock cycles to ensure two complete fractional division cycles are visible.
    env = FreqDivbyfracEnv(dut)
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

