"""Rendered edge cocotb tests for `sequence_detector`.

Edge and boundary tests rendered conservatively from the structured plan.
"""

from __future__ import annotations

import cocotb

from .sequence_detector_env import PLAN_CASES, SequenceDetectorEnv
from .sequence_detector_oracle import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

async def _testcase_setup_edge_001(env) -> None:
    """Optional LLM-fill setup hook for plan case `edge_001`."""
    # TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_edge_001 case_id=edge_001
    # Guidance: Optional per-case setup before env.exercise_case().
    pass
    # TODO(cocoverify2:testcase_setup) END block_id=testcase_setup_edge_001 case_id=edge_001


@cocotb.test()
async def test_edge_001(dut):
    """Validate that the detector correctly handles overlapping occurrences of the target sequence. Note: The bitstream contains two overlapping instances of 1001 (e.g., 10011001). Note: Case relies on deterministic clock-driven observation because no non-control inputs were resolved."""
    # Plan category: edge
    # Execution policy: deterministic
    # Coverage tags: overlap, sequence_edge
    # Timing assumption: Observe over at least 12 clock cycles after reset release to capture both detections.
    env = SequenceDetectorEnv(dut)
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

