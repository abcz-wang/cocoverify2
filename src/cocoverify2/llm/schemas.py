"""Structured LLM response schemas for Phase 2/3 hybrid generation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from cocoverify2.core.types import OracleCheckType, OracleStrictness, TemporalWindowMode, TestCategory


class LLMModelBase(BaseModel):
    """Base model for strict LLM response validation."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class PlanCaseEnrichment(LLMModelBase):
    """Optional enrichment for one baseline plan case."""

    case_id: str
    goal: str | None = None
    stimulus_intent: list[str] = Field(default_factory=list)
    timing_assumptions: list[str] = Field(default_factory=list)
    observed_signals: list[str] = Field(default_factory=list)
    stimulus_signals: list[str] = Field(default_factory=list)
    expected_properties: list[str] = Field(default_factory=list)
    coverage_tags: list[str] = Field(default_factory=list)
    semantic_tags: list[str] = Field(default_factory=list)
    scenario_kind: str = ""
    stimulus_program: list[dict[str, object]] = Field(default_factory=list)
    settle_requirement: str = ""
    comparison_operands: list[str] = Field(default_factory=list)
    relation_kind: str = ""
    expected_transition: str = ""
    reference_domain: str = ""
    notes: list[str] = Field(default_factory=list)
    priority: int | None = Field(default=None, ge=1, le=10)


class AdditionalPlanCase(LLMModelBase):
    """Candidate additional test-plan case proposed by the LLM."""

    draft_id: str = Field(min_length=1)
    category: TestCategory
    goal: str = Field(min_length=1)
    preconditions: list[str] = Field(default_factory=list)
    stimulus_intent: list[str] = Field(default_factory=list)
    stimulus_signals: list[str] = Field(default_factory=list)
    expected_properties: list[str] = Field(default_factory=list)
    observed_signals: list[str] = Field(default_factory=list)
    timing_assumptions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    coverage_tags: list[str] = Field(default_factory=list)
    semantic_tags: list[str] = Field(default_factory=list)
    scenario_kind: str = ""
    stimulus_program: list[dict[str, object]] = Field(default_factory=list)
    settle_requirement: str = ""
    comparison_operands: list[str] = Field(default_factory=list)
    relation_kind: str = ""
    expected_transition: str = ""
    reference_domain: str = ""
    notes: list[str] = Field(default_factory=list)
    priority: int = Field(default=5, ge=1, le=10)


class PlanAugmentation(LLMModelBase):
    """Top-level Phase 2 LLM augmentation payload."""

    baseline_case_enrichments: list[PlanCaseEnrichment] = Field(default_factory=list)
    additional_cases: list[AdditionalPlanCase] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    planning_notes: list[str] = Field(default_factory=list)


class LLMTemporalWindow(LLMModelBase):
    """LLM-proposed temporal window metadata."""

    mode: TemporalWindowMode = TemporalWindowMode.EVENT_BASED
    min_cycles: int | None = Field(default=None, ge=0)
    max_cycles: int | None = Field(default=None, ge=0)
    anchor: str = ""


class LLMOracleCheck(LLMModelBase):
    """LLM-proposed oracle check before merge-time normalization."""

    check_type: OracleCheckType = OracleCheckType.PROPERTY
    description: str = Field(min_length=1)
    observed_signals: list[str] = Field(default_factory=list)
    trigger_condition: str = ""
    pass_condition: str = ""
    temporal_window: LLMTemporalWindow = Field(default_factory=LLMTemporalWindow)
    strictness: OracleStrictness = OracleStrictness.CONSERVATIVE
    semantic_tags: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class OracleCaseEnrichment(LLMModelBase):
    """Append-only enrichment for one existing oracle case bucket."""

    linked_plan_case_id: str
    oracle_class: str = Field(min_length=1)
    checks: list[LLMOracleCheck] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class AdditionalOracleCase(LLMModelBase):
    """New oracle-case bucket proposed by the LLM."""

    linked_plan_case_id: str
    oracle_class: str = Field(min_length=1)
    checks: list[LLMOracleCheck] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class OracleAugmentation(LLMModelBase):
    """Top-level Phase 3 LLM augmentation payload."""

    case_enrichments: list[OracleCaseEnrichment] = Field(default_factory=list)
    additional_oracle_cases: list[AdditionalOracleCase] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    oracle_notes: list[str] = Field(default_factory=list)


class TodoFillResponse(LLMModelBase):
    """Block-level LLM response for filling a rendered TODO block."""

    block_id: str = Field(min_length=1)
    code_lines: list[str] = Field(default_factory=list)
    helper_calls: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
