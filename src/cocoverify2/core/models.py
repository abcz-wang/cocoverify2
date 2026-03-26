"""Core pydantic models used across the cocoverify2 pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from cocoverify2.core.types import LatencyModel, PortDirection, SequentialKind, TestCategory, VerdictKind


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
    expected_properties: list[str] = Field(default_factory=list)
    observed_signals: list[str] = Field(default_factory=list)
    timing_assumptions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    coverage_tags: list[str] = Field(default_factory=list)
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


class OracleSpec(ModelBase):
    """Structured oracle artifact produced independently from the test plan."""

    protocol_oracle: dict[str, Any] = Field(default_factory=dict)
    functional_oracle: dict[str, Any] = Field(default_factory=dict)
    property_oracle: dict[str, Any] = Field(default_factory=dict)
    unresolved_items: list[str] = Field(default_factory=list)
    oracle_confidence: float = Field(default=0.0, ge=0.0, le=1.0)


class SimulationConfig(ModelBase):
    """Execution configuration for simulator invocation."""

    runner_mode: str = "cocotb_tools"
    simulator: str = "icarus"
    rtl_sources: list[Path] = Field(default_factory=list)
    filelist: Path | None = None
    include_dirs: list[Path] = Field(default_factory=list)
    defines: dict[str, str] = Field(default_factory=dict)
    parameters: dict[str, Any] = Field(default_factory=dict)
    toplevel: str = ""
    test_dir: Path = Path("generated_tb")
    timeout_seconds: int = Field(default=60, ge=1)
    waves: bool = False


class SimulationResult(ModelBase):
    """Structured result from the simulation execution layer."""

    build_passed: bool = False
    tests_passed: bool = False
    executed_cases: list[str] = Field(default_factory=list)
    passed_cases: list[str] = Field(default_factory=list)
    failed_cases: list[str] = Field(default_factory=list)
    build_log_path: Path | None = None
    test_log_path: Path | None = None
    junit_xml_path: Path | None = None
    waveform_path: Path | None = None
    runner_metadata: dict[str, Any] = Field(default_factory=dict)


class TriageResult(ModelBase):
    """Structured triage outcome after simulation analysis."""

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
