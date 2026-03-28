"""Simulation execution stage tests for Phase 5."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from cocoverify2.core.models import SimulationConfig
from cocoverify2.execution.make_runner import MakeRunner
from cocoverify2.execution.runner_base import RunnerContext
from cocoverify2.stages.contract_extractor import ContractExtractor
from cocoverify2.stages.oracle_generator import OracleGenerator
from cocoverify2.stages.simulator_runner import SimulatorRunnerStage, load_render_metadata_artifact
from cocoverify2.stages.tb_renderer import TBRenderer
from cocoverify2.stages.test_plan_generator import TestPlanGenerator
from cocoverify2.utils.subprocess import CommandExecutionResult

_FIXTURES = Path(__file__).parent / "fixtures"
_RTL = _FIXTURES / "rtl"


def _build_render_metadata(tmp_path: Path, rtl_name: str) -> Path:
    stem = rtl_name.removesuffix(".v")
    artifact_root = tmp_path / f"phase5_{stem}"
    contract = ContractExtractor().run(
        rtl_paths=[_RTL / rtl_name],
        task_description=None,
        spec_text=None,
        golden_interface_text=None,
        out_dir=artifact_root,
    )
    TestPlanGenerator().run(
        contract=contract,
        task_description=None,
        spec_text=None,
        out_dir=artifact_root,
        based_on_contract=str(artifact_root / "contract" / "contract.json"),
    )
    OracleGenerator().run_from_artifacts(
        contract_path=artifact_root / "contract" / "contract.json",
        plan_path=artifact_root / "plan" / "test_plan.json",
        task_description=None,
        spec_text=None,
        out_dir=artifact_root,
    )
    TBRenderer().run_from_artifacts(
        contract_path=artifact_root / "contract" / "contract.json",
        plan_path=artifact_root / "plan" / "test_plan.json",
        oracle_path=artifact_root / "oracle" / "oracle.json",
        task_description=None,
        spec_text=None,
        out_dir=artifact_root,
    )
    return artifact_root / "render" / "metadata.json"


def _fake_command_result(*, cwd: Path, return_code: int = 0, stdout: str = "", stderr: str = "", timed_out: bool = False, error_type: str | None = None) -> CommandExecutionResult:
    return CommandExecutionResult(
        command=["fake-runner"],
        cwd=str(cwd),
        return_code=return_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        error_type=error_type,
        start_time=datetime.now(timezone.utc),
        end_time=datetime.now(timezone.utc),
        duration_seconds=0.1,
    )


def test_runner_selection_auto_prefers_make_and_records_reason(tmp_path: Path, monkeypatch) -> None:
    render_path = _build_render_metadata(tmp_path, "simple_comb.v")
    stage = SimulatorRunnerStage()

    def fake_execute(*, metadata, config, selection, context):
        return _fake_command_result(cwd=context.package_dir, stdout="no tests discovered\n")

    monkeypatch.setattr(stage._runners["make"], "execute", fake_execute)
    result = stage.run_from_artifact(
        render_metadata_path=render_path,
        config=SimulationConfig(mode="auto", rtl_sources=[_RTL / "simple_comb.v"]),
        out_dir=tmp_path / "run_auto",
    )

    selection_payload = json.loads((tmp_path / "run_auto" / "run" / "runner_selection.json").read_text(encoding="utf-8"))
    assert result.selected_mode == "make"
    assert selection_payload["selected_mode"] == "make"
    assert any("Makefile" in item for item in selection_payload["reasons"])


def test_runner_selection_ignores_non_executable_makefile_contract(tmp_path: Path) -> None:
    render_path = _build_render_metadata(tmp_path, "simple_comb.v")
    metadata = load_render_metadata_artifact(render_path)
    makefile_path = render_path.parent / "cocotb_tests" / "Makefile"
    makefile_path.write_text(
        "# legacy scaffold\nTOPLEVEL ?= simple_comb\nMODULE ?= test_simple_comb_basic\nSIM ?= icarus\n",
        encoding="utf-8",
    )
    stage = SimulatorRunnerStage()
    selection, _ = stage._select_runner(
        metadata=metadata,
        render_metadata_path=render_path,
        config=SimulationConfig(mode="auto", rtl_sources=[_RTL / "simple_comb.v"]),
    )

    assert selection.selected_mode == "cocotb_tools"
    assert any("does not satisfy the executable-shell contract" in item for item in selection.warnings)


def test_filelist_mode_resolves_sources_and_partial_support_warnings(tmp_path: Path) -> None:
    render_path = _build_render_metadata(tmp_path, "simple_comb.v")
    metadata = load_render_metadata_artifact(render_path)
    filelist = tmp_path / "demo.f"
    filelist.write_text(
        f"+incdir+{(_RTL).as_posix()}\n"
        f"{(_RTL / 'simple_comb.v').as_posix()}\n"
        "-f nested.f\n",
        encoding="utf-8",
    )
    stage = SimulatorRunnerStage()
    selection, resolved_config = stage._select_runner(
        metadata=metadata,
        render_metadata_path=render_path,
        config=SimulationConfig(mode="filelist", filelist_path=filelist),
    )

    assert selection.selected_mode == "filelist"
    assert selection.resolved_rtl_sources == [str((_RTL / "simple_comb.v").resolve())]
    assert resolved_config.include_dirs
    assert any("Nested filelist" in item for item in selection.warnings)


def test_make_runner_injects_include_dirs_parameters_defines_and_existing_controls(tmp_path: Path, monkeypatch) -> None:
    render_path = _build_render_metadata(tmp_path, "simple_seq.v")
    metadata = load_render_metadata_artifact(render_path)
    config = SimulationConfig(
        mode="make",
        rtl_sources=[_RTL / "simple_seq.v"],
        include_dirs=[_RTL],
        parameters={"WIDTH": "16"},
        defines={"ENABLE_TRACE": "1", "FLAG_ONLY": ""},
        plusargs=["+trace=1"],
        junit_enabled=True,
        waves_enabled=True,
    )
    selection, _ = SimulatorRunnerStage()._select_runner(
        metadata=metadata,
        render_metadata_path=render_path,
        config=config,
    )
    captured: dict[str, object] = {}

    def fake_execute_command(command, *, cwd, extra_env, timeout_seconds):
        if command[:2] == ["cocotb-config", "--makefiles"]:
            return CommandExecutionResult(
                command=list(command),
                cwd=str(cwd),
                return_code=0,
                stdout=str(tmp_path / "fake_makefiles"),
                stderr="",
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                duration_seconds=0.01,
            )
        captured["command"] = command
        captured["cwd"] = cwd
        captured["env"] = dict(extra_env or {})
        captured["timeout_seconds"] = timeout_seconds
        return _fake_command_result(cwd=Path(cwd))

    (tmp_path / "fake_makefiles").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr("cocoverify2.execution.make_runner.execute_command", fake_execute_command)
    runner = MakeRunner()
    result = runner.execute(
        metadata=metadata,
        config=config,
        selection=selection,
        context=RunnerContext(
            render_metadata_path=render_path,
            render_dir=render_path.parent,
            package_dir=render_path.parent / "cocotb_tests",
            run_dir=tmp_path / "run",
            logs_dir=tmp_path / "logs",
            junit_dir=tmp_path / "junit",
            waves_dir=tmp_path / "waves",
        ),
    )

    assert result.return_code == 0
    assert captured["command"] == ["make"]
    env = captured["env"]
    assert env["MODULE"] == "cocotb_tests.test_simple_seq_basic"
    assert str(render_path.parent.resolve()) in env["PYTHONPATH"].split(os.pathsep)
    assert env["COCOTB_MAKEFILES_DIR"] == str(tmp_path / "fake_makefiles")
    assert env["INCLUDE_DIRS"] == str(_RTL)
    assert env["PARAMETER_OVERRIDES"] == "WIDTH=16"
    assert env["DEFINE_OVERRIDES"] == "ENABLE_TRACE=1 FLAG_ONLY"
    assert env["PLUSARGS"] == "+trace=1"
    assert env["WAVES"] == "1"
    assert env["COCOTB_RESULTS_FILE"].endswith("results.xml")


def test_missing_tool_is_reported_as_environment_error(tmp_path: Path, monkeypatch) -> None:
    render_path = _build_render_metadata(tmp_path, "simple_comb.v")
    stage = SimulatorRunnerStage()

    def fake_execute(*, metadata, config, selection, context):
        return _fake_command_result(cwd=context.package_dir, error_type="missing_tool", stderr="make: not found")

    monkeypatch.setattr(stage._runners["make"], "execute", fake_execute)
    result = stage.run_from_artifact(
        render_metadata_path=render_path,
        config=SimulationConfig(mode="auto", rtl_sources=[_RTL / "simple_comb.v"]),
        out_dir=tmp_path / "run_env_error",
    )

    assert result.status == "environment_error"
    assert (tmp_path / "run_env_error" / "run" / "simulation_result.json").exists()


def test_makefile_structure_failure_regression_is_blocked_before_make_execution(tmp_path: Path, monkeypatch) -> None:
    render_path = _build_render_metadata(tmp_path, "simple_comb.v")
    makefile_path = render_path.parent / "cocotb_tests" / "Makefile"
    makefile_path.write_text(
        "# broken makefile that exists but has no executable contract\n",
        encoding="utf-8",
    )
    stage = SimulatorRunnerStage()
    make_called = {"value": False}

    def fake_make_execute(*, metadata, config, selection, context):
        make_called["value"] = True
        return _fake_command_result(cwd=context.package_dir, return_code=2, stderr="No targets. Stop.")

    def fake_cocotb_execute(*, metadata, config, selection, context):
        return _fake_command_result(cwd=context.render_dir, error_type="missing_tool", stderr="python: No module named cocotb_tools")

    monkeypatch.setattr(stage._runners["make"], "execute", fake_make_execute)
    monkeypatch.setattr(stage._runners["cocotb_tools"], "execute", fake_cocotb_execute)
    result = stage.run_from_artifact(
        render_metadata_path=render_path,
        config=SimulationConfig(mode="auto", rtl_sources=[_RTL / "simple_comb.v"]),
        out_dir=tmp_path / "run_broken_makefile",
    )

    assert make_called["value"] is False
    assert result.selected_mode == "cocotb_tools"
    assert result.status == "environment_error"
    assert "No targets. Stop." not in Path(result.log_paths["build_log"]).read_text(encoding="utf-8")


def test_missing_cocotb_config_returns_clean_environment_failure_before_make(tmp_path: Path, monkeypatch) -> None:
    render_path = _build_render_metadata(tmp_path, "simple_comb.v")
    stage = SimulatorRunnerStage()
    calls: list[list[str]] = []

    def fake_execute_command(command, *, cwd, extra_env, timeout_seconds):
        calls.append(list(command))
        if command[:2] == ["cocotb-config", "--makefiles"]:
            return CommandExecutionResult(
                command=list(command),
                cwd=str(cwd),
                return_code=None,
                stdout="",
                stderr="cocotb-config missing",
                error_type="missing_tool",
                error_message="cocotb-config missing",
                start_time=datetime.now(timezone.utc),
                end_time=datetime.now(timezone.utc),
                duration_seconds=0.01,
            )
        raise AssertionError("real make must not execute when cocotb-config preflight fails")

    monkeypatch.setattr("cocoverify2.execution.make_runner.execute_command", fake_execute_command)
    result = stage.run_from_artifact(
        render_metadata_path=render_path,
        config=SimulationConfig(mode="auto", rtl_sources=[_RTL / "simple_comb.v"]),
        out_dir=tmp_path / "run_missing_cocotb_config",
    )

    build_log = Path(result.log_paths["build_log"]).read_text(encoding="utf-8")
    assert calls == [["cocotb-config", "--makefiles"]]
    assert result.selected_mode == "make"
    assert result.status == "environment_error"
    assert "cocotb-config" in build_log
    assert "/Makefile.sim" not in build_log
    assert "No rule to make target '/Makefile.sim'" not in build_log
    assert "/Makefile.sim: No such file or directory" not in build_log


def test_missing_render_artifact_returns_structured_error_result(tmp_path: Path) -> None:
    stage = SimulatorRunnerStage()
    missing_path = tmp_path / "missing" / "metadata.json"
    result = stage.run_from_artifact(
        render_metadata_path=missing_path,
        config=SimulationConfig(mode="auto"),
        out_dir=tmp_path / "run_missing",
    )

    assert result.status == "environment_error"
    assert result.based_on_render_metadata == str(missing_path)
    assert (tmp_path / "run_missing" / "run" / "runner_selection.json").exists()


def test_mocked_cocotb_success_path_generates_structured_counts(tmp_path: Path, monkeypatch) -> None:
    render_path = _build_render_metadata(tmp_path, "simple_comb.v")
    stage = SimulatorRunnerStage()

    def fake_execute(*, metadata, config, selection, context):
        context.junit_dir.mkdir(parents=True, exist_ok=True)
        (context.junit_dir / "results.xml").write_text(
            """
<testsuite name="demo" tests="2" failures="1" skipped="0">
  <testcase classname="demo" name="test_basic_001" />
  <testcase classname="demo" name="test_edge_001"><failure>boom</failure></testcase>
</testsuite>
""".strip(),
            encoding="utf-8",
        )
        return _fake_command_result(cwd=context.render_dir, return_code=1, stdout="test_basic_001 ... PASSED\ntest_edge_001 ... FAILED\n")

    monkeypatch.setattr(stage._runners["cocotb_tools"], "execute", fake_execute)
    result = stage.run_from_artifact(
        render_metadata_path=render_path,
        config=SimulationConfig(mode="cocotb_tools", rtl_sources=[_RTL / "simple_comb.v"], junit_enabled=True),
        out_dir=tmp_path / "run_success",
    )

    assert result.selected_mode == "cocotb_tools"
    assert result.passed_tests == ["demo.test_basic_001"]
    assert result.failed_tests == ["demo.test_edge_001"]
    assert result.status == "runtime_error"


def test_timeout_path_preserves_logs_and_sets_timeout_status(tmp_path: Path, monkeypatch) -> None:
    render_path = _build_render_metadata(tmp_path, "simple_comb.v")
    stage = SimulatorRunnerStage()

    def fake_execute(*, metadata, config, selection, context):
        return _fake_command_result(cwd=context.render_dir, timed_out=True, stdout="partial output\n", error_type="timeout")

    monkeypatch.setattr(stage._runners["cocotb_tools"], "execute", fake_execute)
    result = stage.run_from_artifact(
        render_metadata_path=render_path,
        config=SimulationConfig(mode="cocotb_tools", rtl_sources=[_RTL / "simple_comb.v"]),
        out_dir=tmp_path / "run_timeout",
    )

    assert result.status == "timeout"
    assert Path(result.log_paths["stdout"]).exists()
    assert Path(result.log_paths["test_log"]).exists()


def test_stage_run_cli_smoke(tmp_path: Path) -> None:
    render_path = _build_render_metadata(tmp_path, "simple_comb.v")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cocoverify2.cli",
            "stage",
            "run",
            "--render",
            str(render_path),
            "--mode",
            "auto",
            "--rtl",
            str(_RTL / "simple_comb.v"),
            "--out-dir",
            str(tmp_path / "cli_run"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Simulation execution finished" in result.stdout
    assert (tmp_path / "cli_run" / "run" / "simulation_result.json").exists()
