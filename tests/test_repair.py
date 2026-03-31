"""Tests for the minimal Phase 7 repair planner."""

from __future__ import annotations

from pathlib import Path

from cocoverify2.core.models import SimulationResult, TriageResult
from cocoverify2.core.types import ExecutionStatus, SimulationMode
from cocoverify2.stages.repair import RepairPlannerStage, earliest_repair_stage
from cocoverify2.utils.files import ensure_dir, read_json, read_text, write_json


def _simulation_result(*, status: ExecutionStatus = ExecutionStatus.RUNTIME_ERROR) -> SimulationResult:
    return SimulationResult(
        module_name="demo",
        based_on_render_metadata="render/metadata.json",
        selected_mode=SimulationMode.AUTO,
        selected_simulator="icarus",
        status=status,
    )


def _triage_result(
    *,
    primary_category: str,
    source_status: str = "",
    secondary_categories: list[str] | None = None,
    suspected_layer: str = "unknown",
) -> TriageResult:
    return TriageResult(
        module_name="demo",
        based_on_simulation_result="run/simulation_result.json",
        source_status=source_status or primary_category,
        primary_category=primary_category,
        secondary_categories=secondary_categories or [],
        suspected_layer=suspected_layer,
    )


def test_compile_failure_recommends_contract_refresh_from_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    ensure_dir(root / "run")
    ensure_dir(root / "triage")
    write_json((root / "run" / "simulation_result.json"), _simulation_result(status=ExecutionStatus.COMPILE_ERROR).model_dump(mode="json"))
    write_json(
        (root / "triage" / "triage.json"),
        _triage_result(primary_category="compile_error", source_status="compile_error", suspected_layer="rtl_build").model_dump(
            mode="json"
        ),
    )

    actions = RepairPlannerStage().run_from_dir(in_dir=root, out_dir=root)

    assert len(actions) == 1
    action = actions[0]
    assert action.target_stage == "contract"
    assert action.artifacts_to_regenerate == ["contract", "plan", "oracle", "render", "run", "triage"]
    assert earliest_repair_stage(actions) == "contract"
    payload = read_json(root / "repair" / "repair_actions.json")
    assert payload["primary_category"] == "compile_error"
    assert payload["repair_actions"][0]["target_stage"] == "contract"


def test_runtime_failure_with_weak_testbench_prefers_plan_refresh(tmp_path: Path) -> None:
    actions = RepairPlannerStage().run(
        triage=_triage_result(
            primary_category="runtime_test_failure",
            source_status="runtime_error",
            secondary_categories=["weak_testbench"],
            suspected_layer="plan_render_gap",
        ),
        triage_path=tmp_path / "triage" / "triage.json",
        simulation_result=_simulation_result(),
        simulation_result_path=tmp_path / "run" / "simulation_result.json",
        runner_selection=None,
        runner_selection_path=None,
        render_metadata=None,
        render_metadata_path=None,
        out_dir=tmp_path,
    )

    assert len(actions) == 1
    action = actions[0]
    assert action.target_stage == "plan"
    assert action.artifacts_to_keep == ["contract"]
    assert action.artifacts_to_regenerate == ["plan", "oracle", "render", "run", "triage"]


def test_insufficient_stimulus_recommends_plan_refresh(tmp_path: Path) -> None:
    actions = RepairPlannerStage().run(
        triage=_triage_result(
            primary_category="insufficient_stimulus",
            source_status="runtime_error",
            suspected_layer="plan_render_gap",
        ),
        triage_path=tmp_path / "triage" / "triage.json",
        simulation_result=_simulation_result(),
        simulation_result_path=tmp_path / "run" / "simulation_result.json",
        runner_selection=None,
        runner_selection_path=None,
        render_metadata=None,
        render_metadata_path=None,
        out_dir=tmp_path,
    )

    assert len(actions) == 1
    assert actions[0].target_stage == "plan"
    assert "plan" in actions[0].artifacts_to_regenerate


def test_no_failure_produces_no_repair_actions(tmp_path: Path) -> None:
    actions = RepairPlannerStage().run(
        triage=_triage_result(primary_category="no_failure", source_status="success", suspected_layer="none"),
        triage_path=tmp_path / "triage" / "triage.json",
        simulation_result=_simulation_result(status=ExecutionStatus.SUCCESS),
        simulation_result_path=tmp_path / "run" / "simulation_result.json",
        runner_selection=None,
        runner_selection_path=None,
        render_metadata=None,
        render_metadata_path=None,
        out_dir=tmp_path,
    )

    assert actions == []
    assert earliest_repair_stage(actions) is None
    summary = read_text(tmp_path / "repair" / "repair_summary.yaml")
    assert "recommended_action_count: 0" in summary


def test_environment_failure_recommends_run_only_refresh(tmp_path: Path) -> None:
    actions = RepairPlannerStage().run(
        triage=_triage_result(
            primary_category="environment_error",
            source_status="environment_error",
            secondary_categories=["execution_infrastructure_error"],
            suspected_layer="environment",
        ),
        triage_path=tmp_path / "triage" / "triage.json",
        simulation_result=_simulation_result(status=ExecutionStatus.ENVIRONMENT_ERROR),
        simulation_result_path=tmp_path / "run" / "simulation_result.json",
        runner_selection=None,
        runner_selection_path=None,
        render_metadata=None,
        render_metadata_path=None,
        out_dir=tmp_path,
    )

    assert len(actions) == 1
    action = actions[0]
    assert action.target_stage == "run"
    assert action.artifacts_to_keep == ["contract", "plan", "oracle", "render"]
    assert action.artifacts_to_regenerate == ["run", "triage"]
