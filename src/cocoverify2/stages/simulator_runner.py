"""Structured simulation execution stage for Phase 5."""

from __future__ import annotations

from pathlib import Path

from cocoverify2.cocotbgen.makefile import MAKEFILE_CONTRACT_MARKER
from cocoverify2.core.models import RenderMetadata, RunnerSelection, SimulationConfig, SimulationResult
from cocoverify2.core.types import SimulationMode
from cocoverify2.execution.cocotb_runner import CocotbRunner
from cocoverify2.execution.make_runner import MakeRunner
from cocoverify2.execution.result_parser import build_simulation_result
from cocoverify2.execution.runner_base import RunnerContext
from cocoverify2.utils.files import ensure_dir, read_json, write_json, write_text, write_yaml
from cocoverify2.utils.logging import get_logger
from cocoverify2.utils.subprocess import CommandExecutionResult


class SimulatorRunnerStage:
    """Execute rendered cocotb packages and persist structured run artifacts."""

    __test__ = False

    def __init__(self) -> None:
        """Initialize the stage with concrete backend implementations."""
        self.logger = get_logger(__name__)
        self._runners = {
            "make": MakeRunner(),
            "cocotb_tools": CocotbRunner(),
        }

    def run_from_artifact(
        self,
        *,
        render_metadata_path: Path,
        config: SimulationConfig,
        out_dir: Path,
    ) -> SimulationResult:
        """Load render metadata, choose a runner, and execute the simulation stage."""
        run_dir = ensure_dir(out_dir / "run")
        logs_dir = ensure_dir(run_dir / "logs")
        junit_dir = ensure_dir(run_dir / "junit") if config.junit_enabled else run_dir / "junit"
        waves_dir = ensure_dir(run_dir / "waves") if config.waves_enabled or config.waves else run_dir / "waves"
        package_dir = render_metadata_path.parent / "cocotb_tests"
        render_dir = render_metadata_path.parent
        context = RunnerContext(
            render_metadata_path=render_metadata_path,
            render_dir=render_dir,
            package_dir=package_dir,
            run_dir=run_dir,
            logs_dir=logs_dir,
            junit_dir=junit_dir,
            waves_dir=waves_dir,
        )

        try:
            metadata = load_render_metadata_artifact(render_metadata_path)
        except Exception as exc:  # keep Phase 5 artifact-oriented even on missing metadata
            selection = RunnerSelection(
                requested_mode=config.mode,
                selected_mode=config.mode,
                backend="unavailable",
                render_metadata_path=str(render_metadata_path),
                package_dir=str(package_dir),
                reasons=["Render metadata could not be loaded."],
                warnings=[str(exc)],
                confidence=0.0,
            )
            write_json(run_dir / "runner_selection.json", selection.model_dump(mode="json"))
            command_result = CommandExecutionResult(
                command=[],
                cwd=str(run_dir),
                return_code=None,
                error_type="configuration",
                error_message=str(exc),
                stderr=str(exc),
            )
            log_paths = self._write_logs(command_result=command_result, logs_dir=logs_dir)
            result = build_simulation_result(
                module_name="",
                based_on_render_metadata=str(render_metadata_path),
                selected_mode=selection.selected_mode,
                selected_simulator=config.simulator,
                command_result=command_result,
                log_paths=log_paths,
                junit_path=None,
                waveform_paths=[],
                runner_warnings=selection.warnings,
                execution_notes=["Simulation stage could not load render metadata and therefore did not execute a runner."],
            )
            self._write_result_artifacts(result=result, selection=selection, run_dir=run_dir)
            return result

        write_json(run_dir / "copied_or_linked_render_metadata.json", metadata.model_dump(mode="json"))
        selection, resolved_config = self._select_runner(metadata=metadata, render_metadata_path=render_metadata_path, config=config)
        write_json(run_dir / "runner_selection.json", selection.model_dump(mode="json"))

        if not package_dir.exists():
            command_result = CommandExecutionResult(
                command=[],
                cwd=str(run_dir),
                return_code=None,
                error_type="configuration",
                error_message=f"Rendered cocotb package is missing: {package_dir}",
                stderr=f"Rendered cocotb package is missing: {package_dir}",
            )
            log_paths = self._write_logs(command_result=command_result, logs_dir=logs_dir)
            result = build_simulation_result(
                module_name=metadata.module_name,
                based_on_render_metadata=str(render_metadata_path),
                selected_mode=selection.selected_mode,
                selected_simulator=resolved_config.simulator,
                command_result=command_result,
                log_paths=log_paths,
                junit_path=None,
                waveform_paths=[],
                runner_warnings=selection.warnings,
                execution_notes=["Render metadata loaded, but the expected cocotb_tests package directory was missing."],
            )
            self._write_result_artifacts(result=result, selection=selection, run_dir=run_dir)
            return result

        runner = self._runners[selection.backend]
        command_result = runner.execute(metadata=metadata, config=resolved_config, selection=selection, context=context)
        log_paths = self._write_logs(command_result=command_result, logs_dir=logs_dir)
        junit_path = junit_dir / "results.xml" if resolved_config.junit_enabled else None
        waveform_paths = list(waves_dir.glob("**/*")) if waves_dir.exists() else []
        execution_notes = _build_execution_notes(config=resolved_config, selection=selection)
        result = build_simulation_result(
            module_name=metadata.module_name,
            based_on_render_metadata=str(render_metadata_path),
            selected_mode=selection.selected_mode,
            selected_simulator=resolved_config.simulator,
            command_result=command_result,
            log_paths=log_paths,
            junit_path=junit_path,
            waveform_paths=waveform_paths,
            runner_warnings=selection.warnings,
            execution_notes=execution_notes,
        )
        self._write_result_artifacts(result=result, selection=selection, run_dir=run_dir)
        self.logger.info(
            "Simulation execution finished for module '%s' with status=%s via mode=%s",
            metadata.module_name,
            result.status,
            result.selected_mode,
        )
        return result

    def _select_runner(
        self,
        *,
        metadata: RenderMetadata,
        render_metadata_path: Path,
        config: SimulationConfig,
    ) -> tuple[RunnerSelection, SimulationConfig]:
        requested_mode = config.mode
        package_dir = render_metadata_path.parent / "cocotb_tests"
        makefile_path = package_dir / "Makefile"
        makefile_is_executable = makefile_path.exists() and _makefile_supports_execution_contract(makefile_path)
        resolved_rtl_sources = [str(path) for path in config.rtl_sources]
        include_dirs = list(config.include_dirs)
        warnings: list[str] = []
        reasons: list[str] = []
        fallbacks: list[str] = []

        if config.filelist_path is not None:
            parsed_sources, parsed_include_dirs, parse_warnings = _parse_filelist(config.filelist_path)
            warnings.extend(parse_warnings)
            if not resolved_rtl_sources:
                resolved_rtl_sources.extend(parsed_sources)
            else:
                resolved_rtl_sources.extend([path for path in parsed_sources if path not in resolved_rtl_sources])
            include_dirs.extend(path for path in parsed_include_dirs if path not in include_dirs)

        if requested_mode == SimulationMode.AUTO:
            if makefile_is_executable:
                selected_mode = SimulationMode.MAKE
                backend = "make"
                reasons.append("Auto mode prefers Makefile execution when a rendered Makefile satisfies the executable-shell contract.")
            elif config.filelist_path is not None:
                selected_mode = SimulationMode.FILELIST
                backend = "cocotb_tools"
                reasons.append("Auto mode selected filelist execution because a filelist was provided and no executable-shell Makefile was available.")
            else:
                selected_mode = SimulationMode.COCOTB_TOOLS
                backend = "cocotb_tools"
                reasons.append("Auto mode selected cocotb-tools execution because no higher-priority executable Makefile or filelist prerequisites were available.")
        elif requested_mode == SimulationMode.MAKE:
            if makefile_is_executable:
                selected_mode = SimulationMode.MAKE
                backend = "make"
                reasons.append("Make mode was explicitly requested and the rendered Makefile satisfies the executable-shell contract.")
            else:
                selected_mode = SimulationMode.COCOTB_TOOLS
                backend = "cocotb_tools"
                reasons.append("Make mode was requested, but the rendered Makefile is missing or does not satisfy the executable-shell contract.")
                warnings.append("Requested make mode could not be satisfied; falling back to cocotb-tools execution.")
                fallbacks.append("make -> cocotb_tools")
        elif requested_mode == SimulationMode.FILELIST:
            if config.filelist_path is not None:
                selected_mode = SimulationMode.FILELIST
                backend = "cocotb_tools"
                reasons.append("Filelist mode was explicitly requested and a filelist path is available.")
            elif makefile_is_executable:
                selected_mode = SimulationMode.MAKE
                backend = "make"
                reasons.append("Filelist mode was requested, but no filelist path was provided.")
                warnings.append("Requested filelist mode could not be satisfied; falling back to make mode because a rendered Makefile satisfies the executable-shell contract.")
                fallbacks.append("filelist -> make")
            else:
                selected_mode = SimulationMode.COCOTB_TOOLS
                backend = "cocotb_tools"
                reasons.append("Filelist mode was requested, but no filelist path was provided.")
                warnings.append("Requested filelist mode could not be satisfied; falling back to cocotb-tools execution.")
                fallbacks.append("filelist -> cocotb_tools")
        else:
            selected_mode = SimulationMode.COCOTB_TOOLS
            backend = "cocotb_tools"
            reasons.append("cocotb-tools mode was explicitly requested.")

        if not resolved_rtl_sources:
            warnings.append("No RTL sources were resolved from CLI arguments or filelist input; runner execution may end as an environment/configuration error.")
        if not metadata.test_modules:
            warnings.append("Render metadata does not list any test modules; execution will rely on the default basic test module name.")
        if config.timescale:
            warnings.append("Timescale overrides are recorded in the config but are not yet propagated into backend-specific build flags.")
        if makefile_path.exists() and not makefile_is_executable:
            warnings.append("Rendered Makefile exists but does not satisfy the executable-shell contract; make mode will not be preferred.")
        if selected_mode == SimulationMode.MAKE and not makefile_is_executable:
            warnings.append("Selected make mode without an executable-shell Makefile contract; execution is unlikely to succeed.")

        resolved_config = config.model_copy(
            update={
                "rtl_sources": [Path(path) for path in resolved_rtl_sources],
                "include_dirs": include_dirs,
            }
        )
        selection = RunnerSelection(
            requested_mode=requested_mode,
            selected_mode=selected_mode,
            backend=backend,
            render_metadata_path=str(render_metadata_path),
            package_dir=str(package_dir),
            makefile_path=str(makefile_path) if makefile_path.exists() else None,
            filelist_path=str(config.filelist_path) if config.filelist_path else None,
            resolved_rtl_sources=list(resolved_rtl_sources),
            reasons=reasons,
            warnings=warnings,
            fallbacks=fallbacks,
            confidence=_selection_confidence(warnings=warnings, fallbacks=fallbacks, selected_mode=selected_mode),
        )
        return selection, resolved_config

    def _write_logs(self, *, command_result: CommandExecutionResult, logs_dir: Path) -> dict[str, str]:
        stdout_path = logs_dir / "stdout.txt"
        stderr_path = logs_dir / "stderr.txt"
        build_log_path = logs_dir / "build.log"
        test_log_path = logs_dir / "test.log"
        combined = "\n".join(part for part in [command_result.stdout, command_result.stderr] if part)
        write_text(stdout_path, command_result.stdout)
        write_text(stderr_path, command_result.stderr)
        write_text(build_log_path, combined)
        write_text(test_log_path, combined)
        return {
            "stdout": str(stdout_path),
            "stderr": str(stderr_path),
            "build_log": str(build_log_path),
            "test_log": str(test_log_path),
        }

    def _write_result_artifacts(self, *, result: SimulationResult, selection: RunnerSelection, run_dir: Path) -> None:
        write_json(run_dir / "simulation_result.json", result.model_dump(mode="json"))
        write_yaml(run_dir / "simulation_summary.yaml", _build_result_summary(result))
        write_json(run_dir / "runner_selection.json", selection.model_dump(mode="json"))


def load_render_metadata_artifact(path: Path) -> RenderMetadata:
    """Load a render metadata artifact from JSON."""
    if not path.exists():
        raise FileNotFoundError(f"Render metadata artifact does not exist: {path}")
    return RenderMetadata.model_validate(read_json(path))



def _parse_filelist(path: Path) -> tuple[list[str], list[Path], list[str]]:
    sources: list[str] = []
    include_dirs: list[Path] = []
    warnings: list[str] = []
    if not path.exists():
        warnings.append(f"Filelist path does not exist: {path}")
        return sources, include_dirs, warnings
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("+incdir+"):
            for item in line.split("+")[2:]:
                if item:
                    include_dirs.append((path.parent / item).resolve())
            continue
        if line.startswith("-f") or line.startswith("-F"):
            warnings.append(f"Nested filelist directive is not expanded in Phase 5 MVP: {line}")
            continue
        source_path = Path(line)
        if not source_path.is_absolute():
            source_path = (path.parent / source_path).resolve()
        sources.append(str(source_path))
    return _deduped(sources), _deduped_paths(include_dirs), warnings


def _makefile_supports_execution_contract(path: Path) -> bool:
    text = path.read_text(encoding="utf-8")
    return MAKEFILE_CONTRACT_MARKER in text and ".DEFAULT_GOAL := sim" in text and "Makefile.sim" in text



def _selection_confidence(*, warnings: list[str], fallbacks: list[str], selected_mode: SimulationMode) -> float:
    base = 0.9 if selected_mode != SimulationMode.AUTO else 0.8
    penalty = min(0.45, 0.06 * len(warnings) + 0.12 * len(fallbacks))
    return max(0.05, min(base - penalty, 0.95))



def _build_execution_notes(config: SimulationConfig, selection: RunnerSelection) -> list[str]:
    notes = [
        "Simulation stage consumes render metadata and package artifacts without modifying rendered test semantics.",
        f"Selected backend '{selection.backend}' for mode '{selection.selected_mode}'.",
    ]
    if config.filelist_path:
        notes.append("Filelist input was parsed conservatively; nested filelist directives remain partial-support in this MVP.")
    if config.waves_enabled or config.waves:
        notes.append("Wave dumping was requested; waveform paths are reported only if the backend emitted files.")
    return notes



def _build_result_summary(result: SimulationResult) -> dict[str, object]:
    return {
        "module_name": result.module_name,
        "status": result.status,
        "selected_mode": result.selected_mode,
        "selected_simulator": result.selected_simulator,
        "return_code": result.return_code,
        "duration_seconds": result.duration_seconds,
        "discovered_test_count": len(result.discovered_tests),
        "passed_test_count": len(result.passed_tests),
        "failed_test_count": len(result.failed_tests),
        "skipped_test_count": len(result.skipped_tests),
        "runner_warning_count": len(result.runner_warnings),
    }



def _deduped(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items



def _deduped_paths(items: list[Path]) -> list[Path]:
    unique = []
    seen: set[str] = set()
    for item in items:
        key = str(item)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
