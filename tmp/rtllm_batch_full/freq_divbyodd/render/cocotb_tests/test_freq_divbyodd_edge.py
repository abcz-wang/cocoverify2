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
    """Observe that the divided clock output toggles at the expected half‑period intervals derived from the odd divisor, confirming correct edge‑based toggling logic. Note: Internal signals cnt1, cnt2, clk_div1, clk_div2 are not observable; inference is made from the external clk_div waveform."""
    # Plan category: edge
    # Coverage tags: toggle_edge, half_count
    # Timing assumption: Allow observation over at least NUM_DIV clock cycles after each observed toggle to accommodate unknown latency.
    # Conservative rendering: no concrete value-level functional oracle was emitted for this case.
    # Unresolved: No functional oracle was generated for plan case 'edge_001' because no observable non-control outputs were available.
    # Unresolved: Property oracle for case 'edge_001' is acting as a guardrail because stronger functional semantics are not yet justified.
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

