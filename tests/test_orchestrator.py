"""Tests for the minimal Phase 7/8 verification orchestrator loop."""

from __future__ import annotations

from pathlib import Path

from cocoverify2.core.config import VerificationConfig
from cocoverify2.core.models import (
    DUTContract,
    OracleSpec,
    RenderMetadata,
    RepairAction,
    RunnerSelection,
    TestPlan as CVTestPlan,
    SimulationConfig,
    SimulationResult,
    TriageResult,
)
from cocoverify2.core.orchestrator import VerificationOrchestrator
from cocoverify2.core.types import ExecutionStatus, SimulationMode, VerdictKind
from cocoverify2.utils.files import read_json


class _FakeContractStage:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, **_: object) -> DUTContract:
        self.calls += 1
        return DUTContract(module_name="demo")


class _FakePlanStage:
    def __init__(self) -> None:
        self.calls = 0

    def run_from_artifact(self, **_: object) -> CVTestPlan:
        self.calls += 1
        return CVTestPlan(module_name="demo", based_on_contract="contract/contract.json", plan_strategy="fake")


class _FakeOracleStage:
    def __init__(self) -> None:
        self.calls = 0

    def run_from_artifacts(self, **_: object) -> OracleSpec:
        self.calls += 1
        return OracleSpec(module_name="demo", based_on_contract="contract/contract.json", based_on_plan="plan/test_plan.json")


class _FakeRenderStage:
    def __init__(self) -> None:
        self.calls = 0

    def run_from_artifacts(self, **_: object) -> RenderMetadata:
        self.calls += 1
        return RenderMetadata(module_name="demo", based_on_contract="contract/contract.json")


class _FakeRunStage:
    def __init__(self, statuses: list[ExecutionStatus]) -> None:
        self.calls = 0
        self._statuses = list(statuses)
        self.rtl_history: list[list[Path]] = []

    def run_from_artifact(self, **kwargs: object) -> SimulationResult:
        self.calls += 1
        config = kwargs["config"]
        self.rtl_history.append(list(config.rtl_sources))
        status = self._statuses.pop(0)
        return SimulationResult(
            module_name="demo",
            based_on_render_metadata="render/metadata.json",
            selected_mode=SimulationMode.AUTO,
            selected_simulator="icarus",
            status=status,
        )


class _FakeTriageStage:
    def __init__(self, categories: list[str]) -> None:
        self.calls = 0
        self._categories = list(categories)

    def run_from_dir(self, **_: object) -> TriageResult:
        self.calls += 1
        category = self._categories.pop(0)
        source_status = "success" if category == "no_failure" else "runtime_error"
        return TriageResult(
            module_name="demo",
            based_on_simulation_result="run/simulation_result.json",
            source_status=source_status,
            primary_category=category,
            suspected_layer="dut_or_testbench" if category != "no_failure" else "none",
        )


class _FakeRepairStage:
    def __init__(self, action_sequences: list[list[RepairAction]]) -> None:
        self.calls = 0
        self._action_sequences = list(action_sequences)

    def run(self, **_: object) -> list[RepairAction]:
        self.calls += 1
        return self._action_sequences.pop(0)


def _build_stages(
    *,
    run_statuses: list[ExecutionStatus],
    triage_categories: list[str],
    repair_sequences: list[list[RepairAction]],
) -> dict[str, object]:
    return {
        "contract": _FakeContractStage(),
        "plan": _FakePlanStage(),
        "oracle": _FakeOracleStage(),
        "render": _FakeRenderStage(),
        "run": _FakeRunStage(run_statuses),
        "triage": _FakeTriageStage(triage_categories),
        "repair": _FakeRepairStage(repair_sequences),
    }


def test_verify_succeeds_without_repair(tmp_path: Path) -> None:
    stages = _build_stages(
        run_statuses=[ExecutionStatus.SUCCESS],
        triage_categories=["no_failure"],
        repair_sequences=[],
    )
    report = VerificationOrchestrator(config=VerificationConfig(max_repair_rounds=1), stages=stages).verify(
        rtl=[tmp_path / "demo.v"],
        task_id="demo",
        task_description="demo smoke",
        out_dir=tmp_path / "out",
        simulation_config=SimulationConfig(),
    )

    assert report.final_verdict.verdict == VerdictKind.PASS
    assert report.repair_actions == []
    assert stages["contract"].calls == 1
    assert stages["plan"].calls == 1
    assert stages["oracle"].calls == 1
    assert stages["render"].calls == 1
    assert stages["run"].calls == 1
    assert stages["triage"].calls == 1
    assert stages["repair"].calls == 0
    payload = read_json(tmp_path / "out" / "report" / "verification_report.json")
    assert payload["final_verdict"]["verdict"] == "pass"


def test_verify_reruns_only_downstream_stages_after_repair(tmp_path: Path) -> None:
    stages = _build_stages(
        run_statuses=[ExecutionStatus.RUNTIME_ERROR, ExecutionStatus.SUCCESS],
        triage_categories=["runtime_test_failure", "no_failure"],
        repair_sequences=[
            [
                RepairAction(
                    target_stage="plan",
                    reason="refresh plan and downstream",
                    artifacts_to_keep=["contract"],
                    artifacts_to_regenerate=["plan", "oracle", "render", "run", "triage"],
                )
            ]
        ],
    )
    report = VerificationOrchestrator(config=VerificationConfig(max_repair_rounds=1), stages=stages).verify(
        rtl=[tmp_path / "demo.v"],
        task_id="demo",
        task_description="demo rerun",
        out_dir=tmp_path / "out",
        simulation_config=SimulationConfig(),
    )

    assert report.final_verdict.verdict == VerdictKind.PASS
    assert len(report.repair_actions) == 1
    assert stages["contract"].calls == 1
    assert stages["plan"].calls == 2
    assert stages["oracle"].calls == 2
    assert stages["render"].calls == 2
    assert stages["run"].calls == 2
    assert stages["triage"].calls == 2
    assert stages["repair"].calls == 1
    assert report.coverage_summary["repair_rounds_used"] == 1


def test_verify_uses_golden_rtl_for_initial_and_repair_runs(tmp_path: Path) -> None:
    stages = _build_stages(
        run_statuses=[ExecutionStatus.RUNTIME_ERROR, ExecutionStatus.SUCCESS],
        triage_categories=["runtime_test_failure", "no_failure"],
        repair_sequences=[
            [
                RepairAction(
                    target_stage="render",
                    reason="rerender and rerun",
                    artifacts_to_keep=["contract", "plan", "oracle"],
                    artifacts_to_regenerate=["render", "run", "triage"],
                )
            ]
        ],
    )
    generation_rtl = tmp_path / "generation_demo.v"
    golden_rtl = tmp_path / "verified_demo.v"

    report = VerificationOrchestrator(config=VerificationConfig(max_repair_rounds=1), stages=stages).verify(
        rtl=[generation_rtl],
        golden_rtl=[golden_rtl],
        task_id="demo",
        task_description="demo golden",
        out_dir=tmp_path / "out",
        simulation_config=SimulationConfig(),
    )

    assert report.final_verdict.verdict == VerdictKind.PASS
    assert stages["run"].rtl_history == [[golden_rtl], [golden_rtl]]
    assert report.coverage_summary["validation_inputs"]["generation_rtl_sources"] == [str(generation_rtl)]
    assert report.coverage_summary["validation_inputs"]["golden_rtl_sources"] == [str(golden_rtl)]
    assert report.coverage_summary["validation_inputs"]["golden_rtl_fallback_used"] is False


def test_verify_stops_at_repair_cap_when_failure_persists(tmp_path: Path) -> None:
    stages = _build_stages(
        run_statuses=[ExecutionStatus.RUNTIME_ERROR, ExecutionStatus.RUNTIME_ERROR],
        triage_categories=["runtime_test_failure", "runtime_test_failure"],
        repair_sequences=[
            [
                RepairAction(
                    target_stage="render",
                    reason="rerender and rerun",
                    artifacts_to_keep=["contract", "plan", "oracle"],
                    artifacts_to_regenerate=["render", "run", "triage"],
                )
            ]
        ],
    )
    report = VerificationOrchestrator(config=VerificationConfig(max_repair_rounds=1), stages=stages).verify(
        rtl=[tmp_path / "demo.v"],
        task_id="demo",
        task_description="demo cap",
        out_dir=tmp_path / "out",
        simulation_config=SimulationConfig(),
    )

    assert report.final_verdict.verdict == VerdictKind.FAIL
    assert stages["contract"].calls == 1
    assert stages["plan"].calls == 1
    assert stages["oracle"].calls == 1
    assert stages["render"].calls == 2
    assert stages["run"].calls == 2
    assert stages["triage"].calls == 2
    assert stages["repair"].calls == 1


def test_verify_records_rtl_fallback_when_golden_rtl_is_absent(tmp_path: Path) -> None:
    stages = _build_stages(
        run_statuses=[ExecutionStatus.SUCCESS],
        triage_categories=["no_failure"],
        repair_sequences=[],
    )
    generation_rtl = tmp_path / "generation_demo.v"

    report = VerificationOrchestrator(config=VerificationConfig(max_repair_rounds=1), stages=stages).verify(
        rtl=[generation_rtl],
        task_id="demo",
        task_description="demo fallback",
        out_dir=tmp_path / "out",
        simulation_config=SimulationConfig(),
    )

    assert report.final_verdict.verdict == VerdictKind.PASS
    assert stages["run"].rtl_history == [[generation_rtl]]
    assert report.coverage_summary["validation_inputs"]["golden_rtl_fallback_used"] is True
