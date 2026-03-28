"""LLM-backed TODO fill stage for rendered cocotb packages."""

from __future__ import annotations

import py_compile
import re
import shutil
from pathlib import Path
from typing import Any

from cocoverify2.core.config import LLMConfig
from cocoverify2.core.errors import ArtifactError, ConfigurationError, StageExecutionError
from cocoverify2.core.models import (
    DUTContract,
    FillBlockResult,
    FillReport,
    LLMTodoBlock,
    OracleCase,
    OracleCheck,
    OracleSpec,
    RenderMetadata,
    SimulationResult,
    TestCasePlan,
    TestPlan,
)
from cocoverify2.core.types import StageName
from cocoverify2.llm.client import LLMClient
from cocoverify2.llm.prompts import build_todo_fill_system_prompt, build_todo_fill_user_prompt
from cocoverify2.llm.validators import parse_todo_fill_response, validate_todo_fill_response
from cocoverify2.stages.simulator_runner import load_render_metadata_artifact
from cocoverify2.stages.tb_renderer import load_contract_artifact, load_oracle_artifact, load_test_plan_artifact
from cocoverify2.utils.files import ensure_dir, read_json, write_json, write_text
from cocoverify2.utils.logging import get_logger

_FILLABLE_KINDS = {"stimulus", "oracle_check"}
_TRACEBACK_PATTERN = re.compile(r'File "([^"]+)", line (\d+)')
_FAILED_TEST_PATTERN = re.compile(r"test_(?P<case_id>[A-Za-z0-9_]+)")


class TodoFillStage:
    """Fill rendered TODO blocks with block-scoped LLM code generation."""

    __test__ = False

    def __init__(self, llm_client: Any | None = None) -> None:
        self.logger = get_logger(__name__)
        self._llm_client = llm_client

    def run_from_artifact(
        self,
        *,
        render_metadata_path: Path,
        out_dir: Path,
        llm_config: LLMConfig,
        task_description: str | None,
        spec_text: str | None,
    ) -> FillReport:
        """Fill render-stage TODO blocks into a runnable cocotb package."""
        metadata = load_render_metadata_artifact(render_metadata_path)
        contract, plan, oracle, resolved_paths = _load_upstream_artifacts(render_metadata_path, metadata)
        fill_dir = ensure_dir(out_dir / "fill")
        package_dir = fill_dir / "cocotb_tests"
        self._copy_render_package(render_metadata_path, package_dir)

        report = FillReport(
            module_name=metadata.module_name,
            based_on_render_metadata=str(render_metadata_path),
            based_on_contract=str(resolved_paths["contract"]),
            based_on_plan=str(resolved_paths["plan"]),
            based_on_oracle=str(resolved_paths["oracle"]),
            package_dir=str(package_dir),
            metadata_path=str(fill_dir / "metadata.json"),
        )

        block_results = self._initial_fill_pass(
            metadata=metadata,
            contract=contract,
            plan=plan,
            oracle=oracle,
            package_dir=package_dir,
            fill_dir=fill_dir,
            llm_config=llm_config,
            task_description=task_description,
            spec_text=spec_text,
        )
        report.block_results = list(block_results.values())
        report.attempted_block_ids = [block.block_id for block in _fillable_blocks(metadata)]

        compile_errors = _compile_package(package_dir)
        repair_targets = set(_failed_block_ids(block_results)) | set(
            _map_compile_errors_to_block_ids(
                compile_errors=compile_errors,
                package_dir=package_dir,
                blocks=_fillable_blocks(metadata),
            )
        )
        if repair_targets:
            self._repair_blocks(
                block_ids=sorted(repair_targets),
                block_results=block_results,
                metadata=metadata,
                contract=contract,
                plan=plan,
                oracle=oracle,
                package_dir=package_dir,
                fill_dir=fill_dir,
                llm_config=llm_config,
                task_description=task_description,
                spec_text=spec_text,
                repair_feedback={"compile_errors": compile_errors},
            )
            compile_errors = _compile_package(package_dir)

        report.block_results = list(block_results.values())
        report.compile_ok = not compile_errors
        for error in compile_errors:
            report.warnings.append(error["message"])

        self._finalize_report(report, metadata=metadata, block_results=block_results)
        fill_metadata = self._build_fill_metadata(
            metadata=metadata,
            report=report,
            package_dir=package_dir,
        )
        write_json(fill_dir / "metadata.json", fill_metadata.model_dump(mode="json"))
        write_json(fill_dir / "fill_report.json", report.model_dump(mode="json"))
        write_json(fill_dir / "repair_report.json", _build_repair_report(report))
        return report

    def repair_from_run_failure(
        self,
        *,
        fill_metadata_path: Path,
        simulation_result_path: Path,
        llm_config: LLMConfig,
        out_dir: Path,
        task_description: str | None,
        spec_text: str | None,
    ) -> FillReport:
        """Attempt one bounded repair pass after simulation failure."""
        metadata = load_render_metadata_artifact(fill_metadata_path)
        report_path = out_dir / "fill" / "fill_report.json"
        if not report_path.exists():
            raise ArtifactError(f"Fill report does not exist: {report_path}")
        report = FillReport.model_validate(read_json(report_path))
        if report.repaired_block_ids:
            report.warnings.append("Simulation-triggered repair was skipped because one repair pass was already used.")
            write_json(report_path, report.model_dump(mode="json"))
            return report

        contract, plan, oracle, _ = _load_upstream_artifacts(fill_metadata_path, metadata)
        simulation_result = SimulationResult.model_validate(read_json(simulation_result_path))
        run_dir = simulation_result_path.parent
        log_text = _read_run_logs(run_dir)
        repair_targets = _repair_targets_from_run_failure(
            metadata=metadata,
            simulation_result=simulation_result,
            log_text=log_text,
            package_dir=fill_metadata_path.parent / "cocotb_tests",
        )
        if not repair_targets:
            report.warnings.append("Simulation-triggered repair found no block-local targets.")
            write_json(report_path, report.model_dump(mode="json"))
            return report

        block_results = {item.block_id: item for item in report.block_results}
        self._repair_blocks(
            block_ids=sorted(repair_targets),
            block_results=block_results,
            metadata=metadata,
            contract=contract,
            plan=plan,
            oracle=oracle,
            package_dir=fill_metadata_path.parent / "cocotb_tests",
            fill_dir=out_dir / "fill",
            llm_config=llm_config,
            task_description=task_description,
            spec_text=spec_text,
            repair_feedback={
                "simulation_status": simulation_result.status,
                "failed_tests": list(simulation_result.failed_tests),
                "log_excerpt": log_text[-4000:],
            },
        )
        compile_errors = _compile_package(fill_metadata_path.parent / "cocotb_tests")
        report.block_results = list(block_results.values())
        report.compile_ok = not compile_errors
        for error in compile_errors:
            report.warnings.append(error["message"])
        self._finalize_report(report, metadata=metadata, block_results=block_results)
        fill_metadata = self._build_fill_metadata(
            metadata=metadata,
            report=report,
            package_dir=fill_metadata_path.parent / "cocotb_tests",
        )
        write_json(fill_metadata_path, fill_metadata.model_dump(mode="json"))
        write_json(report_path, report.model_dump(mode="json"))
        write_json(out_dir / "fill" / "repair_report.json", _build_repair_report(report))
        return report

    def _initial_fill_pass(
        self,
        *,
        metadata: RenderMetadata,
        contract: DUTContract,
        plan: TestPlan,
        oracle: OracleSpec,
        package_dir: Path,
        fill_dir: Path,
        llm_config: LLMConfig,
        task_description: str | None,
        spec_text: str | None,
    ) -> dict[str, FillBlockResult]:
        block_results: dict[str, FillBlockResult] = {}
        for block in _fillable_blocks(metadata):
            block_results[block.block_id] = FillBlockResult(
                block_id=block.block_id,
                fill_kind=block.fill_kind,
                relative_path=block.relative_path,
            )
            self._fill_one_block(
                block=block,
                block_results=block_results,
                contract=contract,
                plan=plan,
                oracle=oracle,
                package_dir=package_dir,
                fill_dir=fill_dir,
                llm_config=llm_config,
                task_description=task_description,
                spec_text=spec_text,
                repair_feedback=None,
            )
        return block_results

    def _repair_blocks(
        self,
        *,
        block_ids: list[str],
        block_results: dict[str, FillBlockResult],
        metadata: RenderMetadata,
        contract: DUTContract,
        plan: TestPlan,
        oracle: OracleSpec,
        package_dir: Path,
        fill_dir: Path,
        llm_config: LLMConfig,
        task_description: str | None,
        spec_text: str | None,
        repair_feedback: dict[str, Any],
    ) -> None:
        block_map = {block.block_id: block for block in _fillable_blocks(metadata)}
        for block_id in block_ids:
            block = block_map.get(block_id)
            if block is None:
                continue
            self._fill_one_block(
                block=block,
                block_results=block_results,
                contract=contract,
                plan=plan,
                oracle=oracle,
                package_dir=package_dir,
                fill_dir=fill_dir,
                llm_config=llm_config,
                task_description=task_description,
                spec_text=spec_text,
                repair_feedback=repair_feedback,
            )

    def _fill_one_block(
        self,
        *,
        block: LLMTodoBlock,
        block_results: dict[str, FillBlockResult],
        contract: DUTContract,
        plan: TestPlan,
        oracle: OracleSpec,
        package_dir: Path,
        fill_dir: Path,
        llm_config: LLMConfig,
        task_description: str | None,
        spec_text: str | None,
        repair_feedback: dict[str, Any] | None,
    ) -> None:
        block_result = block_results[block.block_id]
        target_path = package_dir / Path(block.relative_path).name
        if not target_path.exists():
            block_result.status = "failed"
            block_result.validation_errors.append(f"Target file does not exist for block {block.block_id}: {target_path}")
            return

        plan_case, oracle_case, oracle_check = _resolve_block_dependencies(block, plan, oracle)
        file_context = _extract_file_context(target_path, block)
        helper_contract = _helper_contract_for_block(block.fill_kind)
        system_prompt = build_todo_fill_system_prompt(block.fill_kind)
        user_prompt = build_todo_fill_user_prompt(
            block=block,
            contract=contract,
            task_description=task_description,
            spec_text=spec_text,
            file_context=file_context,
            helper_contract=helper_contract,
            plan_case=plan_case,
            oracle_case=oracle_case,
            oracle_check=oracle_check,
            repair_feedback=repair_feedback,
        )

        attempt_index = int(block_result.attempts) + 1
        request_path = fill_dir / "llm_requests" / f"{block.block_id}.attempt_{attempt_index}.json"
        response_raw_path = fill_dir / "llm_responses" / f"{block.block_id}.attempt_{attempt_index}.raw.txt"
        response_parsed_path = fill_dir / "llm_responses" / f"{block.block_id}.attempt_{attempt_index}.parsed.json"
        write_json(
            request_path,
            {
                "block_id": block.block_id,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
            },
        )
        block_result.request_path = str(request_path)

        try:
            raw_response = self._client(llm_config).complete(system_prompt=system_prompt, user_prompt=user_prompt)
            write_text(response_raw_path, raw_response)
            parsed = parse_todo_fill_response(raw_response)
            validated, validation_report = validate_todo_fill_response(parsed, block=block)
            write_json(response_parsed_path, validated.model_dump(mode="json"))
            updated_text = _replace_todo_block_content(target_path.read_text(encoding="utf-8"), block, validated.code_lines)
            write_text(target_path, updated_text)
            block_result.status = "repaired" if repair_feedback else "filled"
            block_result.attempts = attempt_index
            block_result.response_raw_path = str(response_raw_path)
            block_result.response_parsed_path = str(response_parsed_path)
            block_result.helper_calls = validation_report["used_helper_calls"]
            block_result.assumptions = list(validated.assumptions)
            block_result.unresolved_items = list(validated.unresolved_items)
            block_result.validation_errors = []
            block_result.compile_errors = []
        except Exception as exc:
            block_result.status = "failed"
            block_result.attempts = attempt_index
            block_result.response_raw_path = str(response_raw_path) if response_raw_path.exists() else ""
            block_result.response_parsed_path = str(response_parsed_path) if response_parsed_path.exists() else ""
            block_result.validation_errors.append(str(exc))

    def _build_fill_metadata(
        self,
        *,
        metadata: RenderMetadata,
        report: FillReport,
        package_dir: Path,
    ) -> RenderMetadata:
        block_results = {item.block_id: item for item in report.block_results}
        updated_blocks: list[LLMTodoBlock] = []
        for block in metadata.llm_todo_blocks:
            result = block_results.get(block.block_id)
            if result is None:
                updated_blocks.append(block)
                continue
            updated_blocks.append(
                block.model_copy(
                    update={
                        "fill_status": result.status,
                        "fill_attempts": result.attempts,
                        "fill_errors": [*result.validation_errors, *result.compile_errors],
                    }
                )
            )

        return metadata.model_copy(
            update={
                "artifact_stage": "fill",
                "based_on_render_metadata": report.based_on_render_metadata,
                "generated_files": list(metadata.generated_files),
                "llm_todo_blocks": updated_blocks,
                "filled_todo_block_ids": list(report.filled_block_ids),
                "unfilled_todo_block_ids": list(report.failed_block_ids),
                "fill_status": report.fill_status,
                "fill_warnings": list(report.warnings),
                "render_warnings": [*metadata.render_warnings],
            }
        )

    def _finalize_report(
        self,
        report: FillReport,
        *,
        metadata: RenderMetadata,
        block_results: dict[str, FillBlockResult],
    ) -> None:
        report.filled_block_ids = sorted(
            block_id for block_id, result in block_results.items() if result.status in {"filled", "repaired"}
        )
        report.repaired_block_ids = sorted(
            block_id for block_id, result in block_results.items() if result.status == "repaired"
        )
        report.failed_block_ids = sorted(
            block_id for block_id, result in block_results.items() if result.status != "filled" and result.status != "repaired"
        )
        critical_block_ids = {block.block_id for block in _fillable_blocks(metadata)}
        missing_critical = sorted(critical_block_ids - set(report.filled_block_ids))
        if missing_critical:
            report.warnings.append(f"Critical TODO blocks remain unfilled: {', '.join(missing_critical)}")
        report.fill_status = "success" if report.compile_ok and not missing_critical else "failed"

    def _copy_render_package(self, render_metadata_path: Path, package_dir: Path) -> None:
        render_package_dir = render_metadata_path.parent / "cocotb_tests"
        if not render_package_dir.exists():
            raise ArtifactError(f"Rendered package directory does not exist: {render_package_dir}")
        if package_dir.exists():
            shutil.rmtree(package_dir)
        ensure_dir(package_dir.parent)
        shutil.copytree(render_package_dir, package_dir)

    def _client(self, llm_config: LLMConfig) -> Any:
        if self._llm_client is not None:
            return self._llm_client
        return LLMClient(llm_config)


def _load_upstream_artifacts(
    render_metadata_path: Path,
    metadata: RenderMetadata,
) -> tuple[DUTContract, TestPlan, OracleSpec, dict[str, Path]]:
    root = render_metadata_path.parent.parent
    resolved_paths = {
        "contract": _resolve_artifact_path(metadata.based_on_contract, root / "contract" / "contract.json"),
        "plan": _resolve_artifact_path(metadata.based_on_plan, root / "plan" / "test_plan.json"),
        "oracle": _resolve_artifact_path(metadata.based_on_oracle, root / "oracle" / "oracle.json"),
    }
    return (
        load_contract_artifact(resolved_paths["contract"]),
        load_test_plan_artifact(resolved_paths["plan"]),
        load_oracle_artifact(resolved_paths["oracle"]),
        resolved_paths,
    )


def _resolve_artifact_path(value: str, fallback: Path) -> Path:
    candidate = Path(value) if value else fallback
    if candidate.exists():
        return candidate
    if fallback.exists():
        return fallback
    raise ArtifactError(f"Could not resolve artifact path. Tried {candidate} and {fallback}.")


def _fillable_blocks(metadata: RenderMetadata) -> list[LLMTodoBlock]:
    return [block for block in metadata.llm_todo_blocks if block.fill_kind in _FILLABLE_KINDS]


def _failed_block_ids(block_results: dict[str, FillBlockResult]) -> list[str]:
    return [block_id for block_id, result in block_results.items() if result.status == "failed"]


def _resolve_block_dependencies(
    block: LLMTodoBlock,
    plan: TestPlan,
    oracle: OracleSpec,
) -> tuple[TestCasePlan | None, OracleCase | None, OracleCheck | None]:
    plan_case = next((case for case in plan.cases if case.case_id == block.case_id), None)
    oracle_case = None
    oracle_check = None
    if block.fill_kind == "oracle_check":
        for candidate_case in [*oracle.protocol_oracles, *oracle.functional_oracles, *oracle.property_oracles]:
            if candidate_case.case_id != block.oracle_case_id:
                continue
            oracle_case = candidate_case
            oracle_check = next((check for check in candidate_case.checks if check.check_id == block.check_id), None)
            break
    return plan_case, oracle_case, oracle_check


def _helper_contract_for_block(fill_kind: str) -> dict[str, list[str]]:
    if fill_kind == "stimulus":
        return {
            "methods": [
                "await self.drive_inputs(**signals)",
                "await self.wait_for_settle()",
                "self.record_case_inputs(case_id, signals)",
                "self.record_case_note(case_id, text)",
                "await self.sample_outputs(names=None)",
            ]
        }
    return {
        "methods": [
            "inputs = env.get_case_inputs(plan_case_id)",
            "outputs = await env.sample_outputs(observed_signals)",
            "env.record_case_note(plan_case_id, text)",
            "env.signal_width(signal_name)",
        ],
        "functions": [
            "assert_equal(name, observed, expected)",
            "assert_true(condition, message)",
            "to_uint(value, width)",
            "to_sint(value, width)",
            "mask_width(width)",
            "is_high_impedance(value)",
            "is_unknown(value)",
        ],
    }


def _extract_file_context(path: Path, block: LLMTodoBlock, window: int = 25) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    start = next((index for index, line in enumerate(lines) if line == block.start_marker), None)
    end = next((index for index, line in enumerate(lines) if line == block.end_marker), None)
    if start is None or end is None:
        return path.read_text(encoding="utf-8")
    excerpt = lines[max(0, start - window) : min(len(lines), end + window + 1)]
    return "\n".join(excerpt)


def _replace_todo_block_content(text: str, block: LLMTodoBlock, code_lines: list[str]) -> str:
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if line == block.start_marker), None)
    end = next((index for index, line in enumerate(lines) if line == block.end_marker), None)
    if start is None or end is None or end <= start:
        raise ArtifactError(f"Could not locate TODO markers for block {block.block_id!r}.")
    indent = block.start_marker.split("# TODO", 1)[0]
    replacement = [f"{indent}{line}" if line else indent.rstrip() for line in code_lines]
    updated_lines = [*lines[: start + 1], *replacement, *lines[end:]]
    trailing_newline = "\n" if text.endswith("\n") else ""
    return "\n".join(updated_lines) + trailing_newline


def _compile_package(package_dir: Path) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for path in sorted(package_dir.glob("*.py")):
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            error_value = getattr(exc, "exc_value", None)
            line_number = getattr(error_value, "lineno", None)
            errors.append(
                {
                    "path": str(path),
                    "relative_path": f"cocotb_tests/{path.name}",
                    "line_number": int(line_number) if isinstance(line_number, int) else None,
                    "message": str(error_value or exc),
                }
            )
    return errors


def _map_compile_errors_to_block_ids(
    *,
    compile_errors: list[dict[str, Any]],
    package_dir: Path,
    blocks: list[LLMTodoBlock],
) -> list[str]:
    ranges = _block_line_ranges(package_dir=package_dir, blocks=blocks)
    matched: list[str] = []
    for error in compile_errors:
        relative_path = error["relative_path"]
        line_number = error.get("line_number")
        if not isinstance(line_number, int):
            continue
        for block_id, start, end in ranges.get(relative_path, []):
            if start <= line_number <= end:
                matched.append(block_id)
    return sorted(set(matched))


def _block_line_ranges(package_dir: Path, blocks: list[LLMTodoBlock]) -> dict[str, list[tuple[str, int, int]]]:
    grouped: dict[str, list[tuple[str, int, int]]] = {}
    for block in blocks:
        path = package_dir / Path(block.relative_path).name
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        start = next((index + 1 for index, line in enumerate(lines) if line == block.start_marker), None)
        end = next((index + 1 for index, line in enumerate(lines) if line == block.end_marker), None)
        if start is None or end is None:
            continue
        grouped.setdefault(block.relative_path, []).append((block.block_id, start, end))
    return grouped


def _read_run_logs(run_dir: Path) -> str:
    log_text = []
    for candidate in (
        run_dir / "logs" / "test.log",
        run_dir / "logs" / "stderr.txt",
        run_dir / "logs" / "stdout.txt",
    ):
        if candidate.exists():
            log_text.append(candidate.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(log_text)


def _repair_targets_from_run_failure(
    *,
    metadata: RenderMetadata,
    simulation_result: SimulationResult,
    log_text: str,
    package_dir: Path,
) -> set[str]:
    targets: set[str] = set()
    blocks = _fillable_blocks(metadata)
    ranges = _block_line_ranges(package_dir=package_dir, blocks=blocks)
    for match in _TRACEBACK_PATTERN.finditer(log_text):
        path = Path(match.group(1))
        line_number = int(match.group(2))
        relative_path = f"cocotb_tests/{path.name}"
        for block_id, start, end in ranges.get(relative_path, []):
            if start <= line_number <= end:
                targets.add(block_id)

    failed_case_ids: set[str] = set()
    for test_name in simulation_result.failed_tests:
        match = _FAILED_TEST_PATTERN.search(test_name)
        if match:
            failed_case_ids.add(match.group("case_id"))
    for block in blocks:
        if block.case_id in failed_case_ids:
            targets.add(block.block_id)
    return targets


def _build_repair_report(report: FillReport) -> dict[str, Any]:
    return {
        "module_name": report.module_name,
        "fill_status": report.fill_status,
        "filled_block_ids": list(report.filled_block_ids),
        "repaired_block_ids": list(report.repaired_block_ids),
        "failed_block_ids": list(report.failed_block_ids),
        "warning_count": len(report.warnings),
    }
