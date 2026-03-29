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
    """Verify that a minimal reset pulse correctly re‑initializes the divider without causing output glitches. Note: The pulse width is limited to a single clk cycle to stress the reset recovery logic. Note: Case relies on deterministic clock-driven observation because no non-control inputs were resolved."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: reset, pulse, glitch_free
    # Timing assumption: Monitor at least 5 clk cycles after reset release
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

