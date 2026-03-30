"""Batch evaluator for the RTLLM benchmark using the mainline cocoverify2 pipeline."""

from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
import csv
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

from cocoverify2.core.config import LLMConfig
from cocoverify2.core.models import OracleSpec, RenderMetadata, SimulationConfig, SimulationResult, TestPlan, TriageResult
from cocoverify2.core.types import GenerationMode, SimulationMode
from cocoverify2.llm.client import LLMClient
from cocoverify2.stages.contract_extractor import ContractExtractor
from cocoverify2.stages.oracle_generator import OracleGenerator
from cocoverify2.stages.simulator_runner import SimulatorRunnerStage
from cocoverify2.stages.tb_renderer import TBRenderer
from cocoverify2.stages.test_plan_generator import TestPlanGenerator
from cocoverify2.stages.triage import TriageStage
from cocoverify2.utils.files import ensure_dir, write_json, write_text
from cocoverify2.utils.logging import get_logger
from cocoverify2.utils.spec_hints import extract_interface_hint_text


LOGGER = get_logger(__name__)
DEFAULT_RTLLM_ROOT = Path(
    "/workspace/I/qimeng6/wangchuanhao/QiMeng-Agent/VerilogBenchmark/Benchmarks/RTLLM_for_ivl"
)
DEFAULT_OUT_DIR = Path("tmp/rtllm_batch")
DISALLOWED_GENERATION_INPUT_NAMES = {"reference.dat", "reference.txt", "testbench.v", "testbench.sv"}


@dataclass(slots=True)
class RTLLMTaskInput:
    """Resolved benchmark inputs for one RTLLM task directory."""

    task_name: str
    task_dir: Path
    rtl_sources: list[Path]
    spec_path: Path | None
    makefile_path: Path | None
    makefile_source_discovery_used: bool = False
    ignored_generation_inputs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RTLLMModuleRunResult:
    """Recorded outcome for one rendered cocotb test module."""

    test_module: str
    run_status: str
    triage_category: str
    passed_tests_count: int
    failed_tests_count: int
    return_code: int | None
    run_dir: str
    triage_dir: str
    passed_tests: list[str] = field(default_factory=list)
    failed_tests: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RTLLMTaskSummary:
    """Per-task batch summary."""

    task_name: str
    module_name: str = ""
    task_dir: str = ""
    artifact_root: str = ""
    rtl_sources: list[str] = field(default_factory=list)
    spec_present: bool = False
    makefile_source_discovery_used: bool = False
    ignored_generation_inputs: list[str] = field(default_factory=list)
    plan_generation_mode: str = GenerationMode.HYBRID.value
    oracle_generation_mode: str = GenerationMode.HYBRID.value
    llm_plan_attempted: bool = False
    llm_plan_succeeded: bool = False
    llm_plan_fallback_used: bool = False
    llm_plan_status: str = "not_attempted"
    llm_plan_reason: str = ""
    llm_oracle_attempted: bool = False
    llm_oracle_succeeded: bool = False
    llm_oracle_fallback_used: bool = False
    llm_oracle_status: str = "not_attempted"
    llm_oracle_reason: str = ""
    contract_success: bool = False
    plan_success: bool = False
    oracle_success: bool = False
    render_success: bool = False
    rendered_test_modules: list[str] = field(default_factory=list)
    test_module_results: list[RTLLMModuleRunResult] = field(default_factory=list)
    assertion_strength_counts: dict[str, int] = field(
        default_factory=lambda: {"exact": 0, "guarded": 0, "unresolved": 0}
    )
    resumed_from_cache: bool = False
    task_status: str = "failed"
    failure_reason_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_name": self.task_name,
            "module_name": self.module_name,
            "task_dir": self.task_dir,
            "artifact_root": self.artifact_root,
            "rtl_sources": list(self.rtl_sources),
            "spec_present": self.spec_present,
            "makefile_source_discovery_used": self.makefile_source_discovery_used,
            "ignored_generation_inputs": list(self.ignored_generation_inputs),
            "plan_generation_mode": self.plan_generation_mode,
            "oracle_generation_mode": self.oracle_generation_mode,
            "llm_plan_attempted": self.llm_plan_attempted,
            "llm_plan_succeeded": self.llm_plan_succeeded,
            "llm_plan_fallback_used": self.llm_plan_fallback_used,
            "llm_plan_status": self.llm_plan_status,
            "llm_plan_reason": self.llm_plan_reason,
            "llm_oracle_attempted": self.llm_oracle_attempted,
            "llm_oracle_succeeded": self.llm_oracle_succeeded,
            "llm_oracle_fallback_used": self.llm_oracle_fallback_used,
            "llm_oracle_status": self.llm_oracle_status,
            "llm_oracle_reason": self.llm_oracle_reason,
            "contract_success": self.contract_success,
            "plan_success": self.plan_success,
            "oracle_success": self.oracle_success,
            "render_success": self.render_success,
            "rendered_test_modules": list(self.rendered_test_modules),
            "test_module_results": [
                {
                    "test_module": item.test_module,
                    "run_status": item.run_status,
                    "triage_category": item.triage_category,
                    "passed_tests_count": item.passed_tests_count,
                    "failed_tests_count": item.failed_tests_count,
                    "return_code": item.return_code,
                    "run_dir": item.run_dir,
                    "triage_dir": item.triage_dir,
                    "passed_tests": list(item.passed_tests),
                    "failed_tests": list(item.failed_tests),
                }
                for item in self.test_module_results
            ],
            "assertion_strength_counts": dict(self.assertion_strength_counts),
            "resumed_from_cache": self.resumed_from_cache,
            "task_status": self.task_status,
            "failure_reason_summary": self.failure_reason_summary,
        }


@dataclass(slots=True)
class RTLLMBatchConfig:
    """Configuration for an RTLLM batch run."""

    benchmark_root: Path
    out_dir: Path = DEFAULT_OUT_DIR
    generation_mode: GenerationMode = GenerationMode.HYBRID
    simulator: str = "icarus"
    simulation_mode: SimulationMode = SimulationMode.AUTO
    timeout_seconds: int = 60
    clean_build: bool = True
    junit_enabled: bool = True
    waves_enabled: bool = False
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    task_names: list[str] = field(default_factory=list)
    limit: int | None = None
    jobs: int = 1
    resume: bool = False


def discover_rtllm_tasks(root: Path) -> list[Path]:
    """Return all immediate task directories under the RTLLM benchmark root."""
    if not root.exists():
        raise FileNotFoundError(f"RTLLM benchmark root does not exist: {root}")
    return sorted(path for path in root.iterdir() if path.is_dir())


def resolve_rtllm_task_inputs(task_dir: Path) -> RTLLMTaskInput:
    """Resolve generation inputs for one benchmark task without reading golden outputs."""
    task_name = task_dir.name
    spec_path = task_dir / "design_description.txt"
    makefile_path = task_dir / "makefile"
    rtl_candidates = sorted(
        path
        for pattern in ("verified_*.v", "verified_*.sv")
        for path in task_dir.glob(pattern)
    )
    if not rtl_candidates:
        rtl_candidates = sorted(
            path
            for path in task_dir.iterdir()
            if path.is_file()
            and path.suffix in {".v", ".sv"}
            and path.name not in DISALLOWED_GENERATION_INPUT_NAMES
        )
    ignored_generation_inputs = sorted(
        str(path)
        for path in task_dir.iterdir()
        if path.is_file() and path.name in DISALLOWED_GENERATION_INPUT_NAMES
    )
    return RTLLMTaskInput(
        task_name=task_name,
        task_dir=task_dir,
        rtl_sources=rtl_candidates,
        spec_path=spec_path if spec_path.exists() else None,
        makefile_path=makefile_path if makefile_path.exists() else None,
        makefile_source_discovery_used=False,
        ignored_generation_inputs=ignored_generation_inputs,
    )


def run_rtllm_batch(
    config: RTLLMBatchConfig,
    *,
    task_runner: Callable[[RTLLMTaskInput, RTLLMBatchConfig, Path], RTLLMTaskSummary] | None = None,
) -> dict[str, Any]:
    """Execute the RTLLM batch harness and persist aggregate summaries."""
    out_dir = ensure_dir(config.out_dir)
    discovered_tasks = discover_rtllm_tasks(config.benchmark_root)
    try:
        if out_dir.parent.resolve() == config.benchmark_root.resolve():
            discovered_tasks = [task for task in discovered_tasks if task.resolve() != out_dir.resolve()]
    except FileNotFoundError:
        pass
    if config.task_names:
        selected = set(config.task_names)
        discovered_tasks = [task for task in discovered_tasks if task.name in selected]
    if config.limit is not None:
        discovered_tasks = discovered_tasks[: max(config.limit, 0)]
    runner = task_runner or _run_one_rtllm_task

    indexed_summaries: list[RTLLMTaskSummary | None] = [None] * len(discovered_tasks)
    pending_tasks: list[tuple[int, RTLLMTaskInput, Path]] = []
    resumed_count = 0
    for index, task_dir in enumerate(discovered_tasks):
        task_input = resolve_rtllm_task_inputs(task_dir)
        task_out_dir = out_dir / task_input.task_name
        if config.resume:
            cached_summary = _load_task_summary(task_out_dir)
            if cached_summary is not None:
                cached_summary.resumed_from_cache = True
                indexed_summaries[index] = cached_summary
                resumed_count += 1
                LOGGER.info("Resuming cached RTLLM batch task %s/%s: %s", index + 1, len(discovered_tasks), task_dir.name)
                continue
        pending_tasks.append((index, task_input, task_out_dir))

    worker_count = max(1, int(config.jobs))
    if worker_count == 1 or len(pending_tasks) <= 1:
        for index, task_input, task_out_dir in pending_tasks:
            indexed_summaries[index] = _execute_task_runner(
                runner=runner,
                task_input=task_input,
                config=config,
                task_out_dir=task_out_dir,
                index=index,
                total_tasks=len(discovered_tasks),
            )
    else:
        with ThreadPoolExecutor(max_workers=worker_count, thread_name_prefix="rtllm-batch") as executor:
            future_map = {
                executor.submit(
                    _execute_task_runner,
                    runner=runner,
                    task_input=task_input,
                    config=config,
                    task_out_dir=task_out_dir,
                    index=index,
                    total_tasks=len(discovered_tasks),
                ): index
                for index, task_input, task_out_dir in pending_tasks
            }
            for future in as_completed(future_map):
                index = future_map[future]
                indexed_summaries[index] = future.result()

    task_summaries = [summary for summary in indexed_summaries if summary is not None]

    batch_summary = _build_batch_summary(config=config, task_summaries=task_summaries)
    batch_summary.setdefault("aggregate_metrics", {})["resumed_tasks"] = resumed_count
    _write_batch_summary_files(config=config, batch_summary=batch_summary)
    return batch_summary


def _execute_task_runner(
    *,
    runner: Callable[[RTLLMTaskInput, RTLLMBatchConfig, Path], RTLLMTaskSummary],
    task_input: RTLLMTaskInput,
    config: RTLLMBatchConfig,
    task_out_dir: Path,
    index: int,
    total_tasks: int,
) -> RTLLMTaskSummary:
    LOGGER.info("Running RTLLM batch task %s/%s: %s", index + 1, total_tasks, task_input.task_name)
    try:
        task_summary = runner(task_input, config, task_out_dir)
    except Exception as exc:  # keep the batch moving even if the harness itself trips on one task
        task_summary = RTLLMTaskSummary(
            task_name=task_input.task_name,
            task_dir=str(task_input.task_dir),
            artifact_root=str(task_out_dir),
            rtl_sources=[str(path) for path in task_input.rtl_sources],
            spec_present=task_input.spec_path is not None,
            makefile_source_discovery_used=task_input.makefile_source_discovery_used,
            ignored_generation_inputs=list(task_input.ignored_generation_inputs),
            plan_generation_mode=config.generation_mode.value,
            oracle_generation_mode=config.generation_mode.value,
            task_status="failed",
            failure_reason_summary=f"batch_harness_error: {_single_line(str(exc))}",
        )
    _write_task_summary(task_out_dir, task_summary)
    return task_summary


def _run_one_rtllm_task(task_input: RTLLMTaskInput, config: RTLLMBatchConfig, task_out_dir: Path) -> RTLLMTaskSummary:
    ensure_dir(task_out_dir)
    shared_llm_client = LLMClient(config.llm_config) if config.generation_mode == GenerationMode.HYBRID else None
    spec_text = task_input.spec_path.read_text(encoding="utf-8", errors="replace") if task_input.spec_path else None
    interface_hint_text = extract_interface_hint_text(spec_text)
    task_description = _derive_task_description(task_input.task_name, spec_text)
    summary = RTLLMTaskSummary(
        task_name=task_input.task_name,
        task_dir=str(task_input.task_dir),
        artifact_root=str(task_out_dir),
        rtl_sources=[str(path) for path in task_input.rtl_sources],
        spec_present=task_input.spec_path is not None,
        makefile_source_discovery_used=task_input.makefile_source_discovery_used,
        ignored_generation_inputs=list(task_input.ignored_generation_inputs),
        plan_generation_mode=config.generation_mode.value,
        oracle_generation_mode=config.generation_mode.value,
    )

    if not task_input.rtl_sources:
        summary.failure_reason_summary = "input_resolution_failed: no DUT RTL sources were resolved"
        return summary

    try:
        contract = ContractExtractor().run(
            rtl_paths=task_input.rtl_sources,
            task_description=task_description,
            spec_text=spec_text,
            golden_interface_text=interface_hint_text,
            out_dir=task_out_dir,
        )
        summary.contract_success = True
        summary.module_name = contract.module_name
    except Exception as exc:
        summary.failure_reason_summary = f"contract_failed: {_single_line(str(exc))}"
        return summary

    try:
        plan = TestPlanGenerator(llm_client=shared_llm_client).run(
            contract=contract,
            task_description=task_description,
            spec_text=spec_text,
            out_dir=task_out_dir,
            generation_mode=config.generation_mode,
            llm_config=config.llm_config,
        )
        summary.plan_success = True
        _apply_llm_stage_status(
            summary=summary,
            stage_name="plan",
            attempted=config.generation_mode == GenerationMode.HYBRID,
            merge_report_path=task_out_dir / "plan" / "llm_merge_report.json",
        )
    except Exception as exc:
        summary.failure_reason_summary = f"plan_failed: {_single_line(str(exc))}"
        return summary

    try:
        oracle = OracleGenerator(llm_client=shared_llm_client).run(
            contract=contract,
            plan=plan,
            task_description=task_description,
            spec_text=spec_text,
            out_dir=task_out_dir,
            generation_mode=config.generation_mode,
            llm_config=config.llm_config,
        )
        summary.oracle_success = True
        summary.assertion_strength_counts = _count_assertion_strengths(oracle)
        _apply_llm_stage_status(
            summary=summary,
            stage_name="oracle",
            attempted=config.generation_mode == GenerationMode.HYBRID,
            merge_report_path=task_out_dir / "oracle" / "llm_merge_report.json",
        )
    except Exception as exc:
        summary.failure_reason_summary = f"oracle_failed: {_single_line(str(exc))}"
        return summary

    try:
        metadata = TBRenderer().run(
            contract=contract,
            plan=plan,
            oracle=oracle,
            task_description=task_description,
            spec_text=spec_text,
            out_dir=task_out_dir,
            based_on_contract=str(task_out_dir / "contract" / "contract.json"),
            based_on_plan=str(task_out_dir / "plan" / "test_plan.json"),
            based_on_oracle=str(task_out_dir / "oracle" / "oracle.json"),
        )
        summary.render_success = True
        summary.rendered_test_modules = list(metadata.test_modules)
    except Exception as exc:
        summary.failure_reason_summary = f"render_failed: {_single_line(str(exc))}"
        return summary

    render_metadata_path = task_out_dir / "render" / "metadata.json"
    test_modules = list(summary.rendered_test_modules)
    if not test_modules:
        summary.failure_reason_summary = "render_failed: render metadata listed no test modules"
        return summary

    for test_module in test_modules:
        module_out_dir = task_out_dir / "runs" / test_module
        module_result = _run_test_module(
            render_metadata_path=render_metadata_path,
            rtl_sources=task_input.rtl_sources,
            test_module=test_module,
            config=config,
            module_out_dir=module_out_dir,
        )
        summary.test_module_results.append(module_result)

    summary.task_status = _derive_task_status(summary)
    summary.failure_reason_summary = _derive_failure_reason_summary(summary)
    return summary


def _run_test_module(
    *,
    render_metadata_path: Path,
    rtl_sources: list[Path],
    test_module: str,
    config: RTLLMBatchConfig,
    module_out_dir: Path,
) -> RTLLMModuleRunResult:
    sim_config = SimulationConfig(
        simulator=config.simulator,
        mode=config.simulation_mode,
        rtl_sources=list(rtl_sources),
        test_module=test_module,
        timeout_seconds=config.timeout_seconds,
        junit_enabled=config.junit_enabled,
        waves_enabled=config.waves_enabled,
        clean_build=config.clean_build,
    )
    try:
        simulation_result = SimulatorRunnerStage().run_from_artifact(
            render_metadata_path=render_metadata_path,
            config=sim_config,
            out_dir=module_out_dir,
        )
        triage = TriageStage().run_from_dir(in_dir=module_out_dir, out_dir=module_out_dir)
        return RTLLMModuleRunResult(
            test_module=test_module,
            run_status=str(simulation_result.status),
            triage_category=triage.primary_category,
            passed_tests_count=len(simulation_result.passed_tests),
            failed_tests_count=len(simulation_result.failed_tests),
            return_code=simulation_result.return_code,
            run_dir=str(module_out_dir / "run"),
            triage_dir=str(module_out_dir / "triage"),
            passed_tests=list(simulation_result.passed_tests),
            failed_tests=list(simulation_result.failed_tests),
        )
    except Exception as exc:
        return RTLLMModuleRunResult(
            test_module=test_module,
            run_status="harness_error",
            triage_category="harness_error",
            passed_tests_count=0,
            failed_tests_count=0,
            return_code=None,
            run_dir=str(module_out_dir / "run"),
            triage_dir=str(module_out_dir / "triage"),
            failed_tests=[_single_line(str(exc))],
        )


def _count_assertion_strengths(oracle: OracleSpec) -> dict[str, int]:
    counts: Counter[str] = Counter({"exact": 0, "guarded": 0, "unresolved": 0})
    for oracle_case in [*oracle.protocol_oracles, *oracle.functional_oracles, *oracle.property_oracles]:
        for check in oracle_case.checks:
            for policy in check.signal_policies.values():
                counts[str(policy.strength)] += 1
    return {key: int(counts.get(key, 0)) for key in ("exact", "guarded", "unresolved")}


def _apply_llm_stage_status(
    *,
    summary: RTLLMTaskSummary,
    stage_name: str,
    attempted: bool,
    merge_report_path: Path,
) -> None:
    report = _load_optional_json(merge_report_path)
    status = str(report.get("status", "missing_report")) if report else ("missing_report" if attempted else "not_attempted")
    reason = _single_line(str(report.get("reason", ""))) if report else ""
    succeeded = attempted and status == "merged"
    fallback_used = attempted and status == "fallback"
    if stage_name == "plan":
        summary.llm_plan_attempted = attempted
        summary.llm_plan_succeeded = succeeded
        summary.llm_plan_fallback_used = fallback_used
        summary.llm_plan_status = status
        summary.llm_plan_reason = reason
        return
    summary.llm_oracle_attempted = attempted
    summary.llm_oracle_succeeded = succeeded
    summary.llm_oracle_fallback_used = fallback_used
    summary.llm_oracle_status = status
    summary.llm_oracle_reason = reason


def _load_optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _task_summary_path(task_out_dir: Path) -> Path:
    return task_out_dir / "task_summary.json"


def _write_task_summary(task_out_dir: Path, summary: RTLLMTaskSummary) -> None:
    ensure_dir(task_out_dir)
    write_json(_task_summary_path(task_out_dir), summary.to_dict())


def _load_task_summary(task_out_dir: Path) -> RTLLMTaskSummary | None:
    path = _task_summary_path(task_out_dir)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or not payload.get("task_name"):
        return None
    module_results = [
        RTLLMModuleRunResult(
            test_module=str(item.get("test_module", "")),
            run_status=str(item.get("run_status", "")),
            triage_category=str(item.get("triage_category", "")),
            passed_tests_count=int(item.get("passed_tests_count", 0)),
            failed_tests_count=int(item.get("failed_tests_count", 0)),
            return_code=item.get("return_code"),
            run_dir=str(item.get("run_dir", "")),
            triage_dir=str(item.get("triage_dir", "")),
            passed_tests=[str(name) for name in item.get("passed_tests", [])],
            failed_tests=[str(name) for name in item.get("failed_tests", [])],
        )
        for item in payload.get("test_module_results", [])
        if isinstance(item, dict)
    ]
    return RTLLMTaskSummary(
        task_name=str(payload.get("task_name", "")),
        module_name=str(payload.get("module_name", "")),
        task_dir=str(payload.get("task_dir", "")),
        artifact_root=str(payload.get("artifact_root", "")),
        rtl_sources=[str(path) for path in payload.get("rtl_sources", [])],
        spec_present=bool(payload.get("spec_present", False)),
        makefile_source_discovery_used=bool(payload.get("makefile_source_discovery_used", False)),
        ignored_generation_inputs=[str(path) for path in payload.get("ignored_generation_inputs", [])],
        plan_generation_mode=str(payload.get("plan_generation_mode", GenerationMode.HYBRID.value)),
        oracle_generation_mode=str(payload.get("oracle_generation_mode", GenerationMode.HYBRID.value)),
        llm_plan_attempted=bool(payload.get("llm_plan_attempted", False)),
        llm_plan_succeeded=bool(payload.get("llm_plan_succeeded", False)),
        llm_plan_fallback_used=bool(payload.get("llm_plan_fallback_used", False)),
        llm_plan_status=str(payload.get("llm_plan_status", "not_attempted")),
        llm_plan_reason=str(payload.get("llm_plan_reason", "")),
        llm_oracle_attempted=bool(payload.get("llm_oracle_attempted", False)),
        llm_oracle_succeeded=bool(payload.get("llm_oracle_succeeded", False)),
        llm_oracle_fallback_used=bool(payload.get("llm_oracle_fallback_used", False)),
        llm_oracle_status=str(payload.get("llm_oracle_status", "not_attempted")),
        llm_oracle_reason=str(payload.get("llm_oracle_reason", "")),
        contract_success=bool(payload.get("contract_success", False)),
        plan_success=bool(payload.get("plan_success", False)),
        oracle_success=bool(payload.get("oracle_success", False)),
        render_success=bool(payload.get("render_success", False)),
        rendered_test_modules=[str(name) for name in payload.get("rendered_test_modules", [])],
        test_module_results=module_results,
        assertion_strength_counts={
            "exact": int(payload.get("assertion_strength_counts", {}).get("exact", 0)),
            "guarded": int(payload.get("assertion_strength_counts", {}).get("guarded", 0)),
            "unresolved": int(payload.get("assertion_strength_counts", {}).get("unresolved", 0)),
        },
        resumed_from_cache=bool(payload.get("resumed_from_cache", False)),
        task_status=str(payload.get("task_status", "failed")),
        failure_reason_summary=str(payload.get("failure_reason_summary", "")),
    )


def _derive_task_status(summary: RTLLMTaskSummary) -> str:
    if not summary.render_success:
        return "failed"
    module_results = list(summary.test_module_results)
    if not module_results:
        return "failed"
    successful_modules = [
        item
        for item in module_results
        if item.run_status == "success" and item.triage_category == "no_failure"
    ]
    if len(successful_modules) == len(module_results):
        return "success"
    if successful_modules:
        return "partial_success"
    return "failed"


def _derive_failure_reason_summary(summary: RTLLMTaskSummary) -> str:
    if summary.failure_reason_summary:
        return summary.failure_reason_summary
    failed_modules = [
        f"{item.test_module}:{item.run_status}/{item.triage_category}"
        for item in summary.test_module_results
        if not (item.run_status == "success" and item.triage_category == "no_failure")
    ]
    if failed_modules:
        return "module_failures=" + ", ".join(failed_modules)
    return ""


def _build_batch_summary(*, config: RTLLMBatchConfig, task_summaries: Iterable[RTLLMTaskSummary]) -> dict[str, Any]:
    task_summaries = list(task_summaries)
    triage_histogram: Counter[str] = Counter()
    assertion_histogram: Counter[str] = Counter({"exact": 0, "guarded": 0, "unresolved": 0})
    false_positive_count = 0
    tasks_with_at_least_one_successful_run = 0
    tasks_with_all_rendered_test_modules_successful = 0
    ambiguity_preserving_tasks = 0
    llm_plan_status_histogram: Counter[str] = Counter()
    llm_oracle_status_histogram: Counter[str] = Counter()

    for task_summary in task_summaries:
        successful_modules = [
            item
            for item in task_summary.test_module_results
            if item.run_status == "success" and item.triage_category == "no_failure"
        ]
        if successful_modules:
            tasks_with_at_least_one_successful_run += 1
        if task_summary.render_success and task_summary.test_module_results and len(successful_modules) == len(task_summary.test_module_results):
            tasks_with_all_rendered_test_modules_successful += 1
        if any(item.triage_category == "runtime_test_failure" for item in task_summary.test_module_results):
            false_positive_count += 1
        if task_summary.assertion_strength_counts.get("guarded", 0) or task_summary.assertion_strength_counts.get("unresolved", 0):
            ambiguity_preserving_tasks += 1
        llm_plan_status_histogram[task_summary.llm_plan_status] += 1
        llm_oracle_status_histogram[task_summary.llm_oracle_status] += 1
        for item in task_summary.test_module_results:
            triage_histogram[item.triage_category] += 1
        for key, value in task_summary.assertion_strength_counts.items():
            assertion_histogram[key] += int(value)

    aggregate_metrics = {
        "discovered_tasks": len(task_summaries),
        "tasks_with_valid_contract": sum(1 for item in task_summaries if item.contract_success),
        "tasks_with_valid_plan": sum(1 for item in task_summaries if item.plan_success),
        "tasks_with_valid_oracle": sum(1 for item in task_summaries if item.oracle_success),
        "tasks_with_valid_render": sum(1 for item in task_summaries if item.render_success),
        "tasks_with_at_least_one_successful_run": tasks_with_at_least_one_successful_run,
        "tasks_with_all_rendered_test_modules_successful": tasks_with_all_rendered_test_modules_successful,
        "false_positive_count_on_verified_rtl": false_positive_count,
        "tasks_with_guarded_or_unresolved_policies": ambiguity_preserving_tasks,
        "llm_plan_attempted": sum(1 for item in task_summaries if item.llm_plan_attempted),
        "llm_plan_succeeded": sum(1 for item in task_summaries if item.llm_plan_succeeded),
        "llm_plan_fallback_used": sum(1 for item in task_summaries if item.llm_plan_fallback_used),
        "llm_oracle_attempted": sum(1 for item in task_summaries if item.llm_oracle_attempted),
        "llm_oracle_succeeded": sum(1 for item in task_summaries if item.llm_oracle_succeeded),
        "llm_oracle_fallback_used": sum(1 for item in task_summaries if item.llm_oracle_fallback_used),
        "llm_plan_status_histogram": dict(sorted(llm_plan_status_histogram.items())),
        "llm_oracle_status_histogram": dict(sorted(llm_oracle_status_histogram.items())),
        "triage_category_histogram": dict(sorted(triage_histogram.items())),
        "assertion_strength_histogram": {
            "exact": int(assertion_histogram["exact"]),
            "guarded": int(assertion_histogram["guarded"]),
            "unresolved": int(assertion_histogram["unresolved"]),
        },
        "makefile_source_discovery_tasks": sum(1 for item in task_summaries if item.makefile_source_discovery_used),
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_root": str(config.benchmark_root),
        "out_dir": str(config.out_dir),
        "pipeline": [
            "contract",
            f"plan({config.generation_mode.value})",
            f"oracle({config.generation_mode.value})",
            "render",
            "run",
            "triage",
        ],
        "experimental_fill_used": False,
        "llm_runtime_policy": {
            "provider": config.llm_config.provider,
            "model": config.llm_config.model,
            "base_url": config.llm_config.base_url,
            "trust_env": config.llm_config.trust_env,
            "disable_proxies": config.llm_config.disable_proxies,
        },
        "batch_execution_policy": {
            "jobs": int(config.jobs),
            "resume": bool(config.resume),
        },
        "generation_input_policy": {
            "allowed": ["verified RTL", "design_description.txt", "benchmark makefile only for source discovery if needed"],
            "disallowed": ["reference.dat", "benchmark testbench.v", "golden output data"],
        },
        "aggregate_metrics": aggregate_metrics,
        "tasks": [item.to_dict() for item in task_summaries],
    }


def _write_batch_summary_files(*, config: RTLLMBatchConfig, batch_summary: dict[str, Any]) -> None:
    out_dir = ensure_dir(config.out_dir)
    write_json(out_dir / "summary.json", batch_summary)
    _write_summary_csv(out_dir / "summary.csv", batch_summary)
    write_text(out_dir / "summary.md", _render_summary_markdown(batch_summary))


def _write_summary_csv(path: Path, batch_summary: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "task_name",
                "module_name",
                "task_status",
                "contract_success",
                "plan_success",
                "oracle_success",
                "render_success",
                "spec_present",
                "rtl_sources",
                "rendered_test_modules",
                "llm_plan_status",
                "llm_oracle_status",
                "test_module_outcomes",
                "assertion_exact",
                "assertion_guarded",
                "assertion_unresolved",
                "failure_reason_summary",
                "makefile_source_discovery_used",
            ],
        )
        writer.writeheader()
        for task in batch_summary["tasks"]:
            writer.writerow(
                {
                    "task_name": task["task_name"],
                    "module_name": task["module_name"],
                    "task_status": task["task_status"],
                    "contract_success": task["contract_success"],
                    "plan_success": task["plan_success"],
                    "oracle_success": task["oracle_success"],
                    "render_success": task["render_success"],
                    "spec_present": task["spec_present"],
                    "rtl_sources": ";".join(task["rtl_sources"]),
                    "rendered_test_modules": ";".join(task["rendered_test_modules"]),
                    "llm_plan_status": task["llm_plan_status"],
                    "llm_oracle_status": task["llm_oracle_status"],
                    "test_module_outcomes": ";".join(
                        f"{item['test_module']}:{item['run_status']}/{item['triage_category']}"
                        for item in task["test_module_results"]
                    ),
                    "assertion_exact": task["assertion_strength_counts"]["exact"],
                    "assertion_guarded": task["assertion_strength_counts"]["guarded"],
                    "assertion_unresolved": task["assertion_strength_counts"]["unresolved"],
                    "failure_reason_summary": task["failure_reason_summary"],
                    "makefile_source_discovery_used": task["makefile_source_discovery_used"],
                }
            )


def _render_summary_markdown(batch_summary: dict[str, Any]) -> str:
    metrics = batch_summary["aggregate_metrics"]
    lines = [
        "# RTLLM Batch Summary",
        "",
        f"- Benchmark root: `{batch_summary['benchmark_root']}`",
        f"- Output dir: `{batch_summary['out_dir']}`",
        f"- Pipeline: `{ ' -> '.join(batch_summary['pipeline']) }`",
        f"- Experimental fill used: `{batch_summary['experimental_fill_used']}`",
        f"- LLM runtime policy: `provider={batch_summary['llm_runtime_policy']['provider']}, model={batch_summary['llm_runtime_policy']['model']}, trust_env={batch_summary['llm_runtime_policy']['trust_env']}, disable_proxies={batch_summary['llm_runtime_policy']['disable_proxies']}`",
        f"- Batch execution policy: `jobs={batch_summary['batch_execution_policy']['jobs']}, resume={batch_summary['batch_execution_policy']['resume']}`",
        "",
        "## Aggregate Metrics",
        "",
        f"- Discovered tasks: {metrics['discovered_tasks']}",
        f"- Valid contract: {metrics['tasks_with_valid_contract']}",
        f"- Valid plan: {metrics['tasks_with_valid_plan']}",
        f"- Valid oracle: {metrics['tasks_with_valid_oracle']}",
        f"- Valid render: {metrics['tasks_with_valid_render']}",
        f"- Tasks with >=1 successful run: {metrics['tasks_with_at_least_one_successful_run']}",
        f"- Tasks with all rendered modules successful: {metrics['tasks_with_all_rendered_test_modules_successful']}",
        f"- False positive count on verified RTL: {metrics['false_positive_count_on_verified_rtl']}",
        f"- Tasks with guarded/unresolved policies: {metrics['tasks_with_guarded_or_unresolved_policies']}",
        f"- LLM plan attempted/succeeded/fallback: {metrics['llm_plan_attempted']}/{metrics['llm_plan_succeeded']}/{metrics['llm_plan_fallback_used']}",
        f"- LLM oracle attempted/succeeded/fallback: {metrics['llm_oracle_attempted']}/{metrics['llm_oracle_succeeded']}/{metrics['llm_oracle_fallback_used']}",
        f"- Resumed tasks: {metrics.get('resumed_tasks', 0)}",
        "",
        "## Histograms",
        "",
        f"- Triage: `{json.dumps(metrics['triage_category_histogram'], sort_keys=True)}`",
        f"- Assertion strength: `{json.dumps(metrics['assertion_strength_histogram'], sort_keys=True)}`",
        f"- LLM plan status: `{json.dumps(metrics['llm_plan_status_histogram'], sort_keys=True)}`",
        f"- LLM oracle status: `{json.dumps(metrics['llm_oracle_status_histogram'], sort_keys=True)}`",
        "",
        "## Per-Task Rollup",
        "",
        "| Task | Status | LLM(plan/oracle) | Modules | Assertion Strengths | Failure Summary |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for task in batch_summary["tasks"]:
        module_summary = ", ".join(
            f"{item['test_module']}:{item['run_status']}/{item['triage_category']}"
            for item in task["test_module_results"]
        )
        strength_summary = task["assertion_strength_counts"]
        lines.append(
            "| {task} | {status} | {llm_plan}/{llm_oracle} | {modules} | exact={exact}, guarded={guarded}, unresolved={unresolved} | {failure} |".format(
                task=task["task_name"],
                status=task["task_status"],
                llm_plan=task["llm_plan_status"],
                llm_oracle=task["llm_oracle_status"],
                modules=module_summary or "-",
                exact=strength_summary["exact"],
                guarded=strength_summary["guarded"],
                unresolved=strength_summary["unresolved"],
                failure=task["failure_reason_summary"] or "-",
            )
        )
    lines.append("")
    return "\n".join(lines)


def _derive_task_description(task_name: str, spec_text: str | None) -> str:
    for line in str(spec_text or "").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return f"RTLLM benchmark task {task_name}"


def _single_line(message: str) -> str:
    return " ".join(str(message or "").split())


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m cocoverify2.eval.rtllm_batch",
        description="Run the aligned mainline cocoverify2 pipeline across the RTLLM benchmark.",
    )
    parser.add_argument("--root", type=Path, default=DEFAULT_RTLLM_ROOT, help="RTLLM benchmark root directory.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory for batch artifacts.")
    parser.add_argument(
        "--generation-mode",
        choices=[mode.value for mode in GenerationMode],
        default=GenerationMode.HYBRID.value,
        help="Generation mode for plan/oracle stages.",
    )
    parser.add_argument("--simulator", default="icarus", help="Simulator backend name.")
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in SimulationMode],
        default=SimulationMode.AUTO.value,
        help="Simulation execution mode.",
    )
    parser.add_argument("--timeout-seconds", type=int, default=60, help="Per-run simulation timeout.")
    parser.add_argument("--llm-provider", default="", help="Optional LLM provider override.")
    parser.add_argument("--llm-model", default="", help="Optional LLM model override.")
    parser.add_argument("--llm-base-url", default="", help="Optional LLM base URL override.")
    parser.add_argument("--llm-api-key", default="", help="Optional LLM API key override.")
    parser.add_argument("--llm-temperature", type=float, default=None, help="Optional LLM temperature override.")
    parser.add_argument("--llm-timeout-seconds", type=int, default=None, help="Optional LLM timeout override.")
    parser.add_argument("--llm-max-retries", type=int, default=None, help="Optional LLM retry override.")
    parser.add_argument(
        "--llm-disable-proxies",
        action="store_true",
        help="Explicitly clear proxy environment variables for LLM requests during the batch run.",
    )
    parser.add_argument(
        "--llm-trust-env",
        action="store_true",
        help="Force the LLM client to keep proxy-related environment variables untouched.",
    )
    parser.add_argument("--task", action="append", default=[], help="Optional task name filter; may be passed multiple times.")
    parser.add_argument("--limit", type=int, default=None, help="Optional maximum number of tasks to run.")
    parser.add_argument("--jobs", type=int, default=1, help="Task-level parallelism for the batch runner.")
    parser.add_argument("--resume", action="store_true", help="Reuse per-task summaries that already exist under the output directory.")
    parser.add_argument("--no-clean-build", action="store_true", help="Disable clean-build runs.")
    parser.add_argument("--waves", action="store_true", help="Enable waveform capture.")
    return parser.parse_args(argv)


def _build_llm_config(args: argparse.Namespace) -> LLMConfig:
    config = LLMConfig()
    overrides: dict[str, Any] = {}
    if args.llm_provider:
        overrides["provider"] = args.llm_provider
    if args.llm_model:
        overrides["model"] = args.llm_model
    if args.llm_base_url:
        overrides["base_url"] = args.llm_base_url
    if args.llm_api_key:
        overrides["api_key"] = args.llm_api_key
    if args.llm_temperature is not None:
        overrides["temperature"] = args.llm_temperature
    if args.llm_timeout_seconds is not None:
        overrides["timeout_seconds"] = args.llm_timeout_seconds
    if args.llm_max_retries is not None:
        overrides["max_retries"] = args.llm_max_retries
    if args.llm_disable_proxies:
        overrides["disable_proxies"] = True
    if args.llm_trust_env:
        overrides["trust_env"] = True
    return config.model_copy(update=overrides)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    config = RTLLMBatchConfig(
        benchmark_root=args.root,
        out_dir=args.out_dir,
        generation_mode=GenerationMode(args.generation_mode),
        simulator=args.simulator,
        simulation_mode=SimulationMode(args.mode),
        timeout_seconds=args.timeout_seconds,
        clean_build=not args.no_clean_build,
        waves_enabled=args.waves,
        llm_config=_build_llm_config(args),
        task_names=list(args.task),
        limit=args.limit,
        jobs=max(1, int(args.jobs)),
        resume=args.resume,
    )
    batch_summary = run_rtllm_batch(config)
    summary_dir = Path(batch_summary["out_dir"])
    print(f"RTLLM batch evaluation complete -> {summary_dir / 'summary.json'}")
    print(f"CSV summary -> {summary_dir / 'summary.csv'}")
    print(f"Markdown summary -> {summary_dir / 'summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
