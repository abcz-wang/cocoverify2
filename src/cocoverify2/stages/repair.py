"""Conservative repair-planning stage for the minimal Phase 7 loop."""

from __future__ import annotations

from pathlib import Path

from cocoverify2.core.errors import ArtifactError
from cocoverify2.core.models import RepairAction, RenderMetadata, RunnerSelection, SimulationResult, TriageResult
from cocoverify2.core.types import StageName
from cocoverify2.stages.simulator_runner import load_render_metadata_artifact
from cocoverify2.stages.triage import (
    load_runner_selection_artifact,
    load_simulation_result_artifact,
)
from cocoverify2.utils.files import ensure_dir, read_json, write_json, write_yaml
from cocoverify2.utils.logging import get_logger

_STAGE_ORDER = {
    StageName.CONTRACT.value: 0,
    StageName.PLAN.value: 1,
    StageName.ORACLE.value: 2,
    StageName.RENDER.value: 3,
    StageName.RUN.value: 4,
    StageName.TRIAGE.value: 5,
}


class RepairPlannerStage:
    """Map triage outcomes to conservative, stage-local repair recommendations."""

    __test__ = False

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    def run_from_dir(self, *, in_dir: Path, out_dir: Path) -> list[RepairAction]:
        """Load triage and downstream evidence from an artifact root or triage directory."""
        artifact_root = _resolve_artifact_root(in_dir)
        triage_path = artifact_root / "triage" / "triage.json"
        if not triage_path.exists():
            raise ArtifactError(f"Repair planning could not locate triage.json under: {artifact_root}")
        return self.run_from_artifact(triage_path=triage_path, out_dir=out_dir)

    def run_from_artifact(self, *, triage_path: Path, out_dir: Path) -> list[RepairAction]:
        """Load artifacts referenced by a triage artifact and persist repair recommendations."""
        if not triage_path.exists():
            raise ArtifactError(f"Triage artifact does not exist: {triage_path}")
        triage = load_triage_artifact(triage_path)
        artifact_root = triage_path.parent.parent

        simulation_result_path = _resolve_path(
            triage.based_on_simulation_result,
            fallback=artifact_root / "run" / "simulation_result.json",
        )
        runner_selection_path = _resolve_path(
            triage.based_on_runner_selection,
            fallback=artifact_root / "run" / "runner_selection.json",
        )
        render_metadata_path = _resolve_path(
            triage.based_on_render_metadata,
            fallback=artifact_root / "render" / "metadata.json",
        )

        simulation_result = (
            load_simulation_result_artifact(simulation_result_path) if simulation_result_path and simulation_result_path.exists() else None
        )
        runner_selection = (
            load_runner_selection_artifact(runner_selection_path) if runner_selection_path and runner_selection_path.exists() else None
        )
        render_metadata = (
            load_render_metadata_artifact(render_metadata_path) if render_metadata_path and render_metadata_path.exists() else None
        )
        return self.run(
            triage=triage,
            triage_path=triage_path,
            simulation_result=simulation_result,
            simulation_result_path=simulation_result_path,
            runner_selection=runner_selection,
            runner_selection_path=runner_selection_path,
            render_metadata=render_metadata,
            render_metadata_path=render_metadata_path,
            out_dir=out_dir,
        )

    def run(
        self,
        *,
        triage: TriageResult,
        triage_path: Path | None,
        simulation_result: SimulationResult | None,
        simulation_result_path: Path | None,
        runner_selection: RunnerSelection | None,
        runner_selection_path: Path | None,
        render_metadata: RenderMetadata | None,
        render_metadata_path: Path | None,
        out_dir: Path,
    ) -> list[RepairAction]:
        """Recommend conservative repair actions and persist a structured artifact."""
        actions = _recommend_repair_actions(
            triage=triage,
            simulation_result=simulation_result,
            runner_selection=runner_selection,
            render_metadata=render_metadata,
        )
        repair_dir = ensure_dir(out_dir / "repair")
        payload = {
            "module_name": triage.module_name,
            "primary_category": triage.primary_category,
            "secondary_categories": triage.secondary_categories,
            "suspected_layer": triage.suspected_layer,
            "based_on_triage": str(triage_path) if triage_path else "",
            "based_on_simulation_result": str(simulation_result_path) if simulation_result_path else "",
            "based_on_runner_selection": str(runner_selection_path) if runner_selection_path else "",
            "based_on_render_metadata": str(render_metadata_path) if render_metadata_path else "",
            "repair_actions": [action.model_dump(mode="json") for action in actions],
        }
        write_json(repair_dir / "repair_actions.json", payload)
        write_yaml(repair_dir / "repair_summary.yaml", _build_repair_summary(triage=triage, actions=actions))
        self.logger.info(
            "Planned %d repair action(s) for module '%s' with triage=%s",
            len(actions),
            triage.module_name or "<unknown>",
            triage.primary_category,
        )
        return actions


def load_triage_artifact(path: Path) -> TriageResult:
    """Load a ``TriageResult`` artifact from JSON."""
    if not path.exists():
        raise ArtifactError(f"Triage artifact does not exist: {path}")
    return TriageResult.model_validate(read_json(path))


def earliest_repair_stage(actions: list[RepairAction]) -> str | None:
    """Return the earliest stage targeted by any recommended repair action."""
    if not actions:
        return None
    candidates = [action.target_stage for action in actions if action.target_stage in _STAGE_ORDER]
    if not candidates:
        return None
    return min(candidates, key=lambda item: _STAGE_ORDER[item])


def _resolve_artifact_root(in_dir: Path) -> Path:
    if not in_dir.exists():
        raise ArtifactError(f"Repair input directory does not exist: {in_dir}")
    if (in_dir / "triage" / "triage.json").exists():
        return in_dir
    if in_dir.name == "triage" and (in_dir / "triage.json").exists():
        return in_dir.parent
    if (in_dir / "triage.json").exists():
        return in_dir.parent
    if (in_dir / "run" / "simulation_result.json").exists() and (in_dir / "triage" / "triage.json").exists():
        return in_dir
    raise ArtifactError(
        "Repair planning requires a phase root containing triage/triage.json or a triage directory containing triage.json."
    )


def _resolve_path(raw_path: str | None, *, fallback: Path) -> Path | None:
    if raw_path:
        candidate = Path(raw_path)
        if candidate.exists():
            return candidate
    return fallback if fallback.exists() else None


def _recommend_repair_actions(
    *,
    triage: TriageResult,
    simulation_result: SimulationResult | None,
    runner_selection: RunnerSelection | None,
    render_metadata: RenderMetadata | None,
) -> list[RepairAction]:
    category = triage.primary_category
    secondary = set(triage.secondary_categories)

    if category == "no_failure":
        return []

    if category in {"configuration_error", "environment_error", "timeout_error"}:
        return [
            RepairAction(
                target_stage=StageName.RUN.value,
                reason="Execution-layer failure suggests refreshing simulator invocation without regenerating verification artifacts.",
                inputs_to_refresh=_refresh_inputs_for_run(simulation_result=simulation_result, runner_selection=runner_selection),
                artifacts_to_keep=["contract", "plan", "oracle", "render"],
                artifacts_to_regenerate=["run", "triage"],
            )
        ]

    if category == "artifact_contract_error":
        return [
            RepairAction(
                target_stage=StageName.RENDER.value,
                reason="The run stage reports a render/run contract mismatch, so rerendering the package is the earliest conservative refresh point.",
                inputs_to_refresh=["render_templates", "render_metadata"],
                artifacts_to_keep=["contract", "plan", "oracle"],
                artifacts_to_regenerate=["render", "run", "triage"],
            )
        ]

    if category in {"compile_error", "elaboration_error"}:
        return [
            RepairAction(
                target_stage=StageName.CONTRACT.value,
                reason="Compile or elaboration failures can indicate stale interface assumptions, so the repair loop should reextract the contract and regenerate all downstream artifacts.",
                inputs_to_refresh=["rtl_sources", "task_description", "spec_text"],
                artifacts_to_keep=[],
                artifacts_to_regenerate=["contract", "plan", "oracle", "render", "run", "triage"],
            )
        ]

    if category == "insufficient_stimulus":
        return [
            RepairAction(
                target_stage=StageName.PLAN.value,
                reason="Insufficient stimulus points to missing or weak planned scenarios, so regenerate the plan and everything downstream.",
                inputs_to_refresh=["test_plan_cases", "oracle_checks"],
                artifacts_to_keep=["contract"],
                artifacts_to_regenerate=["plan", "oracle", "render", "run", "triage"],
            )
        ]

    if category == "runtime_test_failure":
        if "weak_testbench" in secondary or triage.suspected_layer == "plan_render_gap":
            return [
                RepairAction(
                    target_stage=StageName.PLAN.value,
                    reason="Runtime failures with weak-testbench evidence suggest revisiting planned scenarios before regenerating downstream artifacts.",
                    inputs_to_refresh=["test_plan_cases", "oracle_checks"],
                    artifacts_to_keep=["contract"],
                    artifacts_to_regenerate=["plan", "oracle", "render", "run", "triage"],
                )
            ]
        return [
            RepairAction(
                target_stage=StageName.ORACLE.value,
                reason="Runtime test failures can stem from overly weak or mismatched oracle checks, so regenerate oracle-derived artifacts conservatively.",
                inputs_to_refresh=["oracle_checks", "rendered_assertions"],
                artifacts_to_keep=["contract", "plan"],
                artifacts_to_regenerate=["oracle", "render", "run", "triage"],
            )
        ]

    reasons = ["Regenerate the rendered package and rerun to refresh executable artifacts conservatively."]
    if render_metadata and render_metadata.render_warnings:
        reasons.append(render_metadata.render_warnings[0])
    return [
        RepairAction(
            target_stage=StageName.RENDER.value,
            reason=" ".join(reasons),
            inputs_to_refresh=["render_templates", "render_metadata"],
            artifacts_to_keep=["contract", "plan", "oracle"],
            artifacts_to_regenerate=["render", "run", "triage"],
        )
    ]


def _refresh_inputs_for_run(
    *,
    simulation_result: SimulationResult | None,
    runner_selection: RunnerSelection | None,
) -> list[str]:
    inputs = ["simulation_config", "runner_selection"]
    if simulation_result and simulation_result.selected_mode:
        inputs.append(f"selected_mode={simulation_result.selected_mode}")
    if runner_selection and runner_selection.backend:
        inputs.append(f"runner_backend={runner_selection.backend}")
    return inputs


def _build_repair_summary(*, triage: TriageResult, actions: list[RepairAction]) -> dict[str, object]:
    return {
        "module_name": triage.module_name,
        "primary_category": triage.primary_category,
        "secondary_categories": triage.secondary_categories,
        "suspected_layer": triage.suspected_layer,
        "recommended_target_stage": earliest_repair_stage(actions),
        "recommended_action_count": len(actions),
        "actions": [
            {
                "target_stage": action.target_stage,
                "reason": action.reason,
                "artifacts_to_keep": action.artifacts_to_keep,
                "artifacts_to_regenerate": action.artifacts_to_regenerate,
            }
            for action in actions
        ],
    }
