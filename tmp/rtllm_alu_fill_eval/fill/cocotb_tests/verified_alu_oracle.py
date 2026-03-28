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
ORACLE_SPEC = json.loads("{\n  \"functional_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.7475,\n          \"description\": \"Observe that legal input changes are reflected on the observable outputs without state dependence.\",\n          \"notes\": [\n            \"Combinational functional oracle stays descriptive and avoids inventing a full truth table.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked basic stimulus applies legal representative input patterns.\"\n        },\n        {\n          \"check_id\": \"basic_001_functional_002\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.7675000000000001,\n          \"description\": \"required\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Outputs reflect combinational function of inputs a, b, aluc without dependence on hidden state.\",\n          \"semantic_tags\": [\n            \"snake_case_tags\"\n          ],\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": 1,\n            \"min_cycles\": 0,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever basic_001 stimulus is applied.\"\n        }\n      ],\n      \"confidence\": 0.7575000000000001,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.6775,\n          \"description\": \"Observe stable, externally consistent response to boundary-value input patterns.\",\n          \"notes\": [\n            \"Boundary oracle is value-oriented but intentionally generic.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Boundary-value outputs remain externally consistent and do not require hidden state or fixed-latency interpretation.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"boundary_inputs_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked edge case applies zero-like, one-like, or width-boundary patterns.\"\n        }\n      ],\n      \"confidence\": 0.6775,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_002\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_002_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.7475,\n          \"description\": \"Observe that legal input changes are reflected on the observable outputs without state dependence.\",\n          \"notes\": [\n            \"Combinational functional oracle stays descriptive and avoids inventing a full truth table.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked basic stimulus applies legal representative input patterns.\"\n        }\n      ],\n      \"confidence\": 0.7475,\n      \"linked_plan_case_id\": \"basic_002\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"property_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7375,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.7375,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6875,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        },\n        {\n          \"check_id\": \"edge_001_property_002\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7175,\n          \"description\": \"Boundary inputs must not cause illegal state; outputs remain defined (z for r, others zero/unknown) when opcode is undefined.\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"When aluc is outside defined opcodes, r is high-impedance (z) and all flag signals are 0 or z, with no assertion violation.\",\n          \"semantic_tags\": [\n            \"invalid_illegal_input\",\n            \"width_sensitive\"\n          ],\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Applied when aluc = 6'b111111 (or any undefined opcode).\"\n        }\n      ],\n      \"confidence\": 0.7025,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"source\": \"hybrid_llm_generated\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_002\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_002_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7375,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.7375,\n      \"linked_plan_case_id\": \"basic_002\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_negative_001\",\n      \"category\": \"negative\",\n      \"checks\": [\n        {\n          \"check_id\": \"negative_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7075,\n          \"description\": \"Guardrail: illegal or constrained inputs do not require normal completion or success signaling.\",\n          \"notes\": [\n            \"Negative behavior is guarded by explicit contract constraints only.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires safe non-violation behavior and does not invent undocumented error responses.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"illegal_input_observation\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked plan probes documented illegal or constrained inputs.\"\n        }\n      ],\n      \"confidence\": 0.7075,\n      \"linked_plan_case_id\": \"negative_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_back_to_back_001\",\n      \"category\": \"back_to_back\",\n      \"checks\": [\n        {\n          \"check_id\": \"back_to_back_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7175,\n          \"description\": \"Guardrail: repeated operations must not collapse into a single ambiguous completion claim.\",\n          \"notes\": [\n            \"Stability-style property used instead of throughput-specific claims.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"repeated_operations\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked case applies repeated or back-to-back operations.\"\n        }\n      ],\n      \"confidence\": 0.7175,\n      \"linked_plan_case_id\": \"back_to_back_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"protocol_oracles\": []\n}")
ORACLE_CASES_BY_PLAN = json.loads("{\n  \"back_to_back_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_back_to_back_001\",\n      \"category\": \"back_to_back\",\n      \"checks\": [\n        {\n          \"check_id\": \"back_to_back_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7175,\n          \"description\": \"Guardrail: repeated operations must not collapse into a single ambiguous completion claim.\",\n          \"notes\": [\n            \"Stability-style property used instead of throughput-specific claims.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"repeated_operations\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked case applies repeated or back-to-back operations.\"\n        }\n      ],\n      \"confidence\": 0.7175,\n      \"linked_plan_case_id\": \"back_to_back_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"basic_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.7475,\n          \"description\": \"Observe that legal input changes are reflected on the observable outputs without state dependence.\",\n          \"notes\": [\n            \"Combinational functional oracle stays descriptive and avoids inventing a full truth table.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked basic stimulus applies legal representative input patterns.\"\n        },\n        {\n          \"check_id\": \"basic_001_functional_002\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.7675000000000001,\n          \"description\": \"required\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Outputs reflect combinational function of inputs a, b, aluc without dependence on hidden state.\",\n          \"semantic_tags\": [\n            \"snake_case_tags\"\n          ],\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": 1,\n            \"min_cycles\": 0,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever basic_001 stimulus is applied.\"\n        }\n      ],\n      \"confidence\": 0.7575000000000001,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7375,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.7375,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"basic_002\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_002\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_002_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.7475,\n          \"description\": \"Observe that legal input changes are reflected on the observable outputs without state dependence.\",\n          \"notes\": [\n            \"Combinational functional oracle stays descriptive and avoids inventing a full truth table.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked basic stimulus applies legal representative input patterns.\"\n        }\n      ],\n      \"confidence\": 0.7475,\n      \"linked_plan_case_id\": \"basic_002\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_002\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_002_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7375,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.7375,\n      \"linked_plan_case_id\": \"basic_002\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"edge_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"confidence\": 0.6775,\n          \"description\": \"Observe stable, externally consistent response to boundary-value input patterns.\",\n          \"notes\": [\n            \"Boundary oracle is value-oriented but intentionally generic.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"Boundary-value outputs remain externally consistent and do not require hidden state or fixed-latency interpretation.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"boundary_inputs_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked edge case applies zero-like, one-like, or width-boundary patterns.\"\n        }\n      ],\n      \"confidence\": 0.6775,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.6875,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        },\n        {\n          \"check_id\": \"edge_001_property_002\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7175,\n          \"description\": \"Boundary inputs must not cause illegal state; outputs remain defined (z for r, others zero/unknown) when opcode is undefined.\",\n          \"notes\": [],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"When aluc is outside defined opcodes, r is high-impedance (z) and all flag signals are 0 or z, with no assertion violation.\",\n          \"semantic_tags\": [\n            \"invalid_illegal_input\",\n            \"width_sensitive\"\n          ],\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Applied when aluc = 6'b111111 (or any undefined opcode).\"\n        }\n      ],\n      \"confidence\": 0.7025,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"hybrid_llm_generated\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"negative_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_negative_001\",\n      \"category\": \"negative\",\n      \"checks\": [\n        {\n          \"check_id\": \"negative_001_property_001\",\n          \"check_type\": \"property\",\n          \"confidence\": 0.7075,\n          \"description\": \"Guardrail: illegal or constrained inputs do not require normal completion or success signaling.\",\n          \"notes\": [\n            \"Negative behavior is guarded by explicit contract constraints only.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"pass_condition\": \"The oracle only requires safe non-violation behavior and does not invent undocumented error responses.\",\n          \"semantic_tags\": [],\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"illegal_input_observation\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"unbounded_safe\"\n          },\n          \"trigger_condition\": \"When the linked plan probes documented illegal or constrained inputs.\"\n        }\n      ],\n      \"confidence\": 0.7075,\n      \"linked_plan_case_id\": \"negative_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ]\n}")
TEMPORAL_MODES = ['event_based', 'unbounded_safe']
UNRESOLVED_ITEMS = []


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
    if check.get("check_id") == 'basic_001_functional_002':
        await _todo_oracle_basic_001_functional_002(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'edge_001_functional_001':
        await _todo_oracle_edge_001_functional_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'basic_002_functional_001':
        await _todo_oracle_basic_002_functional_001(env, plan_case_id, oracle_case_id, check, observed_signals)
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
    if check.get("check_id") == 'basic_002_property_001':
        await _todo_oracle_basic_002_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'negative_001_property_001':
        await _todo_oracle_negative_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return
    if check.get("check_id") == 'back_to_back_001_property_001':
        await _todo_oracle_back_to_back_001_property_001(env, plan_case_id, oracle_case_id, check, observed_signals)
        return


async def _todo_oracle_basic_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001
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
    # Basic sanity checks
    assert_true(0 <= r < (1 << env.signal_width('r')), 'Result r out of 32-bit range')
    expected_zero = 1 if r == 0 else 0
    assert_equal('zero', zero, expected_zero)
    expected_negative = (r >> (env.signal_width('r') - 1)) & 1
    assert_equal('negative', negative, expected_negative)
    # flag is only defined for SLT (0b101010) and SLTU (0b101011)
    SLT = 0b101010
    SLTU = 0b101011
    if aluc in (SLT, SLTU):
        assert_equal('flag', flag, 1)
    else:
        assert_true(is_high_impedance(flag), f'flag should be high‑impedance for aluc {aluc:#06b}')
    # carry and overflow should be defined (not unknown) for all opcodes
    assert_true(not is_unknown(carry), 'carry is unknown')
    assert_true(not is_unknown(overflow), 'overflow is unknown')
    # Record note of applied inputs for debugging
    env.record_case_note(plan_case_id, f'Applied a=0x{a:08x}, b=0x{b:08x}, aluc={aluc:#06b}')
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001

async def _todo_oracle_basic_001_functional_002(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_functional_002`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_002 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_002
    inputs = env.get_case_inputs(plan_case_id)
    a = inputs['a']
    b = inputs['b']
    aluc = inputs['aluc']
    outputs = await env.sample_outputs(observed_signals)
    r = outputs.get('r')
    zero = outputs.get('zero')
    carry = outputs.get('carry')
    negative = outputs.get('negative')
    overflow = outputs.get('overflow')
    flag = outputs.get('flag')
    width = env.signal_width('r')
    mask = (1 << width) - 1
    assert_true(0 <= r <= mask, 'Result r out of range')
    expected_zero = 1 if r == 0 else 0
    assert_equal('zero', zero, expected_zero)
    expected_negative = (r >> (width - 1)) & 1
    assert_equal('negative', negative, expected_negative)
    SLT = 0b101010
    SLTU = 0b101011
    ADD = 0b100000
    ADDU = 0b100001
    SUB = 0b100010
    SUBU = 0b100011
    AND = 0b100100
    OR = 0b100101
    XOR = 0b100110
    NOR = 0b100111
    SLL = 0b000000
    SRL = 0b000010
    SRA = 0b000011
    SLLV = 0b000100
    SRLV = 0b000110
    SRAV = 0b000111
    LUI = 0b001111
    if aluc == SLT:
        expected_flag = 1 if to_sint(a, width) < to_sint(b, width) else 0
        assert_equal('flag', flag, expected_flag)
    elif aluc == SLTU:
        expected_flag = 1 if a < b else 0
        assert_equal('flag', flag, expected_flag)
    else:
        assert_true(is_high_impedance(flag), f'flag should be high‑impedance for aluc {aluc:#06b}')
    if aluc in (ADD, ADDU):
        expected_r = (a + b) & mask
        assert_equal('r', r, expected_r)
        expected_carry = 1 if (a + b) >> width else 0
        assert_equal('carry', carry, expected_carry)
        if aluc == ADD:
            a_s = to_sint(a, width)
            b_s = to_sint(b, width)
            r_s = to_sint(r, width)
            overflow_cond = ((a_s > 0 and b_s > 0 and r_s < 0) or (a_s < 0 and b_s < 0 and r_s >= 0))
            expected_overflow = 1 if overflow_cond else 0
            assert_equal('overflow', overflow, expected_overflow)
        else:
            assert_true(not is_unknown(overflow), 'overflow must be defined for ADDU')
    elif aluc in (SUB, SUBU):
        expected_r = (a - b) & mask
        assert_equal('r', r, expected_r)
        if aluc == SUB:
            a_s = to_sint(a, width)
            b_s = to_sint(b, width)
            r_s = to_sint(r, width)
            overflow_cond = ((a_s > 0 and b_s < 0 and r_s < 0) or (a_s < 0 and b_s > 0 and r_s >= 0))
            expected_overflow = 1 if overflow_cond else 0
            assert_equal('overflow', overflow, expected_overflow)
        else:
            assert_true(not is_unknown(overflow), 'overflow must be defined for SUBU')
    elif aluc == AND:
        expected_r = a & b
        assert_equal('r', r, expected_r)
    elif aluc == OR:
        expected_r = a | b
        assert_equal('r', r, expected_r)
    elif aluc == XOR:
        expected_r = a ^ b
        assert_equal('r', r, expected_r)
    elif aluc == NOR:
        expected_r = (~(a | b)) & mask
        assert_equal('r', r, expected_r)
    elif aluc == SLL:
        shamt = a & 0x1F
        expected_r = (b << shamt) & mask
        assert_equal('r', r, expected_r)
    elif aluc == SRL:
        shamt = a & 0x1F
        expected_r = (b >> shamt) & mask
        assert_equal('r', r, expected_r)
    elif aluc == SRA:
        shamt = a & 0x1F
        b_s = to_sint(b, width)
        expected_r = (b_s >> shamt) & mask
        assert_equal('r', r, expected_r)
    elif aluc == SLLV:
        shamt = b & 0x1F
        expected_r = (a << shamt) & mask
        assert_equal('r', r, expected_r)
    elif aluc == SRLV:
        shamt = b & 0x1F
        expected_r = (a >> shamt) & mask
        assert_equal('r', r, expected_r)
    elif aluc == SRAV:
        shamt = b & 0x1F
        a_s = to_sint(a, width)
        expected_r = (a_s >> shamt) & mask
        assert_equal('r', r, expected_r)
    elif aluc == LUI:
        expected_r = (a << 16) & mask
        assert_equal('r', r, expected_r)
    else:
        assert_true(is_high_impedance(r), f'r should be high‑impedance for unknown aluc {aluc:#06b}')
    assert_true(not is_unknown(carry), 'carry must be defined')
    assert_true(not is_unknown(overflow), 'overflow must be defined')
    env.record_case_note(plan_case_id, f'Applied a=0x{a:08x}, b=0x{b:08x}, aluc={aluc:#06b}')
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_002 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_002

async def _todo_oracle_edge_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_functional_001 case_id=edge_001 oracle_case_id=functional_edge_001 check_id=edge_001_functional_001
    inputs = env.get_case_inputs(plan_case_id)
    a = inputs.get('a', 0)
    b = inputs.get('b', 0)
    aluc = inputs.get('aluc', 0)
    outputs = await env.sample_outputs(observed_signals)
    r = outputs.get('r')
    zero = outputs.get('zero')
    carry = outputs.get('carry')
    negative = outputs.get('negative')
    overflow = outputs.get('overflow')
    flag = outputs.get('flag')
    mask = mask_width(32)
    known_opcodes = {
        0b100000,  # ADD
        0b100001,  # ADDU
        0b100010,  # SUB
        0b100011,  # SUBU
        0b100100,  # AND
        0b100101,  # OR
        0b100110,  # XOR
        0b100111,  # NOR
        0b101010,  # SLT
        0b101011,  # SLTU
        0b000000,  # SLL
        0b000010,  # SRL
        0b000011,  # SRA
        0b000100,  # SLLV
        0b000110,  # SRLV
        0b000111,  # SRAV
        0b001111   # LUI
    }
    if aluc not in known_opcodes:
        assert_true(is_high_impedance(r), f'r should be high‑impedance for unknown aluc {aluc:#06b}')
        assert_true(is_high_impedance(flag), f'flag should be high‑impedance for unknown aluc {aluc:#06b}')
    else:
        # Compute expected result for each supported opcode
        if aluc == 0b100000:  # ADD (signed)
            a_s = to_sint(a, 32)
            b_s = to_sint(b, 32)
            sum_s = a_s + b_s
            expected_r = to_uint(sum_s, 32)
            expected_carry = int((a + b) > mask)
            expected_overflow = int(((a_s > 0 and b_s > 0 and sum_s < 0) or (a_s < 0 and b_s < 0 and sum_s >= 0)))
        elif aluc == 0b100001:  # ADDU (unsigned)
            expected_r = (a + b) & mask
            expected_carry = int((a + b) > mask)
            expected_overflow = 0
        elif aluc == 0b100010:  # SUB (signed)
            a_s = to_sint(a, 32)
            b_s = to_sint(b, 32)
            diff_s = a_s - b_s
            expected_r = to_uint(diff_s, 32)
            expected_carry = int(a < b)
            expected_overflow = int(((a_s > 0 and b_s < 0 and diff_s < 0) or (a_s < 0 and b_s > 0 and diff_s >= 0)))
        elif aluc == 0b100011:  # SUBU (unsigned)
            expected_r = (a - b) & mask
            expected_carry = int(a < b)
            expected_overflow = 0
        elif aluc == 0b100100:  # AND
            expected_r = a & b
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b100101:  # OR
            expected_r = a | b
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b100110:  # XOR
            expected_r = a ^ b
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b100111:  # NOR
            expected_r = (~(a | b)) & mask
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b101010:  # SLT (signed)
            a_s = to_sint(a, 32)
            b_s = to_sint(b, 32)
            expected_flag = int(a_s < b_s)
            expected_r = 0
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b101011:  # SLTU (unsigned)
            expected_flag = int(a < b)
            expected_r = 0
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b000000:  # SLL (shift amount from lower 5 bits of a)
            shamt = a & 0x1F
            expected_r = (b << shamt) & mask
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b000010:  # SRL
            shamt = a & 0x1F
            expected_r = (b >> shamt) & mask
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b000011:  # SRA
            shamt = a & 0x1F
            b_s = to_sint(b, 32)
            expected_r = (b_s >> shamt) & mask
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b000100:  # SLLV (shift amount from lower 5 bits of b)
            shamt = b & 0x1F
            expected_r = (a << shamt) & mask
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b000110:  # SRLV
            shamt = b & 0x1F
            expected_r = (a >> shamt) & mask
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b000111:  # SRAV
            shamt = b & 0x1F
            a_s = to_sint(a, 32)
            expected_r = (a_s >> shamt) & mask
            expected_carry = 0
            expected_overflow = 0
        elif aluc == 0b001111:  # LUI
            expected_r = (a << 16) & mask
            expected_carry = 0
            expected_overflow = 0
        # Verify result and status flags
        assert_equal('r', r, expected_r)
        assert_equal('zero', zero, int(expected_r == 0))
        assert_equal('negative', negative, int((expected_r >> 31) & 1))
        assert_true(not is_unknown(carry), 'carry must be defined')
        assert_true(not is_unknown(overflow), 'overflow must be defined')
        assert_equal('carry', carry, expected_carry)
        assert_equal('overflow', overflow, expected_overflow)
        if aluc == 0b101010:
            assert_equal('flag', flag, expected_flag)
        elif aluc == 0b101011:
            assert_equal('flag', flag, expected_flag)
        else:
            assert_true(is_high_impedance(flag), f'flag should be high‑impedance for aluc {aluc:#06b}')
        env.record_case_note(plan_case_id, f'Edge functional check: a=0x{a:08x}, b=0x{b:08x}, aluc={aluc:#06b}')
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_functional_001 case_id=edge_001 oracle_case_id=functional_edge_001 check_id=edge_001_functional_001

async def _todo_oracle_basic_002_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_002_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_002_functional_001 case_id=basic_002 oracle_case_id=functional_basic_002 check_id=basic_002_functional_001
    inputs = env.get_case_inputs(plan_case_id)
    a = inputs['a']
    b = inputs['b']
    aluc = inputs['aluc']
    outputs = await env.sample_outputs(observed_signals)
    r = outputs['r']
    zero = outputs['zero']
    carry = outputs['carry']
    negative = outputs['negative']
    overflow = outputs['overflow']
    flag = outputs['flag']
    # Verify that the stimulus uses the ADD opcode
    assert_equal('aluc', aluc, 0b100000)
    mask = mask_width(32)
    expected_r = (a + b) & mask
    expected_carry = 1 if (a + b) > mask else 0
    a_s = to_sint(a, 32)
    b_s = to_sint(b, 32)
    sum_s = a_s + b_s
    expected_overflow = 1 if ((a_s >= 0 and b_s >= 0 and sum_s < 0) or (a_s < 0 and b_s < 0 and sum_s >= 0)) else 0
    expected_zero = int(expected_r == 0)
    expected_negative = (expected_r >> 31) & 1
    assert_equal('r', r, expected_r)
    assert_equal('zero', zero, expected_zero)
    assert_equal('carry', carry, expected_carry)
    assert_equal('negative', negative, expected_negative)
    assert_equal('overflow', overflow, expected_overflow)
    assert_true(is_high_impedance(flag), 'flag should be high‑impedance for non‑SLT/SLTU operations')
    env.record_case_note(plan_case_id, f'ADD functional check: a=0x{a:08x}, b=0x{b:08x}, r=0x{r:08x}')
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_002_functional_001 case_id=basic_002 oracle_case_id=functional_basic_002 check_id=basic_002_functional_001

async def _todo_oracle_basic_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001
    inputs = env.get_case_inputs(plan_case_id)
    a = inputs['a']
    b = inputs['b']
    aluc = inputs['aluc']
    outputs = await env.sample_outputs(observed_signals)
    r = outputs['r']
    zero = outputs['zero']
    carry = outputs['carry']
    negative = outputs['negative']
    overflow = outputs['overflow']
    flag = outputs['flag']
    # Verify basic combinational properties
    assert_true(0 <= r < (1 << env.signal_width('r')), 'r should be a 32-bit unsigned value')
    expected_zero = int(r == 0)
    assert_equal('zero', zero, expected_zero)
    expected_negative = (r >> 31) & 1
    assert_equal('negative', negative, expected_negative)
    # carry and overflow must be defined (0 or 1) for defined operations
    assert_true(not is_unknown(carry), 'carry must not be unknown')
    assert_true(not is_unknown(overflow), 'overflow must not be unknown')
    # flag is high-impedance except for SLT/SLTU
    SLT = 0b101010
    SLTU = 0b101011
    if aluc in (SLT, SLTU):
        assert_true(not is_high_impedance(flag), 'flag should be driven for SLT/SLTU')
    else:
        assert_true(is_high_impedance(flag), 'flag should be high-impedance for non-SLT/SLTU')
    env.record_case_note(plan_case_id, f'Property check passed for aluc=0x{aluc:02x}')
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001

async def _todo_oracle_edge_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001
    inputs = env.get_case_inputs(plan_case_id)
    outputs = await env.sample_outputs(observed_signals)
    a = inputs['a']
    b = inputs['b']
    aluc = inputs['aluc']
    r = outputs['r']
    zero = outputs['zero']
    carry = outputs['carry']
    negative = outputs['negative']
    overflow = outputs['overflow']
    flag = outputs['flag']
    # Verify r is a 32‑bit unsigned value
    assert_true(0 <= r < (1 << env.signal_width('r')), 'r should be a 32‑bit unsigned value')
    # zero flag must reflect result being zero
    assert_equal('zero', zero, int(r == 0))
    # negative flag must reflect the sign bit of r
    assert_equal('negative', negative, (r >> 31) & 1)
    # carry and overflow should be defined (not unknown) for any operation
    assert_true(not is_unknown(carry), 'carry must not be unknown')
    assert_true(not is_unknown(overflow), 'overflow must not be unknown')
    # flag is driven only for SLT and SLTU, otherwise high‑impedance
    SLT = 0b101010
    SLTU = 0b101011
    if aluc in (SLT, SLTU):
        assert_true(not is_high_impedance(flag), 'flag should be driven for SLT/SLTU')
    else:
        assert_true(is_high_impedance(flag), 'flag should be high‑impedance for non‑SLT/SLTU')
    env.record_case_note(plan_case_id, f'Edge property checks passed for aluc=0x{aluc:02x}')
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001

async def _todo_oracle_edge_001_property_002(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_property_002`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_property_002 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_002
    inputs = env.get_case_inputs(plan_case_id)
    aluc = inputs['aluc']
    defined_opcodes = {0b100000, 0b100001, 0b100010, 0b100011, 0b100100, 0b100101, 0b100110, 0b100111, 0b101010, 0b101011, 0b000000, 0b000010, 0b000011, 0b000100, 0b000110, 0b000111, 0b001111}
    if aluc not in defined_opcodes:
        outputs = await env.sample_outputs(observed_signals)
        r = outputs['r']
        zero = outputs['zero']
        carry = outputs['carry']
        negative = outputs['negative']
        overflow = outputs['overflow']
        flag = outputs['flag']
        # r must be high‑impedance for undefined opcode
        assert_true(is_high_impedance(r), 'r should be high-impedance for undefined opcode')
        # each flag‑type output must be 0 or high‑impedance
        for name, val in [('zero', zero), ('carry', carry), ('negative', negative), ('overflow', overflow), ('flag', flag)]:
            cond = (val == 0) or is_high_impedance(val)
            assert_true(cond, f'{name} should be 0 or high-impedance for undefined opcode')
        env.record_case_note(plan_case_id, f'Undefined opcode 0x{aluc:02x} produced high‑impedance outputs as expected')
    else:
        # Defined opcode – no special edge checks required here
        pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_property_002 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_002

async def _todo_oracle_basic_002_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_002_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_002_property_001 case_id=basic_002 oracle_case_id=property_basic_002 check_id=basic_002_property_001
    inputs = env.get_case_inputs(plan_case_id)
    a = inputs['a']
    b = inputs['b']
    aluc = inputs['aluc']
    assert_true(aluc == 0b100000, f'Expected ADD opcode (0b100000), got {aluc:#08b}')
    outputs = await env.sample_outputs(observed_signals)
    r = outputs['r']
    zero = outputs['zero']
    carry = outputs['carry']
    negative = outputs['negative']
    overflow = outputs['overflow']
    flag = outputs['flag']
    a_u = to_uint(a, 32)
    b_u = to_uint(b, 32)
    sum_u = a_u + b_u
    mask = mask_width(32)
    expected_r = to_uint(sum_u, 32)
    expected_carry = 1 if sum_u > mask else 0
    expected_zero = 1 if expected_r == 0 else 0
    expected_negative = 1 if (expected_r & 0x80000000) != 0 else 0
    a_s = to_sint(a, 32)
    b_s = to_sint(b, 32)
    sum_s = a_s + b_s
    expected_overflow = 1 if ((a_s >= 0 and b_s >= 0 and sum_s < 0) or (a_s < 0 and b_s < 0 and sum_s >= 0)) else 0
    expected_flag = 0
    assert_equal('r', r, expected_r)
    assert_equal('zero', zero, expected_zero)
    assert_equal('carry', carry, expected_carry)
    assert_equal('negative', negative, expected_negative)
    assert_equal('overflow', overflow, expected_overflow)
    assert_equal('flag', flag, expected_flag)
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_002_property_001 case_id=basic_002 oracle_case_id=property_basic_002 check_id=basic_002_property_001

async def _todo_oracle_negative_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `negative_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_negative_001_property_001 case_id=negative_001 oracle_case_id=property_negative_001 check_id=negative_001_property_001
    inputs = env.get_case_inputs(plan_case_id)
    outputs = await env.sample_outputs(observed_signals)
    r = outputs['r']
    zero = outputs['zero']
    carry = outputs['carry']
    negative = outputs['negative']
    overflow = outputs['overflow']
    flag = outputs['flag']
    # The opcode is illegal, so the ALU should drive high‑impedance on the result
    assert_true(is_high_impedance(r), "Result r should be high‑impedance for undefined opcode")
    # Status flags must not indicate a valid condition; they may be 0, unknown, or high‑impedance
    assert_true(zero == 0 or is_unknown(zero) or is_high_impedance(zero), "zero flag must be 0 or undefined")
    assert_true(carry == 0 or is_unknown(carry) or is_high_impedance(carry), "carry flag must be 0 or undefined")
    assert_true(negative == 0 or is_unknown(negative) or is_high_impedance(negative), "negative flag must be 0 or undefined")
    assert_true(overflow == 0 or is_unknown(overflow) or is_high_impedance(overflow), "overflow flag must be 0 or undefined")
    assert_true(flag == 0 or is_unknown(flag) or is_high_impedance(flag), "flag must be 0 or undefined")
    # TODO(cocoverify2:oracle_check) END block_id=oracle_negative_001_property_001 case_id=negative_001 oracle_case_id=property_negative_001 check_id=negative_001_property_001

async def _todo_oracle_back_to_back_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `back_to_back_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_back_to_back_001_property_001 case_id=back_to_back_001 oracle_case_id=property_back_to_back_001 check_id=back_to_back_001_property_001
    inputs = env.get_case_inputs(plan_case_id)
    outputs = await env.sample_outputs(observed_signals)
    a = inputs['a']
    b = inputs['b']
    aluc = inputs['aluc']
    r = outputs['r']
    zero = outputs['zero']
    carry = outputs['carry']
    negative = outputs['negative']
    overflow = outputs['overflow']
    flag = outputs['flag']
    mask = mask_width(32)
    a_u = to_uint(a, 32)
    b_u = to_uint(b, 32)
    exp_res = None
    exp_carry = 0
    exp_overflow = 0
    if aluc == 0b100000:
        exp_res = (a_u + b_u) & mask
        exp_carry = 1 if a_u + b_u > mask else 0
        a_s = to_sint(a, 32)
        b_s = to_sint(b, 32)
        exp_overflow = 1 if ((a_s > 0 and b_s > 0 and to_sint(exp_res, 32) < 0) or (a_s < 0 and b_s < 0 and to_sint(exp_res, 32) >= 0)) else 0
    elif aluc == 0b100001:
        exp_res = (a_u + b_u) & mask
        exp_carry = 1 if a_u + b_u > mask else 0
        exp_overflow = 0
    elif aluc == 0b100010:
        exp_res = (a_u - b_u) & mask
        exp_carry = 1 if a_u >= b_u else 0
        a_s = to_sint(a, 32)
        b_s = to_sint(b, 32)
        exp_overflow = 1 if ((a_s > 0 and b_s < 0 and to_sint(exp_res, 32) < 0) or (a_s < 0 and b_s > 0 and to_sint(exp_res, 32) >= 0)) else 0
    elif aluc == 0b100011:
        exp_res = (a_u - b_u) & mask
        exp_carry = 1 if a_u >= b_u else 0
        exp_overflow = 0
    elif aluc == 0b100100:
        exp_res = a_u & b_u
    elif aluc == 0b100101:
        exp_res = a_u | b_u
    elif aluc == 0b100110:
        exp_res = a_u ^ b_u
    elif aluc == 0b100111:
        exp_res = (~(a_u | b_u)) & mask
    elif aluc == 0b101010:
        exp_res = 0
    elif aluc == 0b101011:
        exp_res = 0
    elif aluc == 0b000000:
        shamt = a_u & 0x1F
        exp_res = (b_u << shamt) & mask
    elif aluc == 0b000010:
        shamt = a_u & 0x1F
        exp_res = (b_u >> shamt) & mask
    elif aluc == 0b000011:
        shamt = a_u & 0x1F
        b_s = to_sint(b, 32)
        exp_res = (b_s >> shamt) & mask
    elif aluc == 0b000100:
        shamt = a_u & 0x1F
        exp_res = (b_u << shamt) & mask
    elif aluc == 0b000110:
        shamt = a_u & 0x1F
        exp_res = (b_u >> shamt) & mask
    elif aluc == 0b000111:
        shamt = a_u & 0x1F
        b_s = to_sint(b, 32)
        exp_res = (b_s >> shamt) & mask
    elif aluc == 0b001111:
        exp_res = (a_u << 16) & mask
    exp_zero = 1 if exp_res == 0 else 0
    exp_negative = 1 if exp_res is not None and to_sint(exp_res, 32) < 0 else 0
    exp_flag = 1 if aluc in (0b101010, 0b101011) else 0
    assert_equal('r', r, exp_res if exp_res is not None else r)
    assert_equal('zero', zero, exp_zero)
    assert_equal('negative', negative, exp_negative)
    assert_equal('flag', flag, exp_flag)
    assert_equal('carry', carry, exp_carry)
    assert_equal('overflow', overflow, exp_overflow)
    # TODO(cocoverify2:oracle_check) END block_id=oracle_back_to_back_001_property_001 case_id=back_to_back_001 oracle_case_id=property_back_to_back_001 check_id=back_to_back_001_property_001
