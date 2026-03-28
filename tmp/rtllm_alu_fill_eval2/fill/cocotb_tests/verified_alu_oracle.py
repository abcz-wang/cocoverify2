"""Oracle helpers for `verified_alu`.

This file is rendered from the structured oracle artifact. It intentionally keeps
checks conservative: timing windows are preserved, unresolved items stay visible,
and control signals are never reintroduced as business outputs.
"""

from __future__ import annotations

import json
from typing import Any

from .verified_alu_runtime import assert_equal, assert_true, is_high_impedance, is_unknown, mask_width, to_sint, to_uint

CONTROL_SIGNALS = []
SIGNAL_WIDTHS = {'a': 32,
 'aluc': 6,
 'b': 32,
 'carry': 1,
 'flag': 1,
 'negative': 1,
 'overflow': 1,
 'r': 32,
 'zero': 1}
ORACLE_SPEC = json.loads("{\n  \"functional_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.7475,\n          \"description\": \"Observe that legal input changes are reflected on the observable outputs without state dependence.\",\n          \"notes\": [\n            \"Combinational functional oracle stays descriptive and avoids inventing a full truth table.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked basic stimulus applies legal representative input patterns.\"\n        }\n      ],\n      \"confidence\": 0.7475,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.6775,\n          \"description\": \"Observe stable, externally consistent response to boundary-value input patterns.\",\n          \"notes\": [\n            \"Boundary oracle is value-oriented but intentionally generic.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Boundary-value outputs remain externally consistent and do not require hidden state or fixed-latency interpretation.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"boundary_inputs_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked edge case applies zero-like, one-like, or width-boundary patterns.\"\n        }\n      ],\n      \"confidence\": 0.6775,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"property_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7375,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.7375,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6875,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.6875,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"protocol_oracles\": []\n}")
ORACLE_CASES_BY_PLAN = json.loads("{\n  \"basic_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.7475,\n          \"description\": \"Observe that legal input changes are reflected on the observable outputs without state dependence.\",\n          \"notes\": [\n            \"Combinational functional oracle stays descriptive and avoids inventing a full truth table.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked basic stimulus applies legal representative input patterns.\"\n        }\n      ],\n      \"confidence\": 0.7475,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7375,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.7375,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"edge_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.6775,\n          \"description\": \"Observe stable, externally consistent response to boundary-value input patterns.\",\n          \"notes\": [\n            \"Boundary oracle is value-oriented but intentionally generic.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Boundary-value outputs remain externally consistent and do not require hidden state or fixed-latency interpretation.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"boundary_inputs_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked edge case applies zero-like, one-like, or width-boundary patterns.\"\n        }\n      ],\n      \"confidence\": 0.6775,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6875,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.6875,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ]\n}")
TEMPORAL_MODES = ['event_based']
UNRESOLVED_ITEMS = ['Hybrid LLM plan augmentation failed; retained baseline rule-based coverage.',
 'Hybrid LLM oracle augmentation failed; retained baseline rule-based oracle '
 'checks.']


def linked_oracle_case_ids_for_plan_case(plan_case_id: str) -> list[str]:
    """Return rendered oracle-case ids linked to a plan case."""
    return [case["case_id"] for case in ORACLE_CASES_BY_PLAN.get(plan_case_id, [])]


async def run_linked_plan_case(env, plan_case_id: str) -> list[dict[str, Any]]:
    """Invoke all oracle helpers associated with a rendered test-plan case."""
    results: list[dict[str, Any]] = []
    for oracle_case in ORACLE_CASES_BY_PLAN.get(plan_case_id, []):
        results.append(await _run_oracle_case(env, oracle_case))
    return results


async def _run_oracle_case(env, oracle_case: dict[str, Any]) -> dict[str, Any]:
    """Run the rendered checks for one oracle case."""
    case_results: list[dict[str, Any]] = []
    for check in oracle_case.get("checks", []):
        case_results.append(await _evaluate_check(env, oracle_case["linked_plan_case_id"], oracle_case["case_id"], check))
    return {
        "case_id": oracle_case["case_id"],
        "linked_plan_case_id": oracle_case["linked_plan_case_id"],
        "oracle_group": oracle_case.get("oracle_group", "unknown"),
        "check_count": len(case_results),
        "results": case_results,
        "unresolved_items": list(oracle_case.get("unresolved_items", [])),
        "notes": list(oracle_case.get("notes", [])),
    }


async def _evaluate_check(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any]) -> dict[str, Any]:
    """Apply the rendered wait/observation helper that matches one oracle check."""
    temporal_window = dict(check.get("temporal_window", {}))
    await env.wait_for_window(temporal_window, label=check["check_id"])
    observed_signals = [signal for signal in check.get("observed_signals", []) if signal not in CONTROL_SIGNALS]
    env.coverage.record_oracle_check(check["check_id"], check["check_type"], check["strictness"])
    await _apply_oracle_check_todo(env, plan_case_id, oracle_case_id, check, observed_signals)
    result = {
        "oracle_case_id": oracle_case_id,
        "check_id": check["check_id"],
        "check_type": check["check_type"],
        "strictness": check["strictness"],
        "description": check["description"],
        "trigger_condition": check.get("trigger_condition", ""),
        "pass_condition": check.get("pass_condition", ""),
        "observed_signals": observed_signals,
        "temporal_window": temporal_window,
        "status": "filled_check_invoked",
        "notes": list(check.get("notes", [])),
    }
    env.note_oracle_result(result)
    return result


async def _apply_oracle_check_todo(
    env,
    plan_case_id: str,
    oracle_case_id: str,
    check: dict[str, Any],
    observed_signals: list[str],
) -> None:
    """Dispatch per-check LLM-fill oracle hooks."""
    if check.get("check_id") == 'basic_001_functional_001':
        await _todo_oracle_basic_001_functional_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'edge_001_functional_001':
        await _todo_oracle_edge_001_functional_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'basic_001_property_001':
        await _todo_oracle_basic_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'edge_001_property_001':
        await _todo_oracle_edge_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return


async def _todo_oracle_basic_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001
    inputs = env.get_case_inputs(plan_case_id)
    outputs = await env.sample_outputs(observed_signals)
    # Extract stimulus values
    a = inputs.get('a', 0)
    b = inputs.get('b', 0)
    aluc = inputs.get('aluc', 0)
    # Extract DUT outputs
    r = outputs.get('r')
    zero = outputs.get('zero')
    negative = outputs.get('negative')
    flag = outputs.get('flag')
    # Basic sanity: result should not be unknown (x) value
    assert_true(not is_unknown(r), "Result r must not be unknown")
    # Zero flag: 1 iff result is exactly zero
    expected_zero = 1 if to_uint(r, 32) == 0 else 0
    assert_equal('zero', zero, expected_zero)
    # Negative flag: reflects MSB of the 32‑bit result
    expected_negative = (to_uint(r, 32) >> 31) & 1
    assert_equal('negative', negative, expected_negative)
    # Flag output: defined only for SLT (0b101010) and SLTU (0b101011)
    SLT  = 0b101010
    SLTU = 0b101011
    if aluc == SLT or aluc == SLTU:
        assert_equal('flag', flag, 1)
    else:
        assert_true(is_high_impedance(flag), "flag should be high‑impedance for non‑SLT/SLTU operations")
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001

async def _todo_oracle_edge_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_functional_001 case_id=edge_001 oracle_case_id=functional_edge_001 check_id=edge_001_functional_001
    inputs = env.get_case_inputs(plan_case_id)
    a = inputs.get('a')
    b = inputs.get('b')
    aluc = inputs.get('aluc')
    outputs = await env.sample_outputs(observed_signals)
    r = outputs.get('r')
    zero = outputs.get('zero')
    carry = outputs.get('carry')
    negative = outputs.get('negative')
    overflow = outputs.get('overflow')
    flag = outputs.get('flag')
    # result must not be unknown
    assert_true(not is_unknown(r), "Result r must not be unknown")
    # zero flag matches result
    expected_zero = 1 if to_uint(r, 32) == 0 else 0
    assert_equal('zero', zero, expected_zero)
    # negative flag matches MSB of result
    expected_negative = (to_uint(r, 32) >> 31) & 1
    assert_equal('negative', negative, expected_negative)
    # carry and overflow should be defined 0/1 values (not unknown or high‑impedance)
    assert_true(not is_unknown(carry) and not is_high_impedance(carry), "carry must be a defined 0/1 value")
    assert_true(not is_unknown(overflow) and not is_high_impedance(overflow), "overflow must be a defined 0/1 value")
    # flag is 1 for SLT/SLTU, otherwise high‑impedance
    SLT = 0b101010
    SLTU = 0b101011
    if aluc == SLT or aluc == SLTU:
        assert_equal('flag', flag, 1)
    else:
        assert_true(is_high_impedance(flag), "flag should be high‑impedance for non‑SLT/SLTU operations")
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_functional_001 case_id=edge_001 oracle_case_id=functional_edge_001 check_id=edge_001_functional_001

async def _todo_oracle_basic_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001
    inputs = env.get_case_inputs(plan_case_id)
    a = inputs.get('a')
    b = inputs.get('b')
    aluc = inputs.get('aluc')
    outputs = await env.sample_outputs(observed_signals)
    r = outputs.get('r')
    zero = outputs.get('zero')
    carry = outputs.get('carry')
    negative = outputs.get('negative')
    overflow = outputs.get('overflow')
    flag = outputs.get('flag')
    # result must be a defined value (not unknown)
    assert_true(not is_unknown(r), "Result r must not be unknown")
    # zero flag reflects whether the 32‑bit result is all zeros
    expected_zero = 1 if to_uint(r, 32) == 0 else 0
    assert_equal('zero', zero, expected_zero)
    # negative flag reflects the MSB of the result
    expected_negative = (to_uint(r, 32) >> 31) & 1
    assert_equal('negative', negative, expected_negative)
    # carry and overflow should be defined 0/1 values (not unknown or high‑impedance)
    assert_true(not is_unknown(carry) and not is_high_impedance(carry), "carry must be a defined 0/1 value")
    assert_true(not is_unknown(overflow) and not is_high_impedance(overflow), "overflow must be a defined 0/1 value")
    # flag is 1 for SLT/SLTU, otherwise high‑impedance
    SLT = 0b101010
    SLTU = 0b101011
    if aluc == SLT or aluc == SLTU:
        assert_equal('flag', flag, 1)
    else:
        assert_true(is_high_impedance(flag), "flag should be high‑impedance for non‑SLT/SLTU operations")
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001

async def _todo_oracle_edge_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001
    inputs = env.get_case_inputs(plan_case_id)
    outputs = await env.sample_outputs(observed_signals)
    a = inputs.get('a')
    b = inputs.get('b')
    aluc = inputs.get('aluc')
    r = outputs.get('r')
    zero = outputs.get('zero')
    carry = outputs.get('carry')
    negative = outputs.get('negative')
    overflow = outputs.get('overflow')
    flag = outputs.get('flag')
    assert_true(not is_unknown(r), "Result r must not be unknown")
    expected_zero = 1 if to_uint(r, 32) == 0 else 0
    assert_equal('zero', zero, expected_zero)
    expected_negative = (to_uint(r, 32) >> 31) & 1
    assert_equal('negative', negative, expected_negative)
    assert_true(not is_unknown(carry) and not is_high_impedance(carry), "carry must be a defined 0/1 value")
    assert_true(not is_unknown(overflow) and not is_high_impedance(overflow), "overflow must be a defined 0/1 value")
    SLT = 0b101010
    SLTU = 0b101011
    if aluc == SLT or aluc == SLTU:
        assert_equal('flag', flag, 1)
    else:
        assert_true(is_high_impedance(flag), "flag should be high‑impedance for non‑SLT/SLTU operations")
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001
