"""Core pydantic models used across the cocoverify2 pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cocoverify2.core.types import (
    AssertionStrength,
    DefinednessMode,
    ExecutionStatus,
    LatencyModel,
    OracleCheckType,
    OracleStrictness,
    PortDirection,
    SequentialKind,
    SimulationMode,
    TemporalWindowMode,
    TestCategory,
    VerdictKind,
)


class ModelBase(BaseModel):
    """Base model with strict validation and stable serialization defaults."""

    model_config = ConfigDict(extra="forbid", use_enum_values=True)


class PortSpec(ModelBase):
    """Normalized DUT port metadata.

    The ``width`` field is either an integer bit-width, a raw range expression such
    as ``"WIDTH-1:0"``, or ``None`` when the width could not be inferred.
    """

    name: str
    direction: PortDirection = PortDirection.UNKNOWN
    width: int | str | None = 1
    raw_range: str | None = None
    signed: bool = False
    data_type: str | None = None
    source: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ClockSpec(ModelBase):
    """Candidate clock metadata."""

    name: str
    period_ns_guess: float | None = Field(default=None, gt=0.0)
    source: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class ResetSpec(ModelBase):
    """Candidate reset metadata."""

    name: str
    active_level: int | None = Field(default=None)
    synchronous: bool | None = None
    stabilization_cycles: int | None = Field(default=None, ge=0)
    source: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class TimingSpec(ModelBase):
    """High-level timing assumptions for the DUT."""

    sequential_kind: SequentialKind = SequentialKind.UNKNOWN
    latency_model: LatencyModel = LatencyModel.UNKNOWN
    fixed_latency_cycles: int | None = Field(default=None, ge=0)
    variable_latency_range: tuple[int, int] | None = None
    sampling_window_cycles: int | None = Field(default=None, ge=0)
    source: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class HandshakeGroup(ModelBase):
    """Structured handshake relationship inferred from the interface."""

    pattern: str
    group_name: str = "default"
    signals: dict[str, str] = Field(default_factory=dict)
    source: str = "unknown"
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class DUTContract(ModelBase):
    """Structured contract extracted for the DUT under verification."""

    module_name: str = ""
    rtl_sources: list[Path] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    ports: list[PortSpec] = Field(default_factory=list)
    clocks: list[ClockSpec] = Field(default_factory=list)
    resets: list[ResetSpec] = Field(default_factory=list)
    handshake_groups: list[HandshakeGroup] = Field(default_factory=list)
    handshake_signals: list[str] = Field(default_factory=list)
    timing: TimingSpec = Field(default_factory=TimingSpec)
    observable_outputs: list[str] = Field(default_factory=list)
    illegal_input_constraints: list[str] = Field(default_factory=list)
    allowed_unknowns: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)
    source_map: dict[str, list[str]] = Field(default_factory=dict)
    extraction_warnings: list[str] = Field(default_factory=list)
    contract_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class TestCasePlan(ModelBase):
    """Single planned verification case."""

    case_id: str
    goal: str
    category: TestCategory = TestCategory.BASIC
    preconditions: list[str] = Field(default_factory=list)
    stimulus_intent: list[str] = Field(default_factory=list)
    stimulus_signals: list[str] = Field(default_factory=list)
    expected_properties: list[str] = Field(default_factory=list)
    observed_signals: list[str] = Field(default_factory=list)
    timing_assumptions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    coverage_tags: list[str] = Field(default_factory=list)
    semantic_tags: list[str] = Field(default_factory=list)
    execution_policy: str = "deterministic"
    defer_reason: str = ""
    priority: int = Field(default=5, ge=1, le=10)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = "unknown"
    notes: list[str] = Field(default_factory=list)


class TestPlan(ModelBase):
    """Structured verification plan created before rendering code."""

    module_name: str = ""
    based_on_contract: str = ""
    plan_strategy: str = ""
    cases: list[TestCasePlan] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    plan_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class TemporalWindow(ModelBase):
    """Explicit temporal window metadata for an oracle check."""

    mode: TemporalWindowMode = TemporalWindowMode.EVENT_BASED
    min_cycles: int | None = Field(default=None, ge=0)
    max_cycles: int | None = Field(default=None, ge=0)
    anchor: str = ""


class SignalAssertionPolicy(ModelBase):
    """Structured observability policy for one signal inside an oracle check."""

    strength: AssertionStrength = AssertionStrength.UNRESOLVED
    definedness_mode: DefinednessMode = DefinednessMode.NOT_REQUIRED
    allow_unknown: bool = True
    allow_high_impedance: bool = True
    rationale: str = ""


class OracleCheck(ModelBase):
    """Single structured oracle check ready for later render-stage translation."""

    check_id: str
    check_type: OracleCheckType = OracleCheckType.PROPERTY
    description: str
    observed_signals: list[str] = Field(default_factory=list)
    trigger_condition: str = ""
    pass_condition: str = ""
    temporal_window: TemporalWindow = Field(default_factory=TemporalWindow)
    strictness: OracleStrictness = OracleStrictness.CONSERVATIVE
    signal_policies: dict[str, SignalAssertionPolicy] = Field(default_factory=dict)
    semantic_tags: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = "unknown"
    notes: list[str] = Field(default_factory=list)


class OracleCase(ModelBase):
    """Structured oracle bundle linked to a single test-plan case."""

    case_id: str
    linked_plan_case_id: str
    category: TestCategory = TestCategory.BASIC
    checks: list[OracleCheck] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source: str = "unknown"
    notes: list[str] = Field(default_factory=list)


class OracleConfidenceSummary(ModelBase):
    """Confidence breakdown across oracle categories."""

    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    protocol_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    functional_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    property_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class OracleSpec(ModelBase):
    """Structured oracle artifact produced independently from the test plan."""

    module_name: str = ""
    based_on_contract: str = ""
    based_on_plan: str = ""
    oracle_strategy: str = ""
    protocol_oracles: list[OracleCase] = Field(default_factory=list)
    functional_oracles: list[OracleCase] = Field(default_factory=list)
    property_oracles: list[OracleCase] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    oracle_confidence: OracleConfidenceSummary = Field(default_factory=OracleConfidenceSummary)


class LLMTodoBlock(ModelBase):
    """Structured metadata for one LLM-fillable TODO block in rendered code."""

    block_id: str
    fill_kind: str
    relative_path: str = ""
    file_role: str = ""
    template_name: str = ""
    case_id: str = ""
    oracle_case_id: str = ""
    check_id: str = ""
    start_marker: str = ""
    end_marker: str = ""
    instructions: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    fill_status: str = "pending"
    fill_attempts: int = Field(default=0, ge=0)
    fill_errors: list[str] = Field(default_factory=list)


class RenderedFile(ModelBase):
    """Single generated render artifact and its role in the package."""

    relative_path: str
    role: str
    description: str
    template_name: str = ""
    todo_block_ids: list[str] = Field(default_factory=list)


class RenderMetadata(ModelBase):
    """Structured metadata emitted by the render stage."""

    module_name: str = ""
    artifact_stage: str = "render"
    based_on_contract: str = ""
    based_on_plan: str = ""
    based_on_oracle: str = ""
    based_on_render_metadata: str = ""
    generated_files: list[RenderedFile] = Field(default_factory=list)
    test_modules: list[str] = Field(default_factory=list)
    interface_summary: dict[str, Any] = Field(default_factory=dict)
    env_summary: dict[str, Any] = Field(default_factory=dict)
    oracle_summary: dict[str, Any] = Field(default_factory=dict)
    coverage_summary: dict[str, Any] = Field(default_factory=dict)
    template_inventory: list[str] = Field(default_factory=list)
    llm_todo_blocks: list[LLMTodoBlock] = Field(default_factory=list)
    filled_todo_block_ids: list[str] = Field(default_factory=list)
    unfilled_todo_block_ids: list[str] = Field(default_factory=list)
    fill_status: str = ""
    fill_warnings: list[str] = Field(default_factory=list)
    render_warnings: list[str] = Field(default_factory=list)
    render_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class FillBlockResult(ModelBase):
    """Structured fill outcome for one TODO block."""

    block_id: str
    fill_kind: str
    relative_path: str = ""
    status: str = "pending"
    attempts: int = Field(default=0, ge=0)
    request_path: str = ""
    response_raw_path: str = ""
    response_parsed_path: str = ""
    helper_calls: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    unresolved_items: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    compile_errors: list[str] = Field(default_factory=list)


class FillReport(ModelBase):
    """Structured report for the TODO fill stage."""

    module_name: str = ""
    based_on_render_metadata: str = ""
    based_on_contract: str = ""
    based_on_plan: str = ""
    based_on_oracle: str = ""
    fill_status: str = "failed"
    attempted_block_ids: list[str] = Field(default_factory=list)
    filled_block_ids: list[str] = Field(default_factory=list)
    repaired_block_ids: list[str] = Field(default_factory=list)
    failed_block_ids: list[str] = Field(default_factory=list)
    compile_ok: bool = False
    warnings: list[str] = Field(default_factory=list)
    block_results: list[FillBlockResult] = Field(default_factory=list)
    package_dir: str = ""
    metadata_path: str = ""


class RunnerSelection(ModelBase):
    """Structured record of execution-mode selection and fallback behavior."""

    requested_mode: SimulationMode = SimulationMode.AUTO
    selected_mode: SimulationMode = SimulationMode.AUTO
    backend: str = ""
    render_metadata_path: str = ""
    package_dir: str = ""
    makefile_path: str | None = None
    filelist_path: str | None = None
    resolved_rtl_sources: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    fallbacks: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SimulationConfig(ModelBase):
    """Execution configuration for simulator invocation."""

    simulator: str = "icarus"
    mode: SimulationMode = SimulationMode.AUTO
    rtl_sources: list[Path] = Field(default_factory=list)
    filelist_path: Path | None = None
    include_dirs: list[Path] = Field(default_factory=list)
    top_module: str = ""
    test_module: str = ""
    extra_env: dict[str, str] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
    timescale: str | None = None
    waves_enabled: bool = False
    junit_enabled: bool = True
    timeout_seconds: int = Field(default=60, ge=1)
    working_dir: Path | None = None
    clean_build: bool = False
    plusargs: list[str] = Field(default_factory=list)
    make_targets: list[str] = Field(default_factory=list)

    # Phase 0-4 compatibility aliases / legacy fields kept optional for now.
    defines: dict[str, str] = Field(default_factory=dict)
    toplevel: str = ""
    test_dir: Path = Path("generated_tb")
    waves: bool = False


class SimulationResult(ModelBase):
    """Structured result from the simulation execution layer."""

    module_name: str = ""
    based_on_render_metadata: str = ""
    selected_mode: SimulationMode = SimulationMode.AUTO
    selected_simulator: str = ""
    command: list[str] = Field(default_factory=list)
    return_code: int | None = None
    status: ExecutionStatus = ExecutionStatus.UNKNOWN_FAILURE
    start_time: str = ""
    end_time: str = ""
    duration_seconds: float = 0.0
    discovered_tests: list[str] = Field(default_factory=list)
    executed_tests: list[str] = Field(default_factory=list)
    passed_tests: list[str] = Field(default_factory=list)
    failed_tests: list[str] = Field(default_factory=list)
    skipped_tests: list[str] = Field(default_factory=list)
    log_paths: dict[str, str] = Field(default_factory=dict)
    junit_path: str | None = None
    waveform_paths: list[str] = Field(default_factory=list)
    runner_warnings: list[str] = Field(default_factory=list)
    execution_notes: list[str] = Field(default_factory=list)


class TriageResult(ModelBase):
    """Structured triage outcome after simulation analysis."""

    module_name: str = ""
    based_on_simulation_result: str = ""
    based_on_runner_selection: str | None = None
    based_on_render_metadata: str | None = None
    source_status: str = ""
    primary_category: str = "unclassified"
    secondary_categories: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    matched_signals: list[str] = Field(default_factory=list)
    matched_log_fragments: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    suspected_layer: str = "unknown"


class RepairAction(ModelBase):
    """Targeted repair recommendation."""

    target_stage: str = ""
    reason: str = ""
    inputs_to_refresh: list[str] = Field(default_factory=list)
    artifacts_to_keep: list[str] = Field(default_factory=list)
    artifacts_to_regenerate: list[str] = Field(default_factory=list)


class FinalVerdict(ModelBase):
    """Final structured verification verdict."""

    verdict: VerdictKind = VerdictKind.INCONCLUSIVE
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    false_positive_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    false_negative_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    rationale: list[str] = Field(default_factory=list)


class VerificationReport(ModelBase):
    """Top-level report artifact emitted by the framework."""

    contract: DUTContract | None = None
    test_plan_summary: TestPlan | None = None
    oracle_summary: OracleSpec | None = None
    simulation_summary: SimulationResult | None = None
    triage: TriageResult | None = None
    repair_actions: list[RepairAction] = Field(default_factory=list)
    coverage_summary: dict[str, Any] = Field(default_factory=dict)
    unresolved_items: list[str] = Field(default_factory=list)
    final_verdict: FinalVerdict = Field(default_factory=FinalVerdict)
    artifact_paths: dict[str, Path] = Field(default_factory=dict)
