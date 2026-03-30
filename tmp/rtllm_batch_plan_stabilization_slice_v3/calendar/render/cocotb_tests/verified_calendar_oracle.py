"""Oracle helpers for `verified_calendar`.

This file is rendered from the structured oracle artifact. It intentionally keeps
checks conservative: timing windows are preserved, unresolved items stay visible,
and control signals are never reintroduced as business outputs.
"""

from __future__ import annotations

import json
from typing import Any

from .verified_calendar_runtime import assert_equal, assert_true, is_high_impedance, is_unknown, mask_width, to_sint, to_uint

CONTROL_SIGNALS = ['CLK', 'RST']
SIGNAL_WIDTHS = {'CLK': None, 'Hours': 6, 'Mins': 6, 'RST': None, 'Secs': 6}
ORACLE_SPEC = json.loads("{\n  \"functional_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_reset_001\",\n      \"category\": \"reset\",\n      \"checks\": [],\n      \"confidence\": 0.05,\n      \"linked_plan_case_id\": \"reset_001\",\n      \"notes\": [\n        \"Weak-contract path emits an explicit empty functional oracle case instead of guessing values.\"\n      ],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Value-level functional oracle for case 'reset_001' is intentionally deferred because timing or interface confidence is too weak.\"\n      ]\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.5050000000000001,\n          \"description\": \"required\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Ensures observable outputs stay within their defined numeric ranges after reset.\"\n          ],\n          \"observed_signals\": [\n            \"Hours\",\n            \"Mins\",\n            \"Secs\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"Hours \\u2208 [0,23] && Mins \\u2208 [0,59] && Secs \\u2208 [0,59] at all times after reset release.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [\n            \"ambiguity_preserving\",\n            \"width_sensitive\"\n          ],\n          \"signal_policies\": {\n            \"Hours\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"Mins\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"Secs\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": 0,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"After reset is deasserted and on every clock edge.\"\n        }\n      ],\n      \"confidence\": 0.5050000000000001,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [\n        \"Weak-contract path emits an explicit empty functional oracle case instead of guessing values.\"\n      ],\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": [\n        \"Value-level functional oracle for case 'basic_001' is intentionally deferred because timing or interface confidence is too weak.\"\n      ]\n    }\n  ],\n  \"property_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_reset_001\",\n      \"category\": \"reset\",\n      \"checks\": [\n        {\n          \"check_id\": \"reset_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.4750000000000001,\n          \"description\": \"Do not infer business-level completion or acceptance solely from reset activity.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Clock/reset remain anchors and are not emitted as business outputs.\"\n          ],\n          \"observed_signals\": [\n            \"Hours\",\n            \"Mins\",\n            \"Secs\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"No safety property is violated by treating reset as control-only; later functional claims require separate post-reset evidence.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"Hours\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"Mins\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"Secs\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"reset_release\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"While reset is asserted or being released.\"\n        }\n      ],\n      \"confidence\": 0.4750000000000001,\n      \"linked_plan_case_id\": \"reset_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'reset_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.4750000000000001,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"Hours\",\n            \"Mins\",\n            \"Secs\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"Hours\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"Mins\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"Secs\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.4750000000000001,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'basic_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    }\n  ],\n  \"protocol_oracles\": [\n    {\n      \"assumptions\": [\n        \"Handshake groups are treated as heuristic anchors, not fully proven protocol specifications.\"\n      ],\n      \"case_id\": \"protocol_reset_001\",\n      \"category\": \"reset\",\n      \"checks\": [\n        {\n          \"check_id\": \"reset_001_protocol_001\",\n          \"check_type\": \"protocol\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.4650000000000001,\n          \"description\": \"Treat reset assertion/release as a control event and require reset-safe interface behavior.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Reset is used as an anchor only; it is not treated as a business output.\"\n          ],\n          \"observed_signals\": [\n            \"Hours\",\n            \"Mins\",\n            \"Secs\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"No acceptance, completion, or externally visible functional progress is claimed solely during reset; post-release observation waits for stable, externally visible behavior.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"Hours\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"Mins\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"Secs\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"reset_release\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When reset 'RST' is asserted and later released according to the inferred polarity.\"\n        }\n      ],\n      \"confidence\": 0.4650000000000001,\n      \"linked_plan_case_id\": \"reset_001\",\n      \"notes\": [\n        \"Reset oracle focuses on control-safe behavior instead of value-specific output claims.\",\n        \"Protocol oracle strictness is downgraded because the contract or plan is weak.\"\n      ],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ]\n}")
ORACLE_CASES_BY_PLAN = json.loads("{\n  \"basic_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.5050000000000001,\n          \"description\": \"required\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Ensures observable outputs stay within their defined numeric ranges after reset.\"\n          ],\n          \"observed_signals\": [\n            \"Hours\",\n            \"Mins\",\n            \"Secs\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"Hours \\u2208 [0,23] && Mins \\u2208 [0,59] && Secs \\u2208 [0,59] at all times after reset release.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [\n            \"ambiguity_preserving\",\n            \"width_sensitive\"\n          ],\n          \"signal_policies\": {\n            \"Hours\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"Mins\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"Secs\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": 0,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"After reset is deasserted and on every clock edge.\"\n        }\n      ],\n      \"confidence\": 0.5050000000000001,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [\n        \"Weak-contract path emits an explicit empty functional oracle case instead of guessing values.\"\n      ],\n      \"oracle_group\": \"functional\",\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": [\n        \"Value-level functional oracle for case 'basic_001' is intentionally deferred because timing or interface confidence is too weak.\"\n      ]\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.4750000000000001,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"Hours\",\n            \"Mins\",\n            \"Secs\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"Hours\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"Mins\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"Secs\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.4750000000000001,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'basic_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    }\n  ],\n  \"reset_001\": [\n    {\n      \"assumptions\": [\n        \"Handshake groups are treated as heuristic anchors, not fully proven protocol specifications.\"\n      ],\n      \"case_id\": \"protocol_reset_001\",\n      \"category\": \"reset\",\n      \"checks\": [\n        {\n          \"check_id\": \"reset_001_protocol_001\",\n          \"check_type\": \"protocol\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.4650000000000001,\n          \"description\": \"Treat reset assertion/release as a control event and require reset-safe interface behavior.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Reset is used as an anchor only; it is not treated as a business output.\"\n          ],\n          \"observed_signals\": [\n            \"Hours\",\n            \"Mins\",\n            \"Secs\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"No acceptance, completion, or externally visible functional progress is claimed solely during reset; post-release observation waits for stable, externally visible behavior.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"Hours\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"Mins\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"Secs\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"reset_release\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When reset 'RST' is asserted and later released according to the inferred polarity.\"\n        }\n      ],\n      \"confidence\": 0.4650000000000001,\n      \"linked_plan_case_id\": \"reset_001\",\n      \"notes\": [\n        \"Reset oracle focuses on control-safe behavior instead of value-specific output claims.\",\n        \"Protocol oracle strictness is downgraded because the contract or plan is weak.\"\n      ],\n      \"oracle_group\": \"protocol\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_reset_001\",\n      \"category\": \"reset\",\n      \"checks\": [],\n      \"confidence\": 0.05,\n      \"linked_plan_case_id\": \"reset_001\",\n      \"notes\": [\n        \"Weak-contract path emits an explicit empty functional oracle case instead of guessing values.\"\n      ],\n      \"oracle_group\": \"functional\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Value-level functional oracle for case 'reset_001' is intentionally deferred because timing or interface confidence is too weak.\"\n      ]\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_reset_001\",\n      \"category\": \"reset\",\n      \"checks\": [\n        {\n          \"check_id\": \"reset_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.4750000000000001,\n          \"description\": \"Do not infer business-level completion or acceptance solely from reset activity.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Clock/reset remain anchors and are not emitted as business outputs.\"\n          ],\n          \"observed_signals\": [\n            \"Hours\",\n            \"Mins\",\n            \"Secs\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"No safety property is violated by treating reset as control-only; later functional claims require separate post-reset evidence.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"Hours\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"Mins\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"Secs\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"reset_release\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"While reset is asserted or being released.\"\n        }\n      ],\n      \"confidence\": 0.4750000000000001,\n      \"linked_plan_case_id\": \"reset_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'reset_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    }\n  ]\n}")
TEMPORAL_MODES = ['event_based', 'unbounded_safe']
UNRESOLVED_ITEMS = ['Spec/reset hint could not be mapped to a known reset port: The calendar '
 'module uses three always blocks to update the values of seconds, minutes, '
 'and hours based on the clock signal and reset signal.',
 'Spec/reset hint could not be mapped to a known reset port: The second always '
 'block also triggers on the positive edge of the clock signal or the positive '
 'edge of the reset signal. It handles the minutes value (Mins). If the reset '
 'signal is active, it sets the minutes value to 0. If both the minutes and '
 'seconds values are 59, it wraps around and sets the minutes value to 0. If '
 'the seconds value is 59, it increments the minutes value by 1. Otherwise, it '
 'keeps the minutes value unchanged.',
 'Spec/reset hint could not be mapped to a known reset port: The third always '
 'block triggers on the positive edge of the clock signal or the positive edge '
 'of the reset signal. It handles the hours value (Hours). If the reset signal '
 'is active, it sets the hours value to 0. If the hours, minutes, and seconds '
 'values are all at their maximum (23, 59, and 59 respectively), it wraps '
 'around and sets the hours value to 0. If the minutes and seconds values are '
 'both 59, it increments the hours value by 1. Otherwise, it keeps the hours '
 'value unchanged.',
 'Contract strength is limited; generated cases favor safe observation over '
 'precise timing assumptions.',
 'Hybrid LLM plan augmentation failed; retained baseline rule-based coverage.',
 'Contract or plan confidence is limited; oracle generation is intentionally '
 'conservative and may omit value-level functional checks.']


def linked_oracle_case_ids_for_plan_case(plan_case_id: str) -> list[str]:
    """Return rendered oracle-case ids linked to a plan case."""
    return [case["case_id"] for case in ORACLE_CASES_BY_PLAN.get(plan_case_id, [])]


def _signal_policy(check: dict[str, Any], signal_name: str) -> dict[str, Any]:
    return dict(check.get("signal_policies", {}).get(signal_name, {}))


async def _apply_structured_signal_policy(
    env,
    plan_case_id: str,
    check: dict[str, Any],
    observed_signals: list[str],
) -> dict[str, Any]:
    """Apply deterministic, artifact-level observability rules without inventing value semantics."""
    sampled_outputs = await env.sample_outputs(observed_signals) if observed_signals else {}
    recorded_inputs = env.get_case_inputs(plan_case_id)
    if not recorded_inputs:
        return {
            "status": "insufficient_stimulus",
            "checked_signals": [],
            "skipped_signals": list(observed_signals),
            "sampled_outputs": sampled_outputs,
        }

    checked_signals: list[str] = []
    skipped_signals: list[str] = []
    for signal_name in observed_signals:
        policy = _signal_policy(check, signal_name)
        strength = str(policy.get("strength", "unresolved") or "unresolved")
        definedness_mode = str(policy.get("definedness_mode", "not_required") or "not_required")
        value = sampled_outputs.get(signal_name)
        if value is None or strength == "unresolved":
            skipped_signals.append(signal_name)
            continue
        if definedness_mode == "at_observation" and not bool(policy.get("allow_unknown", True)):
            assert_true(not is_unknown(value), f"{signal_name} must not be unknown under structured oracle policy")
        if definedness_mode == "at_observation" and not bool(policy.get("allow_high_impedance", True)):
            assert_true(
                not is_high_impedance(value),
                f"{signal_name} must not be high-impedance under structured oracle policy",
            )
        checked_signals.append(signal_name)

    return {
        "status": "policy_checked" if any(
            str(_signal_policy(check, signal_name).get("definedness_mode", "not_required") or "not_required") == "at_observation"
            for signal_name in checked_signals
        ) else "policy_observed_only" if checked_signals else "policy_guarded_only",
        "checked_signals": checked_signals,
        "skipped_signals": skipped_signals,
        "sampled_outputs": sampled_outputs,
    }


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
    policy_result = await _apply_structured_signal_policy(env, plan_case_id, check, observed_signals)
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
        "signal_policies": dict(check.get("signal_policies", {})),
        "temporal_window": temporal_window,
        "status": policy_result["status"],
        "checked_signals": list(policy_result["checked_signals"]),
        "skipped_signals": list(policy_result["skipped_signals"]),
        "sampled_outputs": dict(policy_result["sampled_outputs"]),
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
    if check.get("check_id") == 'reset_001_protocol_001':
        await _todo_oracle_reset_001_protocol_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'basic_001_functional_001':
        await _todo_oracle_basic_001_functional_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'reset_001_property_001':
        await _todo_oracle_reset_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'basic_001_property_001':
        await _todo_oracle_basic_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return


async def _todo_oracle_reset_001_protocol_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `reset_001_protocol_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_reset_001_protocol_001 case_id=reset_001 oracle_case_id=protocol_reset_001 check_id=reset_001_protocol_001
    # Observed signals: Hours, Mins, Secs
    # Pass condition: No acceptance, completion, or externally visible functional progress is claimed solely during reset; post-release observation waits for stable, externally visible behavior.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_reset_001_protocol_001 case_id=reset_001 oracle_case_id=protocol_reset_001 check_id=reset_001_protocol_001

async def _todo_oracle_basic_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001
    # Observed signals: Hours, Mins, Secs
    # Pass condition: Hours ∈ [0,23] && Mins ∈ [0,59] && Secs ∈ [0,59] at all times after reset release.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001

async def _todo_oracle_reset_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `reset_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_reset_001_property_001 case_id=reset_001 oracle_case_id=property_reset_001 check_id=reset_001_property_001
    # Observed signals: Hours, Mins, Secs
    # Pass condition: No safety property is violated by treating reset as control-only; later functional claims require separate post-reset evidence.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_reset_001_property_001 case_id=reset_001 oracle_case_id=property_reset_001 check_id=reset_001_property_001

async def _todo_oracle_basic_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001
    # Observed signals: Hours, Mins, Secs
    # Pass condition: The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001
