"""Oracle helpers for `verified_alu`.

This file is rendered from the structured oracle artifact. It intentionally keeps
checks conservative: timing windows are preserved, unresolved items stay visible,
and control signals are never reintroduced as business outputs.
"""

from __future__ import annotations

import json
import re
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
ORACLE_SPEC = json.loads("{\n  \"functional_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.7475,\n          \"description\": \"Observe that legal input changes are reflected on the observable outputs without state dependence.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Combinational functional oracle stays descriptive and avoids inventing a full truth table.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"carry\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"negative\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"overflow\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"r\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"zero\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked basic stimulus applies legal representative input patterns.\"\n        },\n        {\n          \"check_id\": \"basic_001_functional_002\",\n          \"check_type\": \"functional\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.7675000000000001,\n          \"description\": \"value_level_operation_check\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Verify that for each defined opcode the combinational result matches the arithmetic/logic definition.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"For each stimulus where aluc matches a defined operation, r equals the expected arithmetic result of a and b, zero is 1 iff r==0, negative is 1 iff r[31]==1, overflow and carry follow the semantics of the operation, and flag is 1 only for SLT/SLTU.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [\n            \"operation_specific\",\n            \"ambiguity_preserving\"\n          ],\n          \"signal_policies\": {\n            \"carry\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"negative\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"overflow\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"r\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"zero\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": 1,\n            \"min_cycles\": 0,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the plan case basic_001 drives concrete aluc values covering all defined opcodes.\"\n        }\n      ],\n      \"confidence\": 0.7575000000000001,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.6775,\n          \"description\": \"Observe stable, externally consistent response to boundary-value input patterns.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Boundary oracle is value-oriented but intentionally generic.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"Boundary-value outputs remain externally consistent and do not require hidden state or fixed-latency interpretation.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"carry\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"negative\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"overflow\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"r\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior_downgraded_for_case_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"zero\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"boundary_inputs_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked edge case applies zero-like, one-like, or width-boundary patterns.\"\n        }\n      ],\n      \"confidence\": 0.6775,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"property_oracles\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.7375,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"carry\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"negative\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"overflow\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"r\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"zero\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.7375,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.6875,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"carry\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"negative\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"overflow\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"r\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"zero\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        },\n        {\n          \"check_id\": \"edge_001_property_002\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.7175,\n          \"description\": \"flag_high_impedance_property\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Ensure flag is only driven for SLT and SLTU, otherwise it may be high-impedance.\"\n          ],\n          \"observed_signals\": [\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"If aluc equals SLT (6'b101010) or SLTU (6'b101011) then flag must be 1; for any other aluc, flag must be either 0 or high-impedance, never 1.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [\n            \"operation_specific\",\n            \"ambiguity_preserving\"\n          ],\n          \"signal_policies\": {\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": 1,\n            \"min_cycles\": 0,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When edge_001 stimulates SLT, SLTU and other opcodes.\"\n        }\n      ],\n      \"confidence\": 0.7025,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"protocol_oracles\": []\n}")
ORACLE_CASES_BY_PLAN = json.loads("{\n  \"basic_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.7475,\n          \"description\": \"Observe that legal input changes are reflected on the observable outputs without state dependence.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Combinational functional oracle stays descriptive and avoids inventing a full truth table.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"carry\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"negative\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"overflow\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"r\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"zero\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked basic stimulus applies legal representative input patterns.\"\n        },\n        {\n          \"check_id\": \"basic_001_functional_002\",\n          \"check_type\": \"functional\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.7675000000000001,\n          \"description\": \"value_level_operation_check\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Verify that for each defined opcode the combinational result matches the arithmetic/logic definition.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"For each stimulus where aluc matches a defined operation, r equals the expected arithmetic result of a and b, zero is 1 iff r==0, negative is 1 iff r[31]==1, overflow and carry follow the semantics of the operation, and flag is 1 only for SLT/SLTU.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [\n            \"operation_specific\",\n            \"ambiguity_preserving\"\n          ],\n          \"signal_policies\": {\n            \"carry\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"negative\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"overflow\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"r\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"zero\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": 1,\n            \"min_cycles\": 0,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the plan case basic_001 drives concrete aluc values covering all defined opcodes.\"\n        }\n      ],\n      \"confidence\": 0.7575000000000001,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_basic_001\",\n      \"category\": \"basic\",\n      \"checks\": [\n        {\n          \"check_id\": \"basic_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.7375,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"carry\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"negative\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"overflow\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"r\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"zero\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        }\n      ],\n      \"confidence\": 0.7375,\n      \"linked_plan_case_id\": \"basic_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    }\n  ],\n  \"edge_001\": [\n    {\n      \"assumptions\": [],\n      \"case_id\": \"functional_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_functional_001\",\n          \"check_type\": \"functional\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.6775,\n          \"description\": \"Observe stable, externally consistent response to boundary-value input patterns.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Boundary oracle is value-oriented but intentionally generic.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"Boundary-value outputs remain externally consistent and do not require hidden state or fixed-latency interpretation.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"carry\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"negative\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"overflow\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"r\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior_downgraded_for_case_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"zero\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"conservative\",\n          \"temporal_window\": {\n            \"anchor\": \"boundary_inputs_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When the linked edge case applies zero-like, one-like, or width-boundary patterns.\"\n        }\n      ],\n      \"confidence\": 0.6775,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"oracle_group\": \"functional\",\n      \"source\": \"rule_based\",\n      \"unresolved_items\": []\n    },\n    {\n      \"assumptions\": [],\n      \"case_id\": \"property_edge_001\",\n      \"category\": \"edge\",\n      \"checks\": [\n        {\n          \"check_id\": \"edge_001_property_001\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.6875,\n          \"description\": \"Guardrail: avoid fixed-cycle expectations unless the contract later proves them.\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Default property oracle protects against over-specific later render behavior.\"\n          ],\n          \"observed_signals\": [\n            \"r\",\n            \"zero\",\n            \"carry\",\n            \"negative\",\n            \"overflow\",\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [],\n          \"signal_policies\": {\n            \"carry\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            },\n            \"negative\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"overflow\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"insufficient_structured_evidence\",\n              \"strength\": \"unresolved\"\n            },\n            \"r\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"property_guardrail_preserves_value_ambiguity\",\n              \"strength\": \"unresolved\"\n            },\n            \"zero\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"rule_based\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"input_stable\",\n            \"max_cycles\": null,\n            \"min_cycles\": null,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"Whenever the linked case evaluates externally visible progress.\"\n        },\n        {\n          \"check_id\": \"edge_001_property_002\",\n          \"check_type\": \"property\",\n          \"comparison_operands\": [],\n          \"confidence\": 0.7175,\n          \"description\": \"flag_high_impedance_property\",\n          \"expected_transition\": \"\",\n          \"notes\": [\n            \"Ensure flag is only driven for SLT and SLTU, otherwise it may be high-impedance.\"\n          ],\n          \"observed_signals\": [\n            \"flag\"\n          ],\n          \"oracle_pattern\": \"\",\n          \"pass_condition\": \"If aluc equals SLT (6'b101010) or SLTU (6'b101011) then flag must be 1; for any other aluc, flag must be either 0 or high-impedance, never 1.\",\n          \"reference_domain\": \"\",\n          \"relation_kind\": \"\",\n          \"semantic_tags\": [\n            \"operation_specific\",\n            \"ambiguity_preserving\"\n          ],\n          \"signal_policies\": {\n            \"flag\": {\n              \"allow_high_impedance\": true,\n              \"allow_unknown\": true,\n              \"definedness_mode\": \"not_required\",\n              \"rationale\": \"explicit_conditional_high_impedance_behavior\",\n              \"strength\": \"guarded\"\n            }\n          },\n          \"source\": \"hybrid_llm_generated\",\n          \"strictness\": \"guarded\",\n          \"temporal_window\": {\n            \"anchor\": \"operation_applied\",\n            \"max_cycles\": 1,\n            \"min_cycles\": 0,\n            \"mode\": \"event_based\"\n          },\n          \"trigger_condition\": \"When edge_001 stimulates SLT, SLTU and other opcodes.\"\n        }\n      ],\n      \"confidence\": 0.7025,\n      \"linked_plan_case_id\": \"edge_001\",\n      \"notes\": [],\n      \"oracle_group\": \"property\",\n      \"source\": \"hybrid_llm_enriched\",\n      \"unresolved_items\": []\n    }\n  ]\n}")
TEMPORAL_MODES = ['event_based']
UNRESOLVED_ITEMS = []
_EVENTUAL_LEVEL_RE = re.compile(
    r"\b(?P<signal>[A-Za-z_][A-Za-z0-9_]*)\s+must\s+become\s+(?P<level>high|low)\b",
    re.IGNORECASE,
)
_ASSERTED_RE = re.compile(
    r"\b(?P<signal>[A-Za-z_][A-Za-z0-9_]*)\s+must\s+be\s+asserted\b",
    re.IGNORECASE,
)
_EXACT_COUNT_RE = re.compile(
    r"exactly\s+(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\s+cycles?\s+with\s+(?P<signal>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>[01])",
    re.IGNORECASE,
)
_DEFINED_BINARY_WHEN_RE = re.compile(
    r"Whenever\s+(?P<condition>[A-Za-z_][A-Za-z0-9_]*)\s+is\s+(?P<cond_value>[01]),\s+"
    r"(?P<target>[A-Za-z_][A-Za-z0-9_]*)\s+must\s+be\s+a\s+defined\s+binary\s+value",
    re.IGNORECASE,
)
_COMPLEX_PREMISE_HINTS = (
    "bitstream",
    "consecutive cycles where",
    "msb-to-lsb",
    "lsb-to-msb",
    "order of bits",
    "serial bits",
)
_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
}


def linked_oracle_case_ids_for_plan_case(plan_case_id: str) -> list[str]:
    """Return rendered oracle-case ids linked to a plan case."""
    return [case["case_id"] for case in ORACLE_CASES_BY_PLAN.get(plan_case_id, [])]


def _signal_policy(check: dict[str, Any], signal_name: str) -> dict[str, Any]:
    return dict(check.get("signal_policies", {}).get(signal_name, {}))


def _normalize_observed_signal_name(name: str, observed_signals: list[str]) -> str | None:
    lowered = str(name or "").strip().lower()
    for signal_name in observed_signals:
        if str(signal_name).strip().lower() == lowered:
            return str(signal_name)
    return None


def _is_exact_scalar_signal(env, check: dict[str, Any], signal_name: str) -> bool:
    policy = _signal_policy(check, signal_name)
    if str(policy.get("strength", "unresolved") or "unresolved") != "exact":
        return False
    width = env.signal_width(signal_name)
    return width in (None, 1)


def _sample_matches_bit(value: Any, bit_value: int) -> bool:
    if value is None or is_unknown(value) or is_high_impedance(value):
        return False
    try:
        return to_uint(value, 1) == int(bit_value)
    except AssertionError:
        return False


def _requires_complex_stimulus_history(pass_condition: str) -> bool:
    lowered = str(pass_condition or "").strip().lower()
    return any(token in lowered for token in _COMPLEX_PREMISE_HINTS)


def _parse_count_token(raw_count: str) -> int | None:
    token = str(raw_count or "").strip().lower()
    if not token:
        return None
    if token.isdigit():
        return int(token)
    return _NUMBER_WORDS.get(token)


def _parse_structured_semantic_expectation(pass_condition: str, observed_signals: list[str]) -> dict[str, Any] | None:
    text = str(pass_condition or "").strip()
    if not text:
        return None

    count_match = _EXACT_COUNT_RE.search(text)
    if count_match:
        signal_name = _normalize_observed_signal_name(count_match.group("signal"), observed_signals)
        count_value = _parse_count_token(count_match.group("count"))
        if signal_name and count_value is not None:
            return {
                "kind": "count_equals",
                "signal": signal_name,
                "count": count_value,
                "value": int(count_match.group("value")),
            }

    defined_match = _DEFINED_BINARY_WHEN_RE.search(text)
    if defined_match:
        condition_name = _normalize_observed_signal_name(defined_match.group("condition"), observed_signals)
        target_name = _normalize_observed_signal_name(defined_match.group("target"), observed_signals)
        if condition_name and target_name:
            return {
                "kind": "conditional_defined_binary",
                "condition_signal": condition_name,
                "condition_value": int(defined_match.group("cond_value")),
                "target_signal": target_name,
            }

    eventual_match = _EVENTUAL_LEVEL_RE.search(text)
    if eventual_match:
        signal_name = _normalize_observed_signal_name(eventual_match.group("signal"), observed_signals)
        if signal_name:
            return {
                "kind": "eventual_level",
                "signal": signal_name,
                "value": 1 if eventual_match.group("level").lower() == "high" else 0,
            }

    asserted_match = _ASSERTED_RE.search(text)
    if asserted_match:
        signal_name = _normalize_observed_signal_name(asserted_match.group("signal"), observed_signals)
        if signal_name:
            return {
                "kind": "eventual_level",
                "signal": signal_name,
                "value": 1,
            }

    return None


def _coerce_recorded_int(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return int(value)
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text, 0)
    except ValueError:
        return None


def _case_stimulus_history(env, plan_case_id: str) -> list[dict[str, Any]]:
    getter = getattr(env, "get_case_stimulus_history", None)
    if getter is None:
        return []
    try:
        history = getter(plan_case_id)
    except Exception:
        return []
    return [dict(step) for step in history if isinstance(step, dict)]


def _case_observation_history(env, plan_case_id: str) -> list[dict[str, Any]]:
    getter = getattr(env, "get_case_observation_history", None)
    if getter is None:
        return []
    try:
        history = getter(plan_case_id)
    except Exception:
        return []
    return [dict(item) for item in history if isinstance(item, dict)]


def _oracle_pattern_dict(check: dict[str, Any]) -> dict[str, Any]:
    raw = check.get("oracle_pattern")
    if not raw:
        return {}
    if isinstance(raw, dict):
        return dict(raw)
    try:
        parsed = json.loads(str(raw))
    except Exception:
        return {}
    return dict(parsed) if isinstance(parsed, dict) else {}


def _drive_steps(history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        dict(step.get("signals", {}))
        for step in history
        if step.get("action") == "drive" and isinstance(step.get("signals"), dict)
    ]


def _history_values(
    history: list[dict[str, Any]],
    *,
    signal_name: str,
    gate_signal: str | None = None,
    gate_value: int = 1,
) -> list[int]:
    values: list[int] = []
    for signals in _drive_steps(history):
        if gate_signal is not None:
            gate_seen = _coerce_recorded_int(signals.get(gate_signal))
            if gate_seen != int(gate_value):
                continue
        value = _coerce_recorded_int(signals.get(signal_name))
        if value is not None:
            values.append(value)
    return values


def _sample_uint_if_defined(env, signal_name: str, sample: dict[str, Any]) -> int | None:
    value = sample.get(signal_name)
    if value is None or is_unknown(value) or is_high_impedance(value):
        return None
    return to_uint(value, env.signal_width(signal_name))


def _sample_bit_if_defined(sample: dict[str, Any], signal_name: str) -> int | None:
    value = sample.get(signal_name)
    if value is None or is_unknown(value) or is_high_impedance(value):
        return None
    return 1 if _sample_matches_bit(value, 1) else 0


def _bit_count(value: int) -> int:
    return bin(int(value) & ((1 << max(1, int(value).bit_length())) - 1)).count("1")


def _structured_relation_expectation(check: dict[str, Any], observed_signals: list[str]) -> dict[str, Any] | None:
    relation_kind = str(check.get("relation_kind", "") or "").strip()
    if not relation_kind:
        return None
    operands = [str(item).strip() for item in check.get("comparison_operands", []) if str(item).strip()]
    return {
        "kind": relation_kind,
        "operands": operands,
        "reference_domain": str(check.get("reference_domain", "") or "").strip(),
        "expected_transition": str(check.get("expected_transition", "") or "").strip(),
        "observed_signals": list(observed_signals),
    }


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


async def _apply_structured_relation_check(
    env,
    plan_case_id: str,
    check: dict[str, Any],
    sampled_outputs: dict[str, Any],
) -> dict[str, Any]:
    expectation = _structured_relation_expectation(check, check.get("observed_signals", []))
    if expectation is None:
        return {"status": "semantic_not_applicable", "kind": "", "reason": "no_relation_kind"}

    kind = str(expectation["kind"])
    operands = list(expectation["operands"])
    history = _case_stimulus_history(env, plan_case_id)
    observation_history = _case_observation_history(env, plan_case_id)
    oracle_pattern = _oracle_pattern_dict(check)

    if kind == "grouped_valid_accumulation":
        if len(operands) < 4:
            return {"status": "semantic_not_applicable", "kind": kind, "reason": "missing_operands"}
        data_in_name, valid_in_name, data_out_name, valid_out_name = operands[:4]
        group_size = int(oracle_pattern.get("group_size") or 0)
        expected_groups = int(oracle_pattern.get("expected_groups") or 1)
        allow_gaps = bool(oracle_pattern.get("allow_gaps", False))
        reset_name = str(oracle_pattern.get("reset_signal") or "")
        reset_active_level = int(oracle_pattern.get("reset_active_level") or 0)
        if group_size <= 0:
            return {"status": "semantic_not_applicable", "kind": kind, "reason": "missing_group_size"}

        groups: list[list[int]] = []
        current_group: list[int] = []
        pending_value: int | None = None
        for step in history:
            action = str(step.get("action") or "")
            signals = dict(step.get("signals", {})) if isinstance(step.get("signals"), dict) else {}
            if action == "drive":
                if reset_name and _coerce_recorded_int(signals.get(reset_name)) == reset_active_level:
                    current_group = []
                    pending_value = None
                    continue
                valid_value = _coerce_recorded_int(signals.get(valid_in_name))
                data_value = _coerce_recorded_int(signals.get(data_in_name))
                if valid_value == 1 and data_value is not None:
                    pending_value = data_value
                elif valid_value == 0 and not allow_gaps:
                    pending_value = None
                continue
            if action not in {"wait_cycles", "wait_for_settle"}:
                continue
            if pending_value is not None:
                current_group.append(int(pending_value))
                pending_value = None
                if len(current_group) == group_size:
                    groups.append(list(current_group))
                    current_group = []

        if expected_groups > 0 and len(groups) < expected_groups:
            return {
                "status": "semantic_skipped_no_history",
                "kind": kind,
                "reason": "insufficient_completed_groups",
                "completed_groups": len(groups),
            }

        event_values: list[int] = []
        event_positions: list[int] = []
        observation_cursor = 0
        accepted_so_far = 0
        completed_so_far = 0
        current_group = []
        pending_value = None
        previous_valid_out = 0
        for step in history:
            action = str(step.get("action") or "")
            signals = dict(step.get("signals", {})) if isinstance(step.get("signals"), dict) else {}
            if action == "drive":
                if reset_name and _coerce_recorded_int(signals.get(reset_name)) == reset_active_level:
                    accepted_so_far = 0
                    completed_so_far = 0
                    current_group = []
                    pending_value = None
                    continue
                valid_value = _coerce_recorded_int(signals.get(valid_in_name))
                data_value = _coerce_recorded_int(signals.get(data_in_name))
                if valid_value == 1 and data_value is not None:
                    pending_value = data_value
                elif valid_value == 0 and not allow_gaps:
                    pending_value = None
                continue
            if action not in {"wait_cycles", "wait_for_settle"}:
                continue
            cycles = int(step.get("cycles") or 1) if action == "wait_cycles" else 1
            if pending_value is not None:
                current_group.append(int(pending_value))
                accepted_so_far += 1
                pending_value = None
                if len(current_group) == group_size:
                    completed_so_far += 1
                    current_group = []
            for _ in range(max(1, cycles)):
                if observation_cursor >= len(observation_history):
                    break
                observation = observation_history[observation_cursor]
                observation_cursor += 1
                sample = dict(observation.get("sampled_outputs", {}))
                valid_out = _sample_bit_if_defined(sample, valid_out_name)
                if valid_out != 1:
                    if valid_out is not None:
                        previous_valid_out = valid_out
                    continue
                if previous_valid_out == 1:
                    continue
                assert_true(
                    completed_so_far > len(event_values),
                    f"{valid_out_name} asserted before a completed {group_size}-sample valid group was available",
                )
                observed_value = _sample_uint_if_defined(env, data_out_name, sample)
                assert_true(observed_value is not None, f"{data_out_name} must be defined when {valid_out_name}=1")
                event_values.append(int(observed_value))
                event_positions.append(int(observation.get("step_index", observation_cursor - 1)))
                previous_valid_out = 1

        current_sample = dict(sampled_outputs)
        future_cycles = max(8, group_size * max(1, expected_groups) + 4)
        for cycle_index in range(future_cycles):
            valid_out = _sample_bit_if_defined(current_sample, valid_out_name)
            if valid_out == 1 and previous_valid_out != 1 and len(event_values) < len(groups):
                observed_value = _sample_uint_if_defined(env, data_out_name, current_sample)
                assert_true(observed_value is not None, f"{data_out_name} must be defined when {valid_out_name}=1")
                event_values.append(int(observed_value))
                event_positions.append(len(observation_history) + cycle_index)
            if valid_out is not None:
                previous_valid_out = valid_out
            if cycle_index < future_cycles - 1:
                await env.wait_event_based(label=f"{check['check_id']}_group_relation")
                current_sample = await env.sample_outputs([data_out_name, valid_out_name])

        if expected_groups == 0:
            assert_equal(f"{valid_out_name}_activation_count", len(event_values), 0)
            return {"status": "semantic_checked", "kind": kind, "activation_count": 0}

        assert_equal(f"{valid_out_name}_activation_count", len(event_values), expected_groups)
        expected_values = [
            sum(group) & mask_width(env.signal_width(data_out_name))
            for group in groups[:expected_groups]
        ]
        for index, expected_value in enumerate(expected_values):
            assert_equal(f"{data_out_name}_group_{index}", event_values[index], expected_value)
        return {
            "status": "semantic_checked",
            "kind": kind,
            "expected_values": expected_values,
            "observed_values": event_values,
            "activation_positions": event_positions,
        }

    if kind == "serial_to_parallel_byte":
        if len(operands) < 4:
            return {"status": "semantic_not_applicable", "kind": kind, "reason": "missing_operands"}
        serial_name, valid_name, data_name, valid_out_name = operands[:4]
        bit_count = int(oracle_pattern.get("bit_count") or env.signal_width(data_name) or 8)
        bit_order = str(oracle_pattern.get("bit_order") or expectation.get("reference_domain") or "either")
        bits = _history_values(history, signal_name=serial_name, gate_signal=valid_name, gate_value=1)
        if len(bits) < bit_count:
            return {"status": "semantic_skipped_no_history", "kind": kind, "reason": "fewer_than_required_valid_bits"}
        expected_msb = 0
        for bit in bits[:bit_count]:
            expected_msb = (expected_msb << 1) | (bit & 1)
        expected_lsb = 0
        for index, bit in enumerate(bits[:bit_count]):
            expected_lsb |= (bit & 1) << index
        if bit_order == "msb_to_lsb":
            expected_values = [expected_msb]
        elif bit_order == "lsb_to_msb":
            expected_values = [expected_lsb]
        else:
            expected_values = sorted({expected_msb, expected_lsb})
        activations: list[dict[str, int]] = []
        observation_history = _case_observation_history(env, plan_case_id)
        previous_valid_out = 0
        for observation in observation_history:
            sample = dict(observation.get("sampled_outputs", {}))
            valid_out = _sample_bit_if_defined(sample, valid_out_name)
            if valid_out == 1 and previous_valid_out != 1:
                observed_value = _sample_uint_if_defined(env, data_name, sample)
                assert_true(observed_value is not None, f"{data_name} must be defined when {valid_out_name}=1")
                activations.append({"cycle": int(observation.get("step_index", len(activations))), "value": int(observed_value)})
            if valid_out is not None:
                previous_valid_out = valid_out
        current_sample = dict(sampled_outputs)
        for cycle_index in range(13):
            valid_out = _sample_bit_if_defined(current_sample, valid_out_name)
            if valid_out == 1 and previous_valid_out != 1:
                observed_value = _sample_uint_if_defined(env, data_name, current_sample)
                assert_true(observed_value is not None, f"{data_name} must be defined when {valid_out_name}=1")
                activations.append({"cycle": len(observation_history) + cycle_index, "value": int(observed_value)})
            if valid_out is not None:
                previous_valid_out = valid_out
            if cycle_index < 12:
                await env.wait_event_based(label=f"{check['check_id']}_serial_relation")
                current_sample = await env.sample_outputs([data_name, valid_out_name])
        assert_equal(f"{valid_out_name}_activation_count", len(activations), 1)
        assert_true(
            activations[0]["value"] in expected_values,
            f"{data_name} must match one of the permitted reconstructed serial values {expected_values}",
        )
        return {
            "status": "semantic_checked",
            "kind": kind,
            "expected_values": expected_values,
            "activation_cycle": activations[0]["cycle"],
        }

    if kind == "byte_pack_pair":
        if len(operands) < 4:
            return {"status": "semantic_not_applicable", "kind": kind, "reason": "missing_operands"}
        data_in_name, valid_in_name, data_out_name, valid_out_name = operands[:4]
        element_count = int(oracle_pattern.get("element_count") or 2)
        pack_order = str(oracle_pattern.get("pack_order") or expectation.get("reference_domain") or "either")
        element_width = int(oracle_pattern.get("element_width") or env.signal_width(data_in_name) or 8)
        values = _history_values(history, signal_name=data_in_name, gate_signal=valid_in_name, gate_value=1)
        if len(values) < element_count:
            return {"status": "semantic_skipped_no_history", "kind": kind, "reason": "fewer_than_required_valid_elements"}
        packed_values = [value & mask_width(element_width) for value in values[:element_count]]
        expected_high_to_low = 0
        for value in packed_values:
            expected_high_to_low = (expected_high_to_low << element_width) | value
        expected_low_to_high = 0
        for index, value in enumerate(packed_values):
            expected_low_to_high |= value << (index * element_width)
        if pack_order == "high_to_low":
            expected_values = [expected_high_to_low]
        elif pack_order == "low_to_high":
            expected_values = [expected_low_to_high]
        else:
            expected_values = sorted({expected_high_to_low, expected_low_to_high})
        activations: list[dict[str, int]] = []
        observation_history = _case_observation_history(env, plan_case_id)
        previous_valid_out = 0
        for observation in observation_history:
            sample = dict(observation.get("sampled_outputs", {}))
            valid_out = _sample_bit_if_defined(sample, valid_out_name)
            if valid_out == 1 and previous_valid_out != 1:
                observed_value = _sample_uint_if_defined(env, data_out_name, sample)
                assert_true(observed_value is not None, f"{data_out_name} must be defined when {valid_out_name}=1")
                activations.append({"cycle": int(observation.get("step_index", len(activations))), "value": int(observed_value)})
            if valid_out is not None:
                previous_valid_out = valid_out
        current_sample = dict(sampled_outputs)
        for cycle_index in range(7):
            valid_out = _sample_bit_if_defined(current_sample, valid_out_name)
            if valid_out == 1 and previous_valid_out != 1:
                observed_value = _sample_uint_if_defined(env, data_out_name, current_sample)
                assert_true(observed_value is not None, f"{data_out_name} must be defined when {valid_out_name}=1")
                activations.append({"cycle": len(observation_history) + cycle_index, "value": int(observed_value)})
            if valid_out is not None:
                previous_valid_out = valid_out
            if cycle_index < 6:
                await env.wait_event_based(label=f"{check['check_id']}_pack_relation")
                current_sample = await env.sample_outputs([data_out_name, valid_out_name])
        assert_equal(f"{valid_out_name}_activation_count", len(activations), 1)
        assert_true(
            activations[0]["value"] in expected_values,
            f"{data_out_name} must match one of the permitted packed values {expected_values}",
        )
        return {
            "status": "semantic_checked",
            "kind": kind,
            "expected_values": expected_values,
            "activation_cycle": activations[0]["cycle"],
        }

    if kind == "fifo_write_readback":
        if len(operands) < 5:
            return {"status": "semantic_not_applicable", "kind": kind, "reason": "missing_operands"}
        wdata_name, winc_name, _rinc_name, rdata_name, rempty_name = operands[:5]
        wfull_name = operands[5] if len(operands) > 5 else ""
        writes = _history_values(history, signal_name=wdata_name, gate_signal=winc_name, gate_value=1)
        if not writes:
            return {"status": "semantic_skipped_no_history", "kind": kind, "reason": "no_recorded_write"}
        expected = writes[0]
        current_sample = dict(sampled_outputs)
        saw_nonempty = False
        saw_match = False
        for cycle_index in range(10):
            rempty = _sample_bit_if_defined(current_sample, rempty_name)
            if rempty == 0:
                saw_nonempty = True
            if wfull_name:
                wfull = _sample_bit_if_defined(current_sample, wfull_name)
                if rempty is not None and wfull is not None:
                    assert_true(not (rempty == 1 and wfull == 1), f"{rempty_name} and {wfull_name} must not both assert")
            observed_rdata = _sample_uint_if_defined(env, rdata_name, current_sample)
            if observed_rdata == expected:
                saw_match = True
            if cycle_index < 9:
                await env.wait_event_based(label=f"{check['check_id']}_fifo_relation")
                current_sample = await env.sample_outputs([name for name in [rdata_name, rempty_name, wfull_name] if name])
        assert_true(saw_nonempty, f"{rempty_name} never deasserted after a recorded write/read sequence")
        assert_true(saw_match, f"{rdata_name} never reflected the recorded FIFO write value")
        return {"status": "semantic_checked", "kind": kind, "expected_value": expected}

    if kind == "pipelined_unsigned_product":
        if len(operands) < 3:
            return {"status": "semantic_not_applicable", "kind": kind, "reason": "missing_operands"}
        mul_a_name, mul_b_name, mul_out_name = operands[:3]
        mul_en_out_name = next((name for name in operands[3:] if name.endswith("_out")), "")
        a_values = _history_values(history, signal_name=mul_a_name)
        b_values = _history_values(history, signal_name=mul_b_name)
        if not a_values or not b_values:
            return {"status": "semantic_skipped_no_history", "kind": kind, "reason": "missing_operand_history"}
        expected = (a_values[-1] * b_values[-1]) & mask_width(env.signal_width(mul_out_name))
        current_sample = dict(sampled_outputs)
        matched_cycle = None
        for cycle_index in range(12):
            valid_active = True
            if mul_en_out_name:
                valid_bit = _sample_bit_if_defined(current_sample, mul_en_out_name)
                valid_active = valid_bit == 1
            if valid_active:
                observed_value = _sample_uint_if_defined(env, mul_out_name, current_sample)
                if observed_value is not None and observed_value == expected:
                    matched_cycle = cycle_index
                    break
            if cycle_index < 11:
                await env.wait_event_based(label=f"{check['check_id']}_product_relation")
                current_sample = await env.sample_outputs([name for name in [mul_out_name, mul_en_out_name] if name])
        assert_true(matched_cycle is not None, f"{mul_out_name} did not present the expected unsigned product")
        return {"status": "semantic_checked", "kind": kind, "expected_value": expected, "matched_after_cycles": matched_cycle}

    if kind == "fixed_point_sign_magnitude_add":
        if len(operands) < 3:
            return {"status": "semantic_not_applicable", "kind": kind, "reason": "missing_operands"}
        a_name, b_name, c_name = operands[:3]
        recorded_inputs = env.get_case_inputs(plan_case_id)
        a_value = _coerce_recorded_int(recorded_inputs.get(a_name))
        b_value = _coerce_recorded_int(recorded_inputs.get(b_name))
        if a_value is None or b_value is None:
            a_values = _history_values(history, signal_name=a_name)
            b_values = _history_values(history, signal_name=b_name)
            a_value = a_value if a_value is not None else (a_values[-1] if a_values else None)
            b_value = b_value if b_value is not None else (b_values[-1] if b_values else None)
        if a_value is None or b_value is None:
            return {"status": "semantic_skipped_no_history", "kind": kind, "reason": "missing_operand_history"}
        width = max(2, int(env.signal_width(c_name) or 16))
        magnitude_mask = (1 << (width - 1)) - 1
        sign_a = (a_value >> (width - 1)) & 1
        sign_b = (b_value >> (width - 1)) & 1
        mag_a = a_value & magnitude_mask
        mag_b = b_value & magnitude_mask
        if sign_a == sign_b:
            mag_sum = mag_a + mag_b
            if mag_sum > magnitude_mask:
                return {"status": "semantic_skipped_ambiguous", "kind": kind, "reason": "overflow_not_constrained"}
            expected = (sign_a << (width - 1)) | mag_sum
        elif mag_a > mag_b:
            expected = mag_a - mag_b
        elif mag_b > mag_a:
            expected = (sign_b << (width - 1)) | (mag_b - mag_a)
        else:
            expected = 0
        observed_value = _sample_uint_if_defined(env, c_name, sampled_outputs)
        assert_true(observed_value is not None, f"{c_name} must be defined for fixed-point semantic checking")
        assert_equal(c_name, observed_value, expected)
        return {"status": "semantic_checked", "kind": kind, "expected_value": expected}

    if kind == "unsigned_divide_16_by_8":
        if len(operands) < 4:
            return {"status": "semantic_not_applicable", "kind": kind, "reason": "missing_operands"}
        dividend_name, divisor_name, result_name, odd_name = operands[:4]
        recorded_inputs = env.get_case_inputs(plan_case_id)
        dividend = _coerce_recorded_int(recorded_inputs.get(dividend_name))
        divisor = _coerce_recorded_int(recorded_inputs.get(divisor_name))
        if dividend is None or divisor is None:
            dividend_values = _history_values(history, signal_name=dividend_name)
            divisor_values = _history_values(history, signal_name=divisor_name)
            dividend = dividend if dividend is not None else (dividend_values[-1] if dividend_values else None)
            divisor = divisor if divisor is not None else (divisor_values[-1] if divisor_values else None)
        if dividend is None or divisor is None:
            return {"status": "semantic_skipped_no_history", "kind": kind, "reason": "missing_operand_history"}
        if divisor == 0:
            return {"status": "semantic_skipped_ambiguous", "kind": kind, "reason": "divisor_zero"}
        expected_q = (dividend // divisor) & mask_width(env.signal_width(result_name))
        expected_r = (dividend % divisor) & mask_width(env.signal_width(odd_name))
        observed_q = _sample_uint_if_defined(env, result_name, sampled_outputs)
        observed_r = _sample_uint_if_defined(env, odd_name, sampled_outputs)
        assert_true(observed_q is not None and observed_r is not None, f"{result_name}/{odd_name} must be defined for divide semantic checking")
        assert_equal(result_name, observed_q, expected_q)
        assert_equal(odd_name, observed_r, expected_r)
        return {"status": "semantic_checked", "kind": kind, "expected_quotient": expected_q, "expected_remainder": expected_r}

    if kind == "sequence_pattern_detect":
        if len(operands) < 2:
            return {"status": "semantic_not_applicable", "kind": kind, "reason": "missing_operands"}
        data_name, output_name = operands[:2]
        pattern_text = str(expectation.get("expected_transition", "")).strip()
        pattern = [int(ch) for ch in pattern_text if ch in {"0", "1"}]
        observed_bits = _history_values(history, signal_name=data_name)
        if len(pattern) == 0 or len(observed_bits) < len(pattern):
            return {"status": "semantic_skipped_no_history", "kind": kind, "reason": "insufficient_pattern_history"}
        saw_pattern = any(observed_bits[index : index + len(pattern)] == pattern for index in range(len(observed_bits) - len(pattern) + 1))
        if not saw_pattern:
            return {"status": "semantic_skipped_no_history", "kind": kind, "reason": "pattern_not_driven"}
        current_sample = dict(sampled_outputs)
        for cycle_index in range(5):
            if _sample_bit_if_defined(current_sample, output_name) == 1:
                return {"status": "semantic_checked", "kind": kind, "matched_after_cycles": cycle_index}
            if cycle_index < 4:
                await env.wait_event_based(label=f"{check['check_id']}_pattern_relation")
                current_sample = await env.sample_outputs([output_name])
        assert_true(False, f"{output_name} did not assert after the documented input pattern {pattern_text}")

    if kind == "one_hot_rotation_progression":
        if len(operands) < 1:
            return {"status": "semantic_not_applicable", "kind": kind, "reason": "missing_operands"}
        output_name = operands[0]
        sample_count = int(oracle_pattern.get("sample_count") or 6)
        samples: list[int] = []
        current_sample = dict(sampled_outputs)
        for cycle_index in range(sample_count):
            observed_value = _sample_uint_if_defined(env, output_name, current_sample)
            if observed_value is not None:
                samples.append(int(observed_value))
            if cycle_index < sample_count - 1:
                await env.wait_event_based(label=f"{check['check_id']}_ring_progression")
                current_sample = await env.sample_outputs([output_name])
        nonzero_samples = [value for value in samples if value != 0]
        assert_true(nonzero_samples, f"{output_name} never produced a non-zero ring state")
        assert_true(all(_bit_count(value) == 1 for value in nonzero_samples), f"{output_name} must remain one-hot in observed ring states")
        assert_true(len(set(nonzero_samples)) > 1, f"{output_name} never advanced to a later ring state")
        width = max(1, int(env.signal_width(output_name) or 8))
        for previous, current in zip(nonzero_samples, nonzero_samples[1:]):
            rotated_left = ((previous << 1) | (previous >> (width - 1))) & mask_width(width)
            rotated_right = ((previous >> 1) | ((previous & 1) << (width - 1))) & mask_width(width)
            assert_true(
                current in {rotated_left, rotated_right},
                f"{output_name} must rotate by one bit between observed ring states",
            )
        return {"status": "semantic_checked", "kind": kind, "observed_states": nonzero_samples}

    if kind == "traffic_light_phase_progression":
        if len(operands) < 4:
            return {"status": "semantic_not_applicable", "kind": kind, "reason": "missing_operands"}
        _request_name, red_name, yellow_name, green_name = operands[:4]
        sample_count = int(oracle_pattern.get("sample_count") or 20)
        current_sample = dict(sampled_outputs)
        phases: list[str] = []
        for cycle_index in range(sample_count):
            red = _sample_bit_if_defined(current_sample, red_name)
            yellow = _sample_bit_if_defined(current_sample, yellow_name)
            green = _sample_bit_if_defined(current_sample, green_name)
            active = [name for name, value in ((red_name, red), (yellow_name, yellow), (green_name, green)) if value == 1]
            assert_true(len(active) <= 1, "traffic-light outputs must be mutually exclusive")
            if active:
                phases.append(active[0])
            if cycle_index < sample_count - 1:
                await env.wait_event_based(label=f"{check['check_id']}_traffic_progression")
                current_sample = await env.sample_outputs([red_name, yellow_name, green_name])
        assert_true(green_name in phases, f"{green_name} never became active")
        assert_true(yellow_name in phases, f"{yellow_name} never became active")
        yellow_index = phases.index(yellow_name)
        assert_true(red_name in phases[yellow_index + 1 :], f"{red_name} never followed {yellow_name} in the observed phase progression")
        return {"status": "semantic_checked", "kind": kind, "phase_trace": phases}

    return {"status": "semantic_not_applicable", "kind": kind, "reason": "unsupported_relation_kind"}


async def _apply_structured_semantic_check(
    env,
    plan_case_id: str,
    check: dict[str, Any],
    observed_signals: list[str],
    sampled_outputs: dict[str, Any],
) -> dict[str, Any]:
    """Apply a tiny set of high-confidence pass_condition semantics when the artifact supports it."""
    relation_expectation = _structured_relation_expectation(check, observed_signals)
    if relation_expectation is not None:
        return await _apply_structured_relation_check(env, plan_case_id, check, sampled_outputs)

    if check.get("source") != "hybrid_llm_generated" and "operation_specific" not in set(check.get("semantic_tags", [])):
        return {"status": "semantic_not_applicable", "kind": "", "reason": "non_llm_or_non_specific_check"}

    if not env.get_case_inputs(plan_case_id):
        return {"status": "semantic_skipped_no_inputs", "kind": "", "reason": "no_recorded_inputs"}

    expectation = _parse_structured_semantic_expectation(check.get("pass_condition", ""), observed_signals)
    if expectation is None:
        return {"status": "semantic_not_applicable", "kind": "", "reason": "no_supported_pattern"}

    if expectation["kind"] == "eventual_level":
        if _requires_complex_stimulus_history(check.get("pass_condition", "")):
            return {"status": "semantic_skipped_complex_premise", "kind": expectation["kind"], "reason": "complex_stimulus_history"}
        signal_name = str(expectation["signal"])
        if not _is_exact_scalar_signal(env, check, signal_name):
            return {"status": "semantic_skipped_policy", "kind": expectation["kind"], "reason": "signal_not_exact_scalar"}
        target_value = int(expectation["value"])
        if _sample_matches_bit(sampled_outputs.get(signal_name), target_value):
            return {"status": "semantic_checked", "kind": expectation["kind"], "matched_after_cycles": 0}
        for cycle_index in range(1, 9):
            await env.wait_event_based(label=f"{check['check_id']}_semantic_eventual")
            future_sample = await env.sample_outputs([signal_name])
            if _sample_matches_bit(future_sample.get(signal_name), target_value):
                return {"status": "semantic_checked", "kind": expectation["kind"], "matched_after_cycles": cycle_index}
        human_value = "high" if target_value else "low"
        assert_true(False, f"{signal_name} did not become {human_value} within the conservative semantic observation window")

    if expectation["kind"] == "count_equals":
        signal_name = str(expectation["signal"])
        if not _is_exact_scalar_signal(env, check, signal_name):
            return {"status": "semantic_skipped_policy", "kind": expectation["kind"], "reason": "signal_not_exact_scalar"}
        expected_count = int(expectation["count"])
        expected_value = int(expectation["value"])
        observation_cycles = max(8, expected_count * 2)
        matched_count = 1 if _sample_matches_bit(sampled_outputs.get(signal_name), expected_value) else 0
        for _ in range(observation_cycles):
            await env.wait_event_based(label=f"{check['check_id']}_semantic_count")
            future_sample = await env.sample_outputs([signal_name])
            if _sample_matches_bit(future_sample.get(signal_name), expected_value):
                matched_count += 1
        assert_equal(f"{signal_name}_match_count", matched_count, expected_count)
        return {"status": "semantic_checked", "kind": expectation["kind"], "matched_count": matched_count}

    if expectation["kind"] == "conditional_defined_binary":
        condition_signal = str(expectation["condition_signal"])
        target_signal = str(expectation["target_signal"])
        if not _is_exact_scalar_signal(env, check, condition_signal):
            return {"status": "semantic_skipped_policy", "kind": expectation["kind"], "reason": "condition_not_exact_scalar"}
        if not _is_exact_scalar_signal(env, check, target_signal):
            return {"status": "semantic_skipped_policy", "kind": expectation["kind"], "reason": "target_not_exact_scalar"}
        target_width = env.signal_width(target_signal)
        if target_width not in (None, 1):
            return {"status": "semantic_skipped_policy", "kind": expectation["kind"], "reason": "target_not_binary_scalar"}
        condition_value = int(expectation["condition_value"])
        activated = 0
        current_sample = dict(sampled_outputs)
        for _ in range(9):
            if _sample_matches_bit(current_sample.get(condition_signal), condition_value):
                activated += 1
                target_value = current_sample.get(target_signal)
                assert_true(target_value is not None, f"{target_signal} must be observable when {condition_signal}={condition_value}")
                assert_true(not is_unknown(target_value), f"{target_signal} must not be unknown when {condition_signal}={condition_value}")
                assert_true(
                    not is_high_impedance(target_value),
                    f"{target_signal} must not be high-impedance when {condition_signal}={condition_value}",
                )
                assert_true(
                    to_uint(target_value, 1) in (0, 1),
                    f"{target_signal} must be a defined binary value when {condition_signal}={condition_value}",
                )
            await env.wait_event_based(label=f"{check['check_id']}_semantic_conditional")
            current_sample = await env.sample_outputs([condition_signal, target_signal])
        return {
            "status": "semantic_checked" if activated else "semantic_observed_only",
            "kind": expectation["kind"],
            "activation_count": activated,
        }

    return {"status": "semantic_not_applicable", "kind": "", "reason": "unsupported_kind"}


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
    semantic_result = await _apply_structured_semantic_check(
        env,
        plan_case_id,
        check,
        observed_signals,
        dict(policy_result.get("sampled_outputs", {})),
    )
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
        "semantic_status": semantic_result.get("status", ""),
        "semantic_kind": semantic_result.get("kind", ""),
        "semantic_details": {
            key: value
            for key, value in semantic_result.items()
            if key not in {"status", "kind"}
        },
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


async def _todo_oracle_basic_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001
    # Observed signals: r, zero, carry, negative, overflow, flag
    # Pass condition: Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001

async def _todo_oracle_basic_001_functional_002(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_functional_002`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_002 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_002
    # Observed signals: r, zero, carry, negative, overflow, flag
    # Pass condition: For each stimulus where aluc matches a defined operation, r equals the expected arithmetic result of a and b, zero is 1 iff r==0, negative is 1 iff r[31]==1, overflow and carry follow the semantics of the operation, and flag is 1 only for SLT/SLTU.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_functional_002 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_002

async def _todo_oracle_edge_001_functional_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_functional_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_functional_001 case_id=edge_001 oracle_case_id=functional_edge_001 check_id=edge_001_functional_001
    # Observed signals: r, zero, carry, negative, overflow, flag
    # Pass condition: Boundary-value outputs remain externally consistent and do not require hidden state or fixed-latency interpretation.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_functional_001 case_id=edge_001 oracle_case_id=functional_edge_001 check_id=edge_001_functional_001

async def _todo_oracle_basic_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `basic_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001
    # Observed signals: r, zero, carry, negative, overflow, flag
    # Pass condition: The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_basic_001_property_001 case_id=basic_001 oracle_case_id=property_basic_001 check_id=basic_001_property_001

async def _todo_oracle_edge_001_property_001(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_property_001`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001
    # Observed signals: r, zero, carry, negative, overflow, flag
    # Pass condition: The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_property_001 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_001

async def _todo_oracle_edge_001_property_002(env, plan_case_id: str, oracle_case_id: str, check: dict[str, Any], observed_signals: list[str]) -> None:
    """LLM-fill oracle hook for check `edge_001_property_002`."""
    # TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_edge_001_property_002 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_002
    # Observed signals: flag
    # Pass condition: If aluc equals SLT (6'b101010) or SLTU (6'b101011) then flag must be 1; for any other aluc, flag must be either 0 or high-impedance, never 1.
    # Guidance: Read DUT outputs and add concrete assertions here.
    pass
    # TODO(cocoverify2:oracle_check) END block_id=oracle_edge_001_property_002 case_id=edge_001 oracle_case_id=property_edge_001 check_id=edge_001_property_002
