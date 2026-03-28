"""Minimal structured triage stage for Phase 6."""

from __future__ import annotations

from pathlib import Path

from cocoverify2.core.errors import ArtifactError
from cocoverify2.core.models import RenderMetadata, RunnerSelection, SimulationResult, TriageResult
from cocoverify2.core.types import ExecutionStatus
from cocoverify2.stages.simulator_runner import load_render_metadata_artifact
from cocoverify2.utils.files import ensure_dir, read_json, read_text, write_json, write_yaml
from cocoverify2.utils.logging import get_logger

_ARTIFACT_CONTRACT_KEYWORDS = (
    "no module named 'cocotb_tests'",
    'no module named "cocotb_tests"',
    "modulenotfounderror: no module named 'cocotb_tests'",
    'modulenotfounderror: no module named "cocotb_tests"',
    "rendered cocotb package is missing",
    "rendered makefile is missing",
    "does not satisfy the executable-shell contract",
    "missing generated helper",
)

_CONFIGURATION_KEYWORDS = (
    "render metadata artifact does not exist",
    "the run stage requires",
    "no rtl sources were resolved",
    "filelist path does not exist",
    "requested filelist mode could not be satisfied",
    "input directory does not exist",
    "simulation result artifact does not exist",
)

_ENVIRONMENT_KEYWORDS = (
    "required tool 'cocotb-config' is unavailable",
    "cocotb-config",
    "command not found",
    "make: not found",
    "permission denied",
    "vvp input file",
    "run time version",
    "simulator unavailable",
    "no module named 'cocotb_tools'",
    'no module named "cocotb_tools"',
)

_COMPILE_KEYWORDS = (
    "syntax error",
    "compile error",
    "parser error",
    "lexical error",
)

_ELABORATION_KEYWORDS = (
    "elaboration",
    "unable to bind",
    "unresolved module",
    "cannot find top module",
    "can't resolve",
)

_TIMEOUT_KEYWORDS = (
    "timed out",
    "timeout",
)

_ORACLE_TRACE_KEYWORDS = (
    "_oracle.py",
    "oracle check",
    "oracle helper",
)

_WEAK_RENDER_HINTS = (
    "conservative",
    "limited",
    "low",
    "empty",
)

_UNRESOLVED_HINTS = (
    "unresolved",
    "ambigu",
    "unknown",
)


class TriageStage:
    """Consume Phase 5 artifacts and emit a conservative triage artifact."""

    __test__ = False

    def __init__(self) -> None:
        """Initialize the stage with a stage-scoped logger."""
        self.logger = get_logger(__name__)

    def run_from_dir(self, *, in_dir: Path, out_dir: Path) -> TriageResult:
        """Resolve run artifacts from a phase root or run directory and triage them."""
        run_dir = _resolve_run_dir(in_dir)
        simulation_result_path = run_dir / "simulation_result.json"
        runner_selection_path = run_dir / "runner_selection.json"
        copied_render_metadata_path = run_dir / "copied_or_linked_render_metadata.json"

        simulation_result = load_simulation_result_artifact(simulation_result_path)
        runner_selection = load_runner_selection_artifact(runner_selection_path) if runner_selection_path.exists() else None
        render_metadata_path = _resolve_render_metadata_path(
            run_dir=run_dir,
            simulation_result=simulation_result,
            runner_selection=runner_selection,
            copied_render_metadata_path=copied_render_metadata_path,
        )
        render_metadata = load_render_metadata_artifact(render_metadata_path) if render_metadata_path else None
        logs = _load_log_texts(run_dir=run_dir, simulation_result=simulation_result)
        triage = self.run(
            simulation_result=simulation_result,
            simulation_result_path=simulation_result_path,
            runner_selection=runner_selection,
            runner_selection_path=runner_selection_path if runner_selection_path.exists() else None,
            render_metadata=render_metadata,
            render_metadata_path=render_metadata_path,
            logs=logs,
            out_dir=out_dir,
        )
        self.logger.info(
            "Completed triage for module '%s' with category=%s",
            triage.module_name or "<unknown>",
            triage.primary_category,
        )
        return triage

    def run(
        self,
        *,
        simulation_result: SimulationResult,
        simulation_result_path: Path,
        runner_selection: RunnerSelection | None,
        runner_selection_path: Path | None,
        render_metadata: RenderMetadata | None,
        render_metadata_path: Path | None,
        logs: dict[str, str],
        out_dir: Path,
    ) -> TriageResult:
        """Classify a loaded Phase 5 result and persist triage artifacts."""
        triage = _classify(
            simulation_result=simulation_result,
            simulation_result_path=simulation_result_path,
            runner_selection=runner_selection,
            runner_selection_path=runner_selection_path,
            render_metadata=render_metadata,
            render_metadata_path=render_metadata_path,
            logs=logs,
        )
        triage_dir = ensure_dir(out_dir / "triage")
        write_json(triage_dir / "triage.json", triage.model_dump(mode="json"))
        write_yaml(triage_dir / "triage_summary.yaml", _build_triage_summary(triage))
        return triage


def load_simulation_result_artifact(path: Path) -> SimulationResult:
    """Load a ``SimulationResult`` artifact from JSON."""
    if not path.exists():
        raise ArtifactError(f"Simulation result artifact does not exist: {path}")
    return SimulationResult.model_validate(read_json(path))


def load_runner_selection_artifact(path: Path) -> RunnerSelection:
    """Load a ``RunnerSelection`` artifact from JSON."""
    if not path.exists():
        raise ArtifactError(f"Runner selection artifact does not exist: {path}")
    return RunnerSelection.model_validate(read_json(path))


def _resolve_run_dir(in_dir: Path) -> Path:
    if not in_dir.exists():
        raise ArtifactError(f"Triage input directory does not exist: {in_dir}")
    if (in_dir / "simulation_result.json").exists():
        return in_dir
    nested_run_dir = in_dir / "run"
    if (nested_run_dir / "simulation_result.json").exists():
        return nested_run_dir
    raise ArtifactError(
        "Triage could not locate simulation_result.json. Expected either <in-dir>/simulation_result.json "
        "or <in-dir>/run/simulation_result.json."
    )


def _resolve_render_metadata_path(
    *,
    run_dir: Path,
    simulation_result: SimulationResult,
    runner_selection: RunnerSelection | None,
    copied_render_metadata_path: Path,
) -> Path | None:
    raw_candidates = []
    if runner_selection and runner_selection.render_metadata_path:
        raw_candidates.append(runner_selection.render_metadata_path)
    if simulation_result.based_on_render_metadata:
        raw_candidates.append(simulation_result.based_on_render_metadata)

    for raw_candidate in raw_candidates:
        candidate = Path(raw_candidate)
        if candidate.exists():
            return candidate
    if copied_render_metadata_path.exists():
        return copied_render_metadata_path
    return None


def _load_log_texts(*, run_dir: Path, simulation_result: SimulationResult) -> dict[str, str]:
    texts: dict[str, str] = {}
    for key in ("build_log", "test_log", "stdout", "stderr"):
        raw_path = simulation_result.log_paths.get(key, "")
        path = _resolve_log_path(raw_path=raw_path, run_dir=run_dir)
        texts[key] = read_text(path) if path else ""
    return texts


def _resolve_log_path(*, raw_path: str, run_dir: Path) -> Path | None:
    if not raw_path:
        return None
    candidate = Path(raw_path)
    if candidate.exists():
        return candidate
    fallback = run_dir / "logs" / candidate.name
    if fallback.exists():
        return fallback
    return None


def _classify(
    *,
    simulation_result: SimulationResult,
    simulation_result_path: Path,
    runner_selection: RunnerSelection | None,
    runner_selection_path: Path | None,
    render_metadata: RenderMetadata | None,
    render_metadata_path: Path | None,
    logs: dict[str, str],
) -> TriageResult:
    status = _value(simulation_result.status)
    all_fragments = _search_fragments(simulation_result=simulation_result, runner_selection=runner_selection, render_metadata=render_metadata, logs=logs)
    build_and_test_lines = [
        *[line for line in logs.get("build_log", "").splitlines() if line.strip()],
        *[line for line in logs.get("test_log", "").splitlines() if line.strip()],
        *[line for line in logs.get("stderr", "").splitlines() if line.strip()],
        *[line for line in logs.get("stdout", "").splitlines() if line.strip()],
    ]

    configuration_matches = _find_matches(all_fragments, _CONFIGURATION_KEYWORDS)
    artifact_matches = _find_matches(all_fragments, _ARTIFACT_CONTRACT_KEYWORDS)
    environment_matches = _find_matches(all_fragments, _ENVIRONMENT_KEYWORDS)
    compile_matches = _find_matches(all_fragments, _COMPILE_KEYWORDS)
    elaboration_matches = _find_matches(all_fragments, _ELABORATION_KEYWORDS)
    timeout_matches = _find_matches(all_fragments, _TIMEOUT_KEYWORDS)
    pass_matches = _find_matches(build_and_test_lines, (" passed", " PASS "))
    oracle_matches = _find_matches(all_fragments, _ORACLE_TRACE_KEYWORDS)

    secondary_categories: list[str] = []
    if status == ExecutionStatus.SUCCESS.value:
        primary_category = "no_failure"
        suspected_layer = "none"
        confidence = 0.92
        matched_log_fragments = pass_matches
    elif configuration_matches:
        primary_category = "configuration_error"
        suspected_layer = "execution_config"
        confidence = 0.82
        secondary_categories = ["execution_infrastructure_error"]
        matched_log_fragments = configuration_matches
    elif artifact_matches:
        primary_category = "artifact_contract_error"
        suspected_layer = "render_run_contract"
        confidence = 0.86
        secondary_categories = ["execution_infrastructure_error"]
        matched_log_fragments = artifact_matches
    elif status == ExecutionStatus.TIMEOUT.value:
        primary_category = "timeout_error"
        suspected_layer = "execution"
        confidence = 0.9
        matched_log_fragments = timeout_matches
    elif status == ExecutionStatus.COMPILE_ERROR.value:
        primary_category = "compile_error"
        suspected_layer = "rtl_build"
        confidence = 0.9
        matched_log_fragments = compile_matches
    elif status == ExecutionStatus.ELABORATION_ERROR.value:
        primary_category = "elaboration_error"
        suspected_layer = "rtl_integration"
        confidence = 0.9
        matched_log_fragments = elaboration_matches
    elif environment_matches or status == ExecutionStatus.ENVIRONMENT_ERROR.value:
        primary_category = "environment_error"
        suspected_layer = "environment"
        confidence = 0.82 if environment_matches else 0.68
        secondary_categories = ["execution_infrastructure_error"]
        matched_log_fragments = environment_matches
    elif status == ExecutionStatus.RUNTIME_ERROR.value and simulation_result.failed_tests:
        primary_category = "runtime_test_failure"
        suspected_layer = "dut_or_testbench"
        confidence = 0.72
        if _render_looks_weak(render_metadata):
            secondary_categories.append("weak_testbench")
        if _render_looks_unresolved(render_metadata):
            secondary_categories.append("unresolved_ambiguity")
        if oracle_matches:
            secondary_categories.append("oracle_error")
        if not any(item in secondary_categories for item in ("weak_testbench", "unresolved_ambiguity", "oracle_error")):
            secondary_categories.append("likely_dut_bug")
        matched_log_fragments = _find_matches(build_and_test_lines, (" failed", " FAILED", " failure", "AssertionError"))
    else:
        primary_category = "unknown_failure"
        suspected_layer = "unknown"
        confidence = 0.35
        matched_log_fragments = configuration_matches or artifact_matches or environment_matches or compile_matches or elaboration_matches or timeout_matches

    evidence = _build_evidence(
        simulation_result=simulation_result,
        status=status,
        runner_selection=runner_selection,
        render_metadata=render_metadata,
    )
    return TriageResult(
        module_name=simulation_result.module_name,
        based_on_simulation_result=str(simulation_result_path),
        based_on_runner_selection=str(runner_selection_path) if runner_selection_path else None,
        based_on_render_metadata=str(render_metadata_path) if render_metadata_path else None,
        source_status=status,
        primary_category=primary_category,
        secondary_categories=_dedupe_preserve_order(secondary_categories),
        evidence=evidence,
        matched_signals=[],
        matched_log_fragments=_dedupe_preserve_order(matched_log_fragments)[:3],
        confidence=confidence,
        suspected_layer=suspected_layer,
    )


def _build_evidence(
    *,
    simulation_result: SimulationResult,
    status: str,
    runner_selection: RunnerSelection | None,
    render_metadata: RenderMetadata | None,
) -> list[str]:
    evidence = [
        f"simulation_status={status}",
        f"module_name={simulation_result.module_name or '<unknown>'}",
        f"failed_tests_count={len(simulation_result.failed_tests)}",
        f"passed_tests_count={len(simulation_result.passed_tests)}",
        f"discovered_tests_count={len(simulation_result.discovered_tests)}",
    ]
    if simulation_result.return_code is not None:
        evidence.append(f"return_code={simulation_result.return_code}")
    if runner_selection is not None:
        evidence.append(f"runner_backend={runner_selection.backend}")
        evidence.append(f"runner_selected_mode={_value(runner_selection.selected_mode)}")
        evidence.append(f"runner_warning_count={len(runner_selection.warnings)}")
    else:
        evidence.append(f"runner_backend={_value(simulation_result.selected_mode)}")
    if render_metadata is not None:
        evidence.append(f"render_warning_count={len(render_metadata.render_warnings)}")
        evidence.append(f"render_confidence={render_metadata.render_confidence:.2f}")
    return evidence


def _render_looks_weak(render_metadata: RenderMetadata | None) -> bool:
    if render_metadata is None:
        return False
    if render_metadata.render_confidence < 0.6:
        return True
    warnings = "\n".join(render_metadata.render_warnings).lower()
    if any(keyword in warnings for keyword in _WEAK_RENDER_HINTS):
        return True
    oracle_summary = render_metadata.oracle_summary
    return bool(oracle_summary.get("empty_functional_cases"))


def _render_looks_unresolved(render_metadata: RenderMetadata | None) -> bool:
    if render_metadata is None:
        return False
    warnings = "\n".join(render_metadata.render_warnings).lower()
    return any(keyword in warnings for keyword in _UNRESOLVED_HINTS)


def _search_fragments(
    *,
    simulation_result: SimulationResult,
    runner_selection: RunnerSelection | None,
    render_metadata: RenderMetadata | None,
    logs: dict[str, str],
) -> list[str]:
    fragments: list[str] = []
    for text in logs.values():
        fragments.extend(line.strip() for line in text.splitlines() if line.strip())
    fragments.extend(simulation_result.execution_notes)
    fragments.extend(simulation_result.runner_warnings)
    if runner_selection is not None:
        fragments.extend(runner_selection.reasons)
        fragments.extend(runner_selection.warnings)
        fragments.extend(runner_selection.fallbacks)
    if render_metadata is not None:
        fragments.extend(render_metadata.render_warnings)
    return fragments


def _find_matches(lines: list[str], keywords: tuple[str, ...]) -> list[str]:
    matches: list[str] = []
    lowered_keywords = tuple(keyword.lower() for keyword in keywords)
    for line in lines:
        lowered = line.lower()
        if any(keyword in lowered for keyword in lowered_keywords):
            matches.append(line)
    return _dedupe_preserve_order(matches)[:3]


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        unique.append(item)
    return unique


def _value(value: object) -> str:
    return value.value if hasattr(value, "value") else str(value)


def _build_triage_summary(result: TriageResult) -> dict[str, object]:
    return {
        "module_name": result.module_name,
        "primary_category": result.primary_category,
        "secondary_categories": result.secondary_categories,
        "suspected_layer": result.suspected_layer,
        "confidence": result.confidence,
        "source_status": result.source_status,
        "evidence": result.evidence,
        "matched_log_fragments": result.matched_log_fragments,
        "based_on_simulation_result": result.based_on_simulation_result,
        "based_on_runner_selection": result.based_on_runner_selection,
        "based_on_render_metadata": result.based_on_render_metadata,
    }
