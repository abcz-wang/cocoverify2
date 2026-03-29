"""Oracle helpers for `sub_64bit`.

This file is rendered from the structured oracle artifact. It intentionally keeps
checks conservative: timing windows are preserved, unresolved items stay visible,
and control signals are never reintroduced as business outputs.
"""

from __future__ import annotations

import json
from typing import Any

from .sub_64bit_runtime import assert_equal, assert_true, is_high_impedance, is_unknown, mask_width, to_sint, to_uint

CONTROL_SIGNALS = []
SIGNAL_WIDTHS = {'A': 64, 'B': 64, 'overflow': 1, 'result': 64}
ORACLE_SPEC = json.loads("{\n  \"functional_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.5700000000000001,\n          \"description\": \"required\",\n          \"expected_transition\": \"\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"result\",\n            \"overflow\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"result equals (A - B) modulo 2^64 and overflow flag follows signed overflow detection rule based on sign bits of A, B, and result\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [\n            \"operation_specific\",\n            \"ambiguity_preserving\"\n          ],\n          \"signal_policies\": {\n            \"overflow\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"definedness_mode\": \"at_observation\",\n              \"rationale\": \"explicit_output_behavior_downgraded_for_weak_contract\",\n              \"strength\": \"guarded\"\n            },\n            \"result\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": 0,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When inputs A and B are driven and outputs become stable\"\n        }\n      ],\n      \"confidence\": 0.5700000000000001,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [\n        \"Weak-contract path emits an explicit empty functional oracle case instead of guessing values.\"\n      ],\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": [\n        \"Value-level functional oracle for case 'basic_001' is intentionally deferred because timing or interface confidence is too weak.\"\n      ]\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [],\n      \"confidence\": 0.05,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [\n        \"Weak-contract path emits an explicit empty functional oracle case instead of guessing values.\"\n      ],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Value-level functional oracle for case 'edge_001' is intentionally deferred because timing or interface confidence is too weak.\"\n      ]\n    }\n  ],\n  \"property_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.54,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"result\",\n            \"overflow\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"overflow\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_output_behavior_downgraded_for_weak_contract\",\n              \"strength\": \"guarded\"\n            },\n            \"result\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"externally_visible_progress\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.54,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'basic_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.49,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"result\",\n            \"overflow\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"overflow\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_output_behavior_downgraded_for_weak_contract\",\n              \"strength\": \"guarded\"\n            },\n            \"result\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"externally_visible_progress\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.49,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'edge_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_metamorphic_001\",\n      \"category\": \"metamorphic\",\n      \"checks\": [\n        {\n          \"check_id\": \"metamorphic_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.42000000000000004,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"result\",\n            \"overflow\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"overflow\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_output_behavior_downgraded_for_weak_contract\",\n              \"strength\": \"guarded\"\n            },\n            \"result\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"externally_visible_progress\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.42000000000000004,\n      \"linked_plan_case_id\": \"metamorphic_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'metamorphic_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_back_to_back_001\",\n      \"category\": \"back_to_back\",\n      \"checks\": [\n        {\n          \"check_id\": \"back_to_back_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.4,\n          \"description\": \"Guardrail: repeated operations must not collapse into a single ambiguous completion claim.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Stability-style property used instead of throughput-specific claims.\"\n          ],\n          \"observed_signals\": [\n            \"result\",\n            \"overflow\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"overflow\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_output_behavior_downgraded_for_weak_contract\",\n              \"strength\": \"guarded\"\n            },\n            \"result\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"repeated_operations\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked case applies repeated or back-to-back operations.\"\n        }\n      ],\n      \"confidence\": 0.4,\n      \"linked_plan_case_id\": \"back_to_back_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'back_to_back_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    }\n  ],\n  \"protocol_oracles\": []\n}")
ORACLE_CASES_BY_PLAN = json.loads("{\n  \"back_to_back_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_back_to_back_001\",\n      \"category\": \"back_to_back\",\n      \"checks\": [\n        {\n          \"check_id\": \"back_to_back_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.4,\n          \"description\": \"Guardrail: repeated operations must not collapse into a single ambiguous completion claim.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Stability-style property used instead of throughput-specific claims.\"\n          ],\n          \"observed_signals\": [\n            \"result\",\n            \"overflow\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"overflow\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_output_behavior_downgraded_for_weak_contract\",\n              \"strength\": \"guarded\"\n            },\n            \"result\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"repeated_operations\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked case applies repeated or back-to-back operations.\"\n        }\n      ],\n      \"confidence\": 0.4,\n      \"linked_plan_case_id\": \"back_to_back_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'back_to_back_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    }\n  ],\n  \"basic_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.5700000000000001,\n          \"description\": \"required\",\n          \"expected_transition\": \"\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"result\",\n            \"overflow\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"result equals (A - B) modulo 2^64 and overflow flag follows signed overflow detection rule based on sign bits of A, B, and result\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [\n            \"operation_specific\",\n            \"ambiguity_preserving\"\n          ],\n          \"signal_policies\": {\n            \"overflow\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"definedness_mode\": \"at_observation\",\n              \"rationale\": \"explicit_output_behavior_downgraded_for_weak_contract\",\n              \"strength\": \"guarded\"\n            },\n            \"result\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": 0,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When inputs A and B are driven and outputs become stable\"\n        }\n      ],\n      \"confidence\": 0.5700000000000001,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [\n        \"Weak-contract path emits an explicit empty functional oracle case instead of guessing values.\"\n      ],\n      \"oracle_group\": \"functional\",\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": [\n        \"Value-level functional oracle for case 'basic_001' is intentionally deferred because timing or interface confidence is too weak.\"\n      ]\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.54,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"result\",\n            \"overflow\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"overflow\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_output_behavior_downgraded_for_weak_contract\",\n              \"strength\": \"guarded\"\n            },\n            \"result\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"externally_visible_progress\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.54,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'basic_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    }\n  ],\n  \"edge_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [],\n      \"confidence\": 0.05,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [\n        \"Weak-contract path emits an explicit empty functional oracle case instead of guessing values.\"\n      ],\n      \"oracle_group\": \"functional\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Value-level functional oracle for case 'edge_001' is intentionally deferred because timing or interface confidence is too weak.\"\n      ]\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.49,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"result\",\n            \"overflow\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"overflow\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_output_behavior_downgraded_for_weak_contract\",\n              \"strength\": \"guarded\"\n            },\n            \"result\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"externally_visible_progress\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.49,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'edge_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    }\n  ],\n  \"metamorphic_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_metamorphic_001\",\n      \"category\": \"metamorphic\",\n      \"checks\": [\n        {\n          \"check_id\": \"metamorphic_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.42000000000000004,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"result\",\n            \"overflow\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"overflow\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_output_behavior_downgraded_for_weak_contract\",\n              \"strength\": \"guarded\"\n            },\n            \"result\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"externally_visible_progress\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.42000000000000004,\n      \"linked_plan_case_id\": \"metamorphic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": [\n        \"Property oracle for case 'metamorphic_001' is acting as a guardrail because stronger functional semantics are not yet justified.\"\n      ]\n    }\n  ]\n}")
TEMPORAL_MODES = ['unbounded_safe']
UNRESOLVED_ITEMS = ['Timing model is unresolved; generated cases avoid fixed-latency checks.',
 'Contract strength is limited; generated cases favor safe observation over '
 'precise timing assumptions.',
 'Negative or illegal-input behavior is not planned because the contract does '
 'not provide reliable constraints.',
 'Timing remains unresolved; oracle checks avoid exact-cycle requirements and '
 'prefer event-based or safety-style windows.',
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
    if check.get("check_id") == 'basic_001_functional_001':
        await _todo_oracle_basic_001_functional_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'basic_001_property_001':
        await _todo_oracle_basic_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'edge_001_property_001':
        await _todo_oracle_edge_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'metamorphic_001_property_001':
        await _todo_oracle_metamorphic_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'back_to_back_001_property_001':
        await _todo_oracle_back_to_back_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return


async def _todo_oracle_basic_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001
    # Observed signals: result, overflow
    # Pass condition: result equals (A - B) modulo 2^64 and overflow flag follows signed overflow detection rule based on sign bits of A, B, and result
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001

async def _todo_oracle_basic_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001
    # Observed signals: result, overflow
    # Pass condition: The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001

async def _todo_oracle_edge_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001
    # Observed signals: result, overflow
    # Pass condition: The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001

async def _todo_oracle_metamorphic_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `metamorphic_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_metamorphic_001_property_001 case_id=metamorphic_001 oracle_case_id=property_metamorphic_001 check_id=metamorphic_001_property_001
    # Observed signals: result, overflow
    # Pass condition: The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_metamorphic_001_property_001 case_id=metamorphic_001 oracle_case_id=property_metamorphic_001 check_id=metamorphic_001_property_001

async def _todo_oracle_back_to_back_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `back_to_back_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_back_to_back_001_property_001 case_id=back_to_back_001 oracle_case_id=property_back_to_back_001 check_id=back_to_back_001_property_001
    # Observed signals: result, overflow
    # Pass condition: Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_back_to_back_001_property_001 case_id=back_to_back_001 oracle_case_id=property_back_to_back_001 check_id=back_to_back_001_property_001
