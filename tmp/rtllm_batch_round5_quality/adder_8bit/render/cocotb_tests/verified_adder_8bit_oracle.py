"""Oracle helpers for `verified_adder_8bit`.

This file is rendered from the structured oracle artifact. It intentionally keeps
checks conservative: timing windows are preserved, unresolved items stay visible,
and control signals are never reintroduced as business outputs.
"""

from __future__ import annotations

import json
from typing import Any

from .verified_adder_8bit_runtime import assert_equal, assert_true, is_high_impedance, is_unknown, mask_width, to_sint, to_uint

CONTROL_SIGNALS = []
SIGNAL_WIDTHS = {'a': 8, 'b': 8, 'cin': 1, 'cout': 1, 'sum': 8}
ORACLE_SPEC = json.loads("{\n  \"functional_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.6975,\n          \"description\": \"Observe that legal input changes are reflected on the observable outputs without state dependence.\",\n          \"notes\": [\n            \"Combinational functional oracle stays descriptive and avoids inventing a full truth table.\"\n          ],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked basic stimulus applies legal representative input patterns.\"\n        },\n        {\n          \"check_id\": \"basic_001_functional_002\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.7175,\n          \"description\": \"required\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"For each sampled input vector, sum must equal (a + b + cin) modulo 256 and cout must equal the carry out of the 9\\u2011bit addition.\",\n          \"semantic_tags\": [\n            \"operation_specific\",\n            \"ambiguity_preserving\"\n          ],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": 1,\n            \"min_cycles\": 0,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the basic stimulus applies a random legal input vector.\"\n        }\n      ],\n      \"confidence\": 0.7075,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.6275,\n          \"description\": \"Observe stable, externally consistent response to boundary-value input patterns.\",\n          \"notes\": [\n            \"Boundary oracle is value-oriented but intentionally generic.\"\n          ],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"Boundary-value outputs remain externally consistent and do not require hidden state or fixed-latency interpretation.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"rationale\": \"primary_data_output_guarded_definedness\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"boundary_inputs_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked edge case applies zero-like, one-like, or width-boundary patterns.\"\n        }\n      ],\n      \"confidence\": 0.6275,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"property_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6875,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.6875,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6375,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        },\n        {\n          \"check_id\": \"edge_001_property_002\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6675,\n          \"description\": \"Carry-out must be asserted when addition of maximum operands overflows.\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"When a = 0xFF, b = 0xFF, cin = 1, the observed sum must be 0xFF (mod 256) and cout must be 1.\",\n          \"semantic_tags\": [\n            \"width_sensitive\",\n            \"edge\",\n            \"ambiguity_preserving\"\n          ],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"boundary_inputs_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the edge case stimulus applies the maximum operand values.\"\n        }\n      ],\n      \"confidence\": 0.6525,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"source\": \"hybrid_llm_generated\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_back_to_back_001\",\n      \"category\": \"back_to_back\",\n      \"checks\": [\n        {\n          \"check_id\": \"back_to_back_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6675,\n          \"description\": \"Guardrail: repeated operations must not collapse into a single ambiguous completion claim.\",\n          \"notes\": [\n            \"Stability-style property used instead of throughput-specific claims.\"\n          ],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"repeated_operations\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked case applies repeated or back-to-back operations.\"\n        }\n      ],\n      \"confidence\": 0.6675,\n      \"linked_plan_case_id\": \"back_to_back_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"protocol_oracles\": []\n}")
ORACLE_CASES_BY_PLAN = json.loads("{\n  \"back_to_back_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_back_to_back_001\",\n      \"category\": \"back_to_back\",\n      \"checks\": [\n        {\n          \"check_id\": \"back_to_back_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6675,\n          \"description\": \"Guardrail: repeated operations must not collapse into a single ambiguous completion claim.\",\n          \"notes\": [\n            \"Stability-style property used instead of throughput-specific claims.\"\n          ],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"repeated_operations\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked case applies repeated or back-to-back operations.\"\n        }\n      ],\n      \"confidence\": 0.6675,\n      \"linked_plan_case_id\": \"back_to_back_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"basic_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.6975,\n          \"description\": \"Observe that legal input changes are reflected on the observable outputs without state dependence.\",\n          \"notes\": [\n            \"Combinational functional oracle stays descriptive and avoids inventing a full truth table.\"\n          ],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked basic stimulus applies legal representative input patterns.\"\n        },\n        {\n          \"check_id\": \"basic_001_functional_002\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.7175,\n          \"description\": \"required\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"For each sampled input vector, sum must equal (a + b + cin) modulo 256 and cout must equal the carry out of the 9\\u2011bit addition.\",\n          \"semantic_tags\": [\n            \"operation_specific\",\n            \"ambiguity_preserving\"\n          ],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": 1,\n            \"min_cycles\": 0,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the basic stimulus applies a random legal input vector.\"\n        }\n      ],\n      \"confidence\": 0.7075,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6875,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.6875,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"edge_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.6275,\n          \"description\": \"Observe stable, externally consistent response to boundary-value input patterns.\",\n          \"notes\": [\n            \"Boundary oracle is value-oriented but intentionally generic.\"\n          ],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"Boundary-value outputs remain externally consistent and do not require hidden state or fixed-latency interpretation.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": false,\n              \"allow_unknown\": false,\n              \"rationale\": \"primary_data_output_guarded_definedness\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"boundary_inputs_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked edge case applies zero-like, one-like, or width-boundary patterns.\"\n        }\n      ],\n      \"confidence\": 0.6275,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6375,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        },\n        {\n          \"check_id\": \"edge_001_property_002\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6675,\n          \"description\": \"Carry-out must be asserted when addition of maximum operands overflows.\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"sum\",\n            \"cout\"\n          ],\n          \"pass_condition\": \"When a = 0xFF, b = 0xFF, cin = 1, the observed sum must be 0xFF (mod 256) and cout must be 1.\",\n          \"semantic_tags\": [\n            \"width_sensitive\",\n            \"edge\",\n            \"ambiguity_preserving\"\n          ],\n          \"signal_policies\": {\n            \"cout\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"sum\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"boundary_inputs_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the edge case stimulus applies the maximum operand values.\"\n        }\n      ],\n      \"confidence\": 0.6525,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"hybrid_llm_generated\",\n      \"unresolved_items\": []\n    }\n  ]\n}")
TEMPORAL_MODES = ['event_based', 'unbounded_safe']
UNRESOLVED_ITEMS = []


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
        value = sampled_outputs.get(signal_name)
        if value is None or strength == "unresolved":
            skipped_signals.append(signal_name)
            continue
        if not bool(policy.get("allow_unknown", True)):
            assert_true(not is_unknown(value), f"{signal_name} must not be unknown under structured oracle policy")
        if not bool(policy.get("allow_high_impedance", True)):
            assert_true(
                not is_high_impedance(value),
                f"{signal_name} must not be high-impedance under structured oracle policy",
            )
        checked_signals.append(signal_name)

    return {
        "status": "policy_checked" if checked_signals else "policy_guarded_only",
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
    if check.get("check_id") == 'basic_001_functional_002':
        await _todo_oracle_basic_001_functional_002(env, plan_case_id, oracle_case_id, check, observed_signals)
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
    if check.get("check_id") == 'edge_001_property_002':
        await _todo_oracle_edge_001_property_002(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'back_to_back_001_property_001':
        await _todo_oracle_back_to_back_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return


async def _todo_oracle_basic_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001
    # Observed signals: sum, cout
    # Pass condition: Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001

async def _todo_oracle_basic_001_functional_002(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_functional_002`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_002 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_002
    # Observed signals: sum, cout
    # Pass condition: For each sampled input vector, sum must equal (a + b + cin) modulo 256 and cout must equal the carry out of the 9‑bit addition.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_002 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_002

async def _todo_oracle_edge_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_functional_001 case_id=edge_001 oracle_case_id=functional_edge_001 check_id=edge_001_functional_001
    # Observed signals: sum, cout
    # Pass condition: Boundary-value outputs remain externally consistent and do not require hidden state or fixed-latency interpretation.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_functional_001 case_id=edge_001 oracle_case_id=functional_edge_001 check_id=edge_001_functional_001

async def _todo_oracle_basic_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001
    # Observed signals: sum, cout
    # Pass condition: The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001

async def _todo_oracle_edge_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001
    # Observed signals: sum, cout
    # Pass condition: The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001

async def _todo_oracle_edge_001_property_002(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_property_002`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_property_002 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_002
    # Observed signals: sum, cout
    # Pass condition: When a = 0xFF, b = 0xFF, cin = 1, the observed sum must be 0xFF (mod 256) and cout must be 1.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_property_002 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_002

async def _todo_oracle_back_to_back_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `back_to_back_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_back_to_back_001_property_001 case_id=back_to_back_001 oracle_case_id=property_back_to_back_001 check_id=back_to_back_001_property_001
    # Observed signals: sum, cout
    # Pass condition: Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_back_to_back_001_property_001 case_id=back_to_back_001 oracle_case_id=property_back_to_back_001 check_id=back_to_back_001_property_001
