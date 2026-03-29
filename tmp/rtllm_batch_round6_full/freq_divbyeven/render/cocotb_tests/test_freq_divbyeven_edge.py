"""Rendered edge cocotb tests for `freq_divbyeven`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .freq_divbyeven_env import PLAN_CASES, FreqDivbyevenEnv
from .freq_divbyeven_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Verify that the divided clock output toggles at the correct interval dictated by the even NUM_DIV parameter and that the internal counter resets on each toggle. Note: NUM_DIV is a parameter; the test assumes a concrete even value (e.g., 8) to make the observation concrete while preserving parameter‑agnostic intent."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: toggle_edge, frequency_division, even_divisor
    # Timing assumption: Conservative observation window spanning at least NUM_DIV cycles after reset release
    env = FreqDivbyevenEnv(dut)
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

