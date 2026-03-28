"""Phase 6 triage tests."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from cocoverify2.core.models import RenderMetadata, RenderedFile, RunnerSelection, SimulationResult
from cocoverify2.core.types import ExecutionStatus, SimulationMode
from cocoverify2.stages.triage import TriageStage
from cocoverify2.utils.files import ensure_dir, write_json, write_text


def _write_run_fixture(
    root: Path,
    *,
    status: ExecutionStatus,
    build_log: str = "",
    test_log: str = "",
    stdout: str = "",
    stderr: str = "",
    failed_tests: list[str] | None = None,
    passed_tests: list[str] | None = None,
    discovered_tests: list[str] | None = None,
    execution_notes: list[str] | None = None,
    runner_warnings: list[str] | None = None,
    render_warnings: list[str] | None = None,
    render_confidence: float = 0.8,
    return_code: int | None = 0,
) -> Path:
    run_dir = ensure_dir(root / "run")
    logs_dir = ensure_dir(run_dir / "logs")
    build_log_path = logs_dir / "build.log"
    test_log_path = logs_dir / "test.log"
    stdout_path = logs_dir / "stdout.txt"
    stderr_path = logs_dir / "stderr.txt"
    write_text(build_log_path, build_log)
    write_text(test_log_path, test_log or build_log)
    write_text(stdout_path, stdout)
    write_text(stderr_path, stderr)

    render_path = root / "render" / "metadata.json"
    render_metadata = RenderMetadata(
        module_name="demo",
        based_on_contract="contract/contract.json",
        based_on_plan="plan/test_plan.json",
        based_on_oracle="oracle/oracle.json",
        generated_files=[
            RenderedFile(
                relative_path="cocotb_tests/test_demo_basic.py",
                role="test_module",
                description="demo",
            )
        ],
        test_modules=["test_demo_basic"],
        oracle_summary={"empty_functional_cases": []},
        render_warnings=render_warnings or [],
        render_confidence=render_confidence,
    )
    write_json(render_path, render_metadata.model_dump(mode="json"))
    write_json(run_dir / "copied_or_linked_render_metadata.json", render_metadata.model_dump(mode="json"))

    selection = RunnerSelection(
        requested_mode=SimulationMode.AUTO,
        selected_mode=SimulationMode.MAKE,
        backend="make",
        render_metadata_path=str(render_path),
        package_dir=str(root / "render" / "cocotb_tests"),
        reasons=["test fixture"],
        warnings=[],
        resolved_rtl_sources=["dut.v"],
    )
    write_json(run_dir / "runner_selection.json", selection.model_dump(mode="json"))

    simulation_result = SimulationResult(
        module_name="demo",
        based_on_render_metadata=str(render_path),
        selected_mode=SimulationMode.MAKE,
        selected_simulator="icarus",
        command=["make"],
        return_code=return_code,
        status=status,
        discovered_tests=discovered_tests or list(failed_tests or []) + list(passed_tests or []),
        executed_tests=list(failed_tests or []) + list(passed_tests or []),
        passed_tests=passed_tests or [],
        failed_tests=failed_tests or [],
        skipped_tests=[],
        log_paths={
            "build_log": str(build_log_path),
            "test_log": str(test_log_path),
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
        },
        runner_warnings=runner_warnings or [],
        execution_notes=execution_notes or ["fixture generated"],
    )
    write_json(run_dir / "simulation_result.json", simulation_result.model_dump(mode="json"))
    return root


def test_success_run_triages_to_no_failure(tmp_path: Path) -> None:
    root = _write_run_fixture(
        tmp_path / "success_case",
        status=ExecutionStatus.SUCCESS,
        build_log="cocotb_tests.test_demo_basic.test_basic_001 passed\n",
        passed_tests=["cocotb_tests.test_demo_basic.test_basic_001"],
        discovered_tests=["cocotb_tests.test_demo_basic.test_basic_001"],
    )

    result = TriageStage().run_from_dir(in_dir=root, out_dir=tmp_path / "triage_out")

    assert result.primary_category == "no_failure"
    assert result.suspected_layer == "none"
    assert result.confidence >= 0.9
    assert "simulation_status=success" in result.evidence


def test_missing_tool_environment_failure_triages_cleanly(tmp_path: Path) -> None:
    root = _write_run_fixture(
        tmp_path / "env_case",
        status=ExecutionStatus.ENVIRONMENT_ERROR,
        build_log="Required tool 'cocotb-config' is unavailable; make-mode preflight could not resolve the cocotb makefiles directory.\n",
        return_code=None,
    )

    result = TriageStage().run_from_dir(in_dir=root, out_dir=tmp_path / "triage_env")

    assert result.primary_category == "environment_error"
    assert result.suspected_layer == "environment"
    assert "execution_infrastructure_error" in result.secondary_categories
    assert any("cocotb-config" in fragment for fragment in result.matched_log_fragments)


def test_internal_rendered_package_import_failure_is_artifact_contract_error(tmp_path: Path) -> None:
    root = _write_run_fixture(
        tmp_path / "artifact_case",
        status=ExecutionStatus.ENVIRONMENT_ERROR,
        build_log="ModuleNotFoundError: No module named 'cocotb_tests'\n",
        return_code=2,
    )

    result = TriageStage().run_from_dir(in_dir=root, out_dir=tmp_path / "triage_artifact")

    assert result.primary_category == "artifact_contract_error"
    assert result.primary_category != "environment_error"
    assert result.suspected_layer == "render_run_contract"


def test_compile_and_elaboration_status_passthrough(tmp_path: Path) -> None:
    compile_root = _write_run_fixture(
        tmp_path / "compile_case",
        status=ExecutionStatus.COMPILE_ERROR,
        build_log="syntax error near token ';'\n",
        return_code=1,
    )
    elaboration_root = _write_run_fixture(
        tmp_path / "elab_case",
        status=ExecutionStatus.ELABORATION_ERROR,
        build_log="unable to bind wire/reg/memory 'top.u_missing'\n",
        return_code=1,
    )

    compile_result = TriageStage().run_from_dir(in_dir=compile_root, out_dir=tmp_path / "triage_compile")
    elaboration_result = TriageStage().run_from_dir(in_dir=elaboration_root, out_dir=tmp_path / "triage_elab")

    assert compile_result.primary_category == "compile_error"
    assert compile_result.suspected_layer == "rtl_build"
    assert elaboration_result.primary_category == "elaboration_error"
    assert elaboration_result.suspected_layer == "rtl_integration"


def test_timeout_passthrough(tmp_path: Path) -> None:
    root = _write_run_fixture(
        tmp_path / "timeout_case",
        status=ExecutionStatus.TIMEOUT,
        build_log="simulation timed out after 60 seconds\n",
        return_code=None,
    )

    result = TriageStage().run_from_dir(in_dir=root, out_dir=tmp_path / "triage_timeout")

    assert result.primary_category == "timeout_error"
    assert result.suspected_layer == "execution"


def test_runtime_failure_with_weak_render_stays_conservative(tmp_path: Path) -> None:
    root = _write_run_fixture(
        tmp_path / "runtime_case",
        status=ExecutionStatus.RUNTIME_ERROR,
        build_log="FAILED cocotb_tests.test_demo_basic.test_basic_001\nAssertionError: observed mismatch\n",
        failed_tests=["cocotb_tests.test_demo_basic.test_basic_001"],
        discovered_tests=["cocotb_tests.test_demo_basic.test_basic_001"],
        return_code=1,
        render_warnings=[
            "Timing is unresolved; rendering preserves event-based and safety-style checks only.",
            "Contract confidence is low; interface and testcase rendering remain conservative.",
            "Some functional oracle cases are intentionally empty; render output preserves them as conservative protocol/property-driven tests.",
        ],
        render_confidence=0.42,
    )

    result = TriageStage().run_from_dir(in_dir=root, out_dir=tmp_path / "triage_runtime")

    assert result.primary_category == "runtime_test_failure"
    assert "weak_testbench" in result.secondary_categories
    assert "unresolved_ambiguity" in result.secondary_categories
    assert "likely_dut_bug" not in result.secondary_categories
    assert any(item.startswith("failed_tests_count=1") for item in result.evidence)


def test_stage_triage_cli_smoke(tmp_path: Path) -> None:
    root = _write_run_fixture(
        tmp_path / "cli_case",
        status=ExecutionStatus.SUCCESS,
        build_log="cocotb_tests.test_demo_basic.test_basic_001 passed\n",
        passed_tests=["cocotb_tests.test_demo_basic.test_basic_001"],
        discovered_tests=["cocotb_tests.test_demo_basic.test_basic_001"],
    )

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cocoverify2.cli",
            "stage",
            "triage",
            "--in-dir",
            str(root),
            "--out-dir",
            str(tmp_path / "cli_triage_out"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Triage completed for module 'demo' with category 'no_failure'" in result.stdout
    assert (tmp_path / "cli_triage_out" / "triage" / "triage.json").exists()
    assert (tmp_path / "cli_triage_out" / "triage" / "triage_summary.yaml").exists()
