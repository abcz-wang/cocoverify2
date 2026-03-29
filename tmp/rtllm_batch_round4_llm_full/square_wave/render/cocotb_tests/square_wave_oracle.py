"""Oracle helpers for `square_wave`.

This file is rendered from the structured oracle artifact. It intentionally keeps
checks conservative: timing windows are preserved, unresolved items stay visible,
and control signals are never reintroduced as business outputs.
"""

from __future__ import annotations

import json
from typing import Any

from .square_wave_runtime import assert_equal, assert_true, is_high_impedance, is_unknown, mask_width, to_sint, to_uint

CONTROL_SIGNALS = ['clk']
SIGNAL_WIDTHS = {'clk': 1, 'freq': 8, 'wave_out': 1}
ORACLE_SPEC = json.loads("{\n  \"functional_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.765,\n          \"description\": \"Observe externally visible state progress after a legal operation.\",\n          \"notes\": [\n            \"Sequential functional oracle remains event-based unless a future contract explicitly provides fixed latency.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"At least one observable output or progress indicator eventually updates in a manner consistent with state progress; no exact-cycle update is required.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked plan applies one or more legal sequential operations.\"\n        },\n        {\n          \"check_id\": \"basic_001_functional_002\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.805,\n          \"description\": \"wave_out must toggle at least once within a conservative observation window after freq is applied.\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"wave_out changes value (0\\u21921 or 1\\u21920) at least once within the bounded observation window.\",\n          \"semantic_tags\": [\n            \"ambiguity_preserving\",\n            \"operation_specific\"\n          ],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": 512,\n            \"min_cycles\": 0,\n            \"mode\": \"bounded_range\"\n          },\n          \"trigger_condition\": \"When freq input is driven to a non-zero value.\"\n        }\n      ],\n      \"confidence\": 0.785,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.715,\n          \"description\": \"Observe externally visible state progress after a legal operation.\",\n          \"notes\": [\n            \"Sequential functional oracle remains event-based unless a future contract explicitly provides fixed latency.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"At least one observable output or progress indicator eventually updates in a manner consistent with state progress; no exact-cycle update is required.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked plan applies one or more legal sequential operations.\"\n        }\n      ],\n      \"confidence\": 0.715,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_back_to_back_001\",\n      \"category\": \"back_to_back\",\n      \"checks\": [\n        {\n          \"check_id\": \"back_to_back_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.685,\n          \"description\": \"Observe externally visible state progress after a legal operation.\",\n          \"notes\": [\n            \"Sequential functional oracle remains event-based unless a future contract explicitly provides fixed latency.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"At least one observable output or progress indicator eventually updates in a manner consistent with state progress; no exact-cycle update is required.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked plan applies one or more legal sequential operations.\"\n        }\n      ],\n      \"confidence\": 0.685,\n      \"linked_plan_case_id\": \"back_to_back_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"property_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.775,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.775,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.725,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        },\n        {\n          \"check_id\": \"edge_001_property_002\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.755,\n          \"description\": \"wave_out must never become X or Z for any legal freq value.\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"wave_out remains 0 or 1 throughout the observation period.\",\n          \"semantic_tags\": [\n            \"ambiguity_preserving\",\n            \"width_sensitive\"\n          ],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": 512,\n            \"min_cycles\": 0,\n            \"mode\": \"bounded_range\"\n          },\n          \"trigger_condition\": \"During any stimulus where freq is driven within [0,255].\"\n        }\n      ],\n      \"confidence\": 0.74,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_back_to_back_001\",\n      \"category\": \"back_to_back\",\n      \"checks\": [\n        {\n          \"check_id\": \"back_to_back_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.675,\n          \"description\": \"Guardrail: repeated operations must not collapse into a single ambiguous completion claim.\",\n          \"notes\": [\n            \"Stability-style property used instead of throughput-specific claims.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"repeated_operations\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked case applies repeated or back-to-back operations.\"\n        }\n      ],\n      \"confidence\": 0.675,\n      \"linked_plan_case_id\": \"back_to_back_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_negative_001\",\n      \"category\": \"negative\",\n      \"checks\": [\n        {\n          \"check_id\": \"negative_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.745,\n          \"description\": \"Guardrail: illegal or constrained inputs do not require normal completion or success signaling.\",\n          \"notes\": [\n            \"Negative behavior is guarded by explicit contract constraints only.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"The oracle only requires safe non-violation behavior and does not invent undocumented error responses.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"negative_or_illegal_case_preserves_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"illegal_input_observation\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked plan probes documented illegal or constrained inputs.\"\n        }\n      ],\n      \"confidence\": 0.745,\n      \"linked_plan_case_id\": \"negative_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_metamorphic_001\",\n      \"category\": \"metamorphic\",\n      \"checks\": [\n        {\n          \"check_id\": \"metamorphic_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.775,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.775,\n      \"linked_plan_case_id\": \"metamorphic_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"protocol_oracles\": []\n}")
ORACLE_CASES_BY_PLAN = json.loads("{\n  \"back_to_back_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_back_to_back_001\",\n      \"category\": \"back_to_back\",\n      \"checks\": [\n        {\n          \"check_id\": \"back_to_back_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.685,\n          \"description\": \"Observe externally visible state progress after a legal operation.\",\n          \"notes\": [\n            \"Sequential functional oracle remains event-based unless a future contract explicitly provides fixed latency.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"At least one observable output or progress indicator eventually updates in a manner consistent with state progress; no exact-cycle update is required.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked plan applies one or more legal sequential operations.\"\n        }\n      ],\n      \"confidence\": 0.685,\n      \"linked_plan_case_id\": \"back_to_back_001\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_back_to_back_001\",\n      \"category\": \"back_to_back\",\n      \"checks\": [\n        {\n          \"check_id\": \"back_to_back_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.675,\n          \"description\": \"Guardrail: repeated operations must not collapse into a single ambiguous completion claim.\",\n          \"notes\": [\n            \"Stability-style property used instead of throughput-specific claims.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"repeated_operations\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked case applies repeated or back-to-back operations.\"\n        }\n      ],\n      \"confidence\": 0.675,\n      \"linked_plan_case_id\": \"back_to_back_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"basic_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.765,\n          \"description\": \"Observe externally visible state progress after a legal operation.\",\n          \"notes\": [\n            \"Sequential functional oracle remains event-based unless a future contract explicitly provides fixed latency.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"At least one observable output or progress indicator eventually updates in a manner consistent with state progress; no exact-cycle update is required.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked plan applies one or more legal sequential operations.\"\n        },\n        {\n          \"check_id\": \"basic_001_functional_002\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.805,\n          \"description\": \"wave_out must toggle at least once within a conservative observation window after freq is applied.\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"wave_out changes value (0\\u21921 or 1\\u21920) at least once within the bounded observation window.\",\n          \"semantic_tags\": [\n            \"ambiguity_preserving\",\n            \"operation_specific\"\n          ],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": 512,\n            \"min_cycles\": 0,\n            \"mode\": \"bounded_range\"\n          },\n          \"trigger_condition\": \"When freq input is driven to a non-zero value.\"\n        }\n      ],\n      \"confidence\": 0.785,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.775,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.775,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"edge_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.715,\n          \"description\": \"Observe externally visible state progress after a legal operation.\",\n          \"notes\": [\n            \"Sequential functional oracle remains event-based unless a future contract explicitly provides fixed latency.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"At least one observable output or progress indicator eventually updates in a manner consistent with state progress; no exact-cycle update is required.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked plan applies one or more legal sequential operations.\"\n        }\n      ],\n      \"confidence\": 0.715,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.725,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        },\n        {\n          \"check_id\": \"edge_001_property_002\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.755,\n          \"description\": \"wave_out must never become X or Z for any legal freq value.\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"wave_out remains 0 or 1 throughout the observation period.\",\n          \"semantic_tags\": [\n            \"ambiguity_preserving\",\n            \"width_sensitive\"\n          ],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": 512,\n            \"min_cycles\": 0,\n            \"mode\": \"bounded_range\"\n          },\n          \"trigger_condition\": \"During any stimulus where freq is driven within [0,255].\"\n        }\n      ],\n      \"confidence\": 0.74,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"metamorphic_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_metamorphic_001\",\n      \"category\": \"metamorphic\",\n      \"checks\": [\n        {\n          \"check_id\": \"metamorphic_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.775,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.775,\n      \"linked_plan_case_id\": \"metamorphic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"negative_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_negative_001\",\n      \"category\": \"negative\",\n      \"checks\": [\n        {\n          \"check_id\": \"negative_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.745,\n          \"description\": \"Guardrail: illegal or constrained inputs do not require normal completion or success signaling.\",\n          \"notes\": [\n            \"Negative behavior is guarded by explicit contract constraints only.\"\n          ],\n          \"observed_signals\": [\n            \"wave_out\"\n          ],\n          \"pass_condition\": \"The oracle only requires safe non-violation behavior and does not invent undocumented error responses.\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"wave_out\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"rationale\": \"negative_or_illegal_case_preserves_ambiguity\",\n              \"strength\": \"unresolved\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"illegal_input_observation\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked plan probes documented illegal or constrained inputs.\"\n        }\n      ],\n      \"confidence\": 0.745,\n      \"linked_plan_case_id\": \"negative_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ]\n}")
TEMPORAL_MODES = ['bounded_range', 'event_based', 'unbounded_safe']
UNRESOLVED_ITEMS = ['Spec/reset hint could not be mapped to a known reset port: When count '
 'reaches (freq - 1), the count is reset to 0 and wave_out is toggled (i.e., '
 'flipped from 0 to 1 or from 1 to 0).',
 'Spec/reset hint could not be mapped to a known reset port: When count '
 'reaches (freq - 1), the count is reset to 0 and wave_out is toggled.']


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
    if check.get("check_id") == 'back_to_back_001_functional_001':
        await _todo_oracle_back_to_back_001_functional_001(env, plan_case_id, oracle_case_id, check, observed_signals)
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
    if check.get("check_id") == 'negative_001_property_001':
        await _todo_oracle_negative_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'metamorphic_001_property_001':
        await _todo_oracle_metamorphic_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return


async def _todo_oracle_basic_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001
    # Observed signals: wave_out
    # Pass condition: At least one observable output or progress indicator eventually updates in a manner consistent with state progress; no exact-cycle update is required.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001

async def _todo_oracle_basic_001_functional_002(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_functional_002`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_002 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_002
    # Observed signals: wave_out
    # Pass condition: wave_out changes value (0→1 or 1→0) at least once within the bounded observation window.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_002 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_002

async def _todo_oracle_edge_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_functional_001 case_id=edge_001 oracle_case_id=functional_edge_001 check_id=edge_001_functional_001
    # Observed signals: wave_out
    # Pass condition: At least one observable output or progress indicator eventually updates in a manner consistent with state progress; no exact-cycle update is required.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_functional_001 case_id=edge_001 oracle_case_id=functional_edge_001 check_id=edge_001_functional_001

async def _todo_oracle_back_to_back_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `back_to_back_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_back_to_back_001_functional_001 case_id=back_to_back_001 oracle_case_id=functional_back_to_back_001 check_id=back_to_back_001_functional_001
    # Observed signals: wave_out
    # Pass condition: At least one observable output or progress indicator eventually updates in a manner consistent with state progress; no exact-cycle update is required.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_back_to_back_001_functional_001 case_id=back_to_back_001 oracle_case_id=functional_back_to_back_001 check_id=back_to_back_001_functional_001

async def _todo_oracle_basic_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001
    # Observed signals: wave_out
    # Pass condition: The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001

async def _todo_oracle_edge_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001
    # Observed signals: wave_out
    # Pass condition: The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001

async def _todo_oracle_edge_001_property_002(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_property_002`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_property_002 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_002
    # Observed signals: wave_out
    # Pass condition: wave_out remains 0 or 1 throughout the observation period.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_property_002 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_002

async def _todo_oracle_back_to_back_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `back_to_back_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_back_to_back_001_property_001 case_id=back_to_back_001 oracle_case_id=property_back_to_back_001 check_id=back_to_back_001_property_001
    # Observed signals: wave_out
    # Pass condition: Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_back_to_back_001_property_001 case_id=back_to_back_001 oracle_case_id=property_back_to_back_001 check_id=back_to_back_001_property_001

async def _todo_oracle_negative_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `negative_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_negative_001_property_001 case_id=negative_001 oracle_case_id=property_negative_001 check_id=negative_001_property_001
    # Observed signals: wave_out
    # Pass condition: The oracle only requires safe non-violation behavior and does not invent undocumented error responses.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_negative_001_property_001 case_id=negative_001 oracle_case_id=property_negative_001 check_id=negative_001_property_001

async def _todo_oracle_metamorphic_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `metamorphic_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_metamorphic_001_property_001 case_id=metamorphic_001 oracle_case_id=property_metamorphic_001 check_id=metamorphic_001_property_001
    # Observed signals: wave_out
    # Pass condition: The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_metamorphic_001_property_001 case_id=metamorphic_001 oracle_case_id=property_metamorphic_001 check_id=metamorphic_001_property_001
