"""Thin orchestrator for the minimal Phase 7/8 closed-loop pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from cocoverify2.core.config import LLMConfig, VerificationConfig
from cocoverify2.core.errors import ConfigurationError
from cocoverify2.core.models import (
    DUTContract,
    FinalVerdict,
    OracleSpec,
    RenderMetadata,
    RepairAction,
    RunnerSelection,
    SimulationConfig,
    SimulationResult,
    TestPlan,
    TriageResult,
    VerificationReport,
)
from cocoverify2.core.types import GenerationMode, StageName, VerdictKind
from cocoverify2.stages.contract_extractor import ContractExtractor, load_optional_text
from cocoverify2.stages.oracle_generator import OracleGenerator
from cocoverify2.stages.repair import RepairPlannerStage, earliest_repair_stage
from cocoverify2.stages.simulator_runner import SimulatorRunnerStage
from cocoverify2.stages.tb_renderer import TBRenderer
from cocoverify2.stages.test_plan_generator import TestPlanGenerator
from cocoverify2.stages.triage import TriageStage, load_runner_selection_artifact
from cocoverify2.utils.files import ensure_dir, write_json, write_yaml
from cocoverify2.utils.logging import get_logger

_STAGE_ORDER = {
    StageName.CONTRACT.value: 0,
    StageName.PLAN.value: 1,
    StageName.ORACLE.value: 2,
    StageName.RENDER.value: 3,
    StageName.RUN.value: 4,
    StageName.TRIAGE.value: 5,
}


@dataclass(slots=True)
class _PipelineArtifacts:
    contract: DUTContract | None = None
    plan: TestPlan | None = None
    oracle: OracleSpec | None = None
    render: RenderMetadata | None = None
    simulation: SimulationResult | None = None
    runner_selection: RunnerSelection | None = None
    triage: TriageResult | None = None
    artifact_paths: dict[str, Path] = field(default_factory=dict)


class VerificationOrchestrator:
    """Coordinate stage execution without owning stage business logic."""

    def __init__(
        self,
        *,
        config: VerificationConfig | None = None,
        stages: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the orchestrator with optional dependency injection."""
        self.config = config or VerificationConfig()
        self.stages = {
            "contract": ContractExtractor(),
            "plan": TestPlanGenerator(),
            "oracle": OracleGenerator(),
            "render": TBRenderer(),
            "run": SimulatorRunnerStage(),
            "triage": TriageStage(),
            "repair": RepairPlannerStage(),
        }
        for key, stage in (stages or {}).items():
            normalized_key = key.value if hasattr(key, "value") else str(key)
            self.stages[normalized_key] = stage
        self.logger = get_logger(__name__, level=self.config.log_level)

    def verify(
        self,
        *,
        rtl: list[Path] | None = None,
        golden_rtl: list[Path] | None = None,
        task_id: str = "",
        task_description: str = "",
        spec: Path | None = None,
        golden_tb: Path | None = None,
        out_dir: Path | None = None,
        generation_mode: GenerationMode | str = GenerationMode.RULE_BASED,
        llm_config: LLMConfig | None = None,
        simulation_config: SimulationConfig | None = None,
        max_repair_rounds: int | None = None,
    ) -> VerificationReport:
        """Run the minimal closed-loop verification pipeline with bounded repair."""
        rtl_paths = list(rtl or [])
        if not rtl_paths:
            raise ConfigurationError("The verify command requires at least one RTL source.")
        requested_golden_rtl_paths = list(golden_rtl or self.config.golden_rtl_sources)
        golden_rtl_fallback_used = not requested_golden_rtl_paths
        validation_rtl_paths = list(requested_golden_rtl_paths or rtl_paths)

        artifact_root = out_dir or self.config.artifacts.out_dir
        ensure_dir(artifact_root)
        spec_text = load_optional_text(spec)
        generation_mode = GenerationMode(generation_mode)
        stage_llm_config = llm_config or self.config.llm
        stage_simulation_config = (simulation_config or SimulationConfig()).model_copy(deep=True)
        stage_simulation_config.rtl_sources = validation_rtl_paths

        repair_cap = self.config.max_repair_rounds if max_repair_rounds is None else max_repair_rounds
        artifacts = _PipelineArtifacts(artifact_paths=_default_artifact_paths(artifact_root))
        repair_actions_taken: list[RepairAction] = []
        attempt_summaries: list[dict[str, object]] = []
        repair_rounds_used = 0
        current_stage = StageName.CONTRACT.value

        while True:
            executed_stages = self._run_from_stage(
                start_stage=current_stage,
                rtl_paths=rtl_paths,
                task_description=task_description,
                spec_text=spec_text,
                out_dir=artifact_root,
                artifacts=artifacts,
                generation_mode=generation_mode,
                llm_config=stage_llm_config,
                simulation_config=stage_simulation_config,
            )
            attempt_summaries.append(
                {
                    "attempt_index": len(attempt_summaries),
                    "start_stage": current_stage,
                    "executed_stages": executed_stages,
                    "simulation_status": artifacts.simulation.status if artifacts.simulation else "",
                    "triage_category": artifacts.triage.primary_category if artifacts.triage else "",
                    "validation_rtl_sources": [str(path) for path in validation_rtl_paths],
                    "golden_validation": True,
                }
            )
            if artifacts.triage and artifacts.triage.primary_category == "no_failure":
                break
            if repair_rounds_used >= repair_cap:
                break
            if artifacts.triage is None:
                break

            actions = self.stages["repair"].run(
                triage=artifacts.triage,
                triage_path=artifacts.artifact_paths.get("triage"),
                simulation_result=artifacts.simulation,
                simulation_result_path=artifacts.artifact_paths.get("run"),
                runner_selection=artifacts.runner_selection,
                runner_selection_path=artifacts.artifact_paths.get("runner_selection"),
                render_metadata=artifacts.render,
                render_metadata_path=artifacts.artifact_paths.get("render"),
                out_dir=artifact_root,
            )
            repair_actions_taken.extend(actions)
            next_stage = earliest_repair_stage(actions)
            if next_stage is None:
                break
            current_stage = next_stage
            repair_rounds_used += 1

        report = VerificationReport(
            contract=artifacts.contract,
            test_plan_summary=artifacts.plan,
            oracle_summary=artifacts.oracle,
            simulation_summary=artifacts.simulation,
            triage=artifacts.triage,
            repair_actions=repair_actions_taken,
            coverage_summary={
                "task_id": task_id,
                "repair_loop_used": bool(repair_actions_taken),
                "repair_rounds_used": repair_rounds_used,
                "max_repair_rounds": repair_cap,
                "validation_inputs": {
                    "generation_rtl_sources": [str(path) for path in rtl_paths],
                    "golden_rtl_sources": [str(path) for path in validation_rtl_paths],
                    "golden_rtl_fallback_used": golden_rtl_fallback_used,
                    "golden_tb_ignored": golden_tb is not None,
                },
                "golden_validation_triage_category": artifacts.triage.primary_category if artifacts.triage else "",
                "golden_validation_source_status": artifacts.triage.source_status if artifacts.triage else "",
                "attempts": attempt_summaries,
            },
            unresolved_items=_build_unresolved_items(
                triage=artifacts.triage,
                golden_tb=golden_tb,
                golden_rtl_fallback_used=golden_rtl_fallback_used,
                repair_cap=repair_cap,
                repair_rounds_used=repair_rounds_used,
            ),
            final_verdict=_build_final_verdict(
                triage=artifacts.triage,
                repair_rounds_used=repair_rounds_used,
                repair_cap=repair_cap,
            ),
            artifact_paths=artifacts.artifact_paths,
        )
        _write_report_artifacts(out_dir=artifact_root, report=report)
        self.logger.info(
            "Verification completed for task '%s' with verdict=%s and triage=%s",
            task_id or "<unknown>",
            report.final_verdict.verdict,
            report.triage.primary_category if report.triage else "<none>",
        )
        return report

    def _run_from_stage(
        self,
        *,
        start_stage: str,
        rtl_paths: list[Path],
        task_description: str,
        spec_text: str | None,
        out_dir: Path,
        artifacts: _PipelineArtifacts,
        generation_mode: GenerationMode,
        llm_config: LLMConfig,
        simulation_config: SimulationConfig,
    ) -> list[str]:
        if start_stage not in _STAGE_ORDER:
            raise ConfigurationError(f"Unsupported repair stage target: {start_stage}")

        executed_stages: list[str] = []
        start_index = _STAGE_ORDER[start_stage]

        if start_index <= _STAGE_ORDER[StageName.CONTRACT.value]:
            artifacts.contract = self.stages["contract"].run(
                rtl_paths=rtl_paths,
                task_description=task_description or None,
                spec_text=spec_text,
                golden_interface_text=None,
                out_dir=out_dir,
            )
            executed_stages.append(StageName.CONTRACT.value)

        if start_index <= _STAGE_ORDER[StageName.PLAN.value]:
            artifacts.plan = self.stages["plan"].run_from_artifact(
                contract_path=artifacts.artifact_paths["contract"],
                task_description=task_description or None,
                spec_text=spec_text,
                out_dir=out_dir,
                generation_mode=generation_mode,
                llm_config=llm_config,
            )
            executed_stages.append(StageName.PLAN.value)

        if start_index <= _STAGE_ORDER[StageName.ORACLE.value]:
            artifacts.oracle = self.stages["oracle"].run_from_artifacts(
                contract_path=artifacts.artifact_paths["contract"],
                plan_path=artifacts.artifact_paths["plan"],
                task_description=task_description or None,
                spec_text=spec_text,
                out_dir=out_dir,
                generation_mode=generation_mode,
                llm_config=llm_config,
            )
            executed_stages.append(StageName.ORACLE.value)

        if start_index <= _STAGE_ORDER[StageName.RENDER.value]:
            artifacts.render = self.stages["render"].run_from_artifacts(
                contract_path=artifacts.artifact_paths["contract"],
                plan_path=artifacts.artifact_paths["plan"],
                oracle_path=artifacts.artifact_paths["oracle"],
                task_description=task_description or None,
                spec_text=spec_text,
                out_dir=out_dir,
            )
            executed_stages.append(StageName.RENDER.value)

        if start_index <= _STAGE_ORDER[StageName.RUN.value]:
            artifacts.simulation = self.stages["run"].run_from_artifact(
                render_metadata_path=artifacts.artifact_paths["render"],
                config=simulation_config,
                out_dir=out_dir,
            )
            artifacts.runner_selection = _load_runner_selection_optional(artifacts.artifact_paths["runner_selection"])
            executed_stages.append(StageName.RUN.value)

        if start_index <= _STAGE_ORDER[StageName.TRIAGE.value]:
            artifacts.triage = self.stages["triage"].run_from_dir(in_dir=out_dir, out_dir=out_dir)
            executed_stages.append(StageName.TRIAGE.value)

        return executed_stages


def _default_artifact_paths(out_dir: Path) -> dict[str, Path]:
    return {
        "contract": out_dir / "contract" / "contract.json",
        "plan": out_dir / "plan" / "test_plan.json",
        "oracle": out_dir / "oracle" / "oracle.json",
        "render": out_dir / "render" / "metadata.json",
        "run": out_dir / "run" / "simulation_result.json",
        "runner_selection": out_dir / "run" / "runner_selection.json",
        "triage": out_dir / "triage" / "triage.json",
        "repair": out_dir / "repair" / "repair_actions.json",
        "report": out_dir / "report" / "verification_report.json",
    }


def _load_runner_selection_optional(path: Path) -> RunnerSelection | None:
    if not path.exists():
        return None
    return load_runner_selection_artifact(path)


def _build_unresolved_items(
    *,
    triage: TriageResult | None,
    golden_tb: Path | None,
    golden_rtl_fallback_used: bool,
    repair_cap: int,
    repair_rounds_used: int,
) -> list[str]:
    unresolved: list[str] = []
    if golden_tb is not None:
        unresolved.append("golden_tb was provided, but golden validation is driven by golden_rtl rather than golden_tb.")
    if golden_rtl_fallback_used:
        unresolved.append("golden_rtl was not provided, so verification fell back to generation RTL for validation.")
    if triage is None:
        unresolved.append("No triage artifact was produced.")
        return unresolved
    if triage.primary_category != "no_failure" and repair_rounds_used >= repair_cap:
        unresolved.append(
            f"Repair rounds were exhausted with final triage category '{triage.primary_category}'."
        )
    if triage.primary_category in {"configuration_error", "environment_error", "timeout_error", "artifact_contract_error"}:
        unresolved.append("Final result remained bounded by environment or execution-layer limitations.")
    return unresolved


def _build_final_verdict(
    *,
    triage: TriageResult | None,
    repair_rounds_used: int,
    repair_cap: int,
) -> FinalVerdict:
    if triage is None:
        return FinalVerdict(
            verdict=VerdictKind.INCONCLUSIVE,
            confidence=0.2,
            false_positive_risk=0.5,
            false_negative_risk=0.5,
            rationale=["No final triage result was available to classify the verification attempt."],
        )
    if triage.primary_category == "no_failure":
        rationale = (
            ["Verification completed without needing a repair round."]
            if repair_rounds_used == 0
            else [f"Verification completed after {repair_rounds_used} repair round(s)."]
        )
        return FinalVerdict(
            verdict=VerdictKind.PASS,
            confidence=0.82 if repair_rounds_used == 0 else 0.72,
            false_positive_risk=0.22 if repair_rounds_used == 0 else 0.32,
            false_negative_risk=0.18,
            rationale=rationale,
        )
    if triage.primary_category in {"configuration_error", "environment_error", "timeout_error", "artifact_contract_error", "unknown_failure"}:
        return FinalVerdict(
            verdict=VerdictKind.INCONCLUSIVE,
            confidence=0.48,
            false_positive_risk=0.4,
            false_negative_risk=0.4,
            rationale=[
                f"Verification ended with triage category '{triage.primary_category}', which is treated as inconclusive in the minimal closed loop."
            ],
        )
    if triage.primary_category == "insufficient_stimulus":
        return FinalVerdict(
            verdict=VerdictKind.SUSPICIOUS,
            confidence=0.56,
            false_positive_risk=0.58,
            false_negative_risk=0.24,
            rationale=[
                "The repair loop ended with insufficient stimulus, so the result is suspicious rather than a strong pass/fail claim."
            ],
        )
    return FinalVerdict(
        verdict=VerdictKind.FAIL,
        confidence=0.74 if repair_rounds_used >= repair_cap else 0.64,
        false_positive_risk=0.18,
        false_negative_risk=0.36,
        rationale=[
            f"Verification ended with triage category '{triage.primary_category}' after {repair_rounds_used} repair round(s)."
        ],
    )


def _write_report_artifacts(*, out_dir: Path, report: VerificationReport) -> None:
    report_dir = ensure_dir(out_dir / "report")
    write_json(report_dir / "verification_report.json", report.model_dump(mode="json"))
    write_yaml(
        report_dir / "verification_summary.yaml",
        {
            "final_verdict": report.final_verdict.verdict,
            "final_confidence": report.final_verdict.confidence,
            "final_triage_category": report.triage.primary_category if report.triage else "",
            "repair_loop_used": bool(report.repair_actions),
            "repair_action_count": len(report.repair_actions),
            "validation_inputs": report.coverage_summary.get("validation_inputs", {}),
            "golden_validation_triage_category": report.coverage_summary.get("golden_validation_triage_category", ""),
            "artifact_paths": {key: str(path) for key, path in report.artifact_paths.items()},
            "unresolved_items": report.unresolved_items,
        },
    )
