"""Hermetic tests for the RTLLM batch evaluator."""

from __future__ import annotations

from pathlib import Path

from cocoverify2.eval.rtllm_batch import (
    RTLLMBatchConfig,
    RTLLMModuleRunResult,
    RTLLMTaskSummary,
    _build_batch_summary,
    discover_rtllm_tasks,
    resolve_rtllm_task_inputs,
    run_rtllm_batch,
)


def test_discover_rtllm_tasks_lists_immediate_directories(tmp_path: Path) -> None:
    (tmp_path / "task_a").mkdir()
    (tmp_path / "task_b").mkdir()
    (tmp_path / "README.txt").write_text("ignore me", encoding="utf-8")

    discovered = discover_rtllm_tasks(tmp_path)

    assert [path.name for path in discovered] == ["task_a", "task_b"]


def test_resolve_rtllm_task_inputs_ignores_golden_files(tmp_path: Path) -> None:
    task_dir = tmp_path / "alu"
    task_dir.mkdir()
    (task_dir / "verified_alu.v").write_text("module verified_alu; endmodule", encoding="utf-8")
    (task_dir / "design_description.txt").write_text("ALU spec", encoding="utf-8")
    (task_dir / "testbench.v").write_text("module tb; endmodule", encoding="utf-8")
    (task_dir / "reference.dat").write_text("golden", encoding="utf-8")
    (task_dir / "makefile").write_text("all:\n\ttrue\n", encoding="utf-8")

    resolved = resolve_rtllm_task_inputs(task_dir)

    assert resolved.task_name == "alu"
    assert resolved.spec_path == task_dir / "design_description.txt"
    assert resolved.makefile_path == task_dir / "makefile"
    assert resolved.rtl_sources == [task_dir / "verified_alu.v"]
    assert str(task_dir / "testbench.v") in resolved.ignored_generation_inputs
    assert str(task_dir / "reference.dat") in resolved.ignored_generation_inputs
    assert resolved.makefile_source_discovery_used is False


def test_build_batch_summary_aggregates_histograms() -> None:
    task_ok = RTLLMTaskSummary(
        task_name="task_ok",
        contract_success=True,
        plan_success=True,
        oracle_success=True,
        render_success=True,
        rendered_test_modules=["test_ok_basic", "test_ok_edge"],
        test_module_results=[
            RTLLMModuleRunResult(
                test_module="test_ok_basic",
                run_status="success",
                triage_category="no_failure",
                passed_tests_count=2,
                failed_tests_count=0,
                return_code=0,
                run_dir="run/basic",
                triage_dir="triage/basic",
            ),
            RTLLMModuleRunResult(
                test_module="test_ok_edge",
                run_status="success",
                triage_category="no_failure",
                passed_tests_count=1,
                failed_tests_count=0,
                return_code=0,
                run_dir="run/edge",
                triage_dir="triage/edge",
            ),
        ],
        assertion_strength_counts={"exact": 2, "guarded": 1, "unresolved": 3},
        task_status="success",
    )
    task_partial = RTLLMTaskSummary(
        task_name="task_partial",
        contract_success=True,
        plan_success=True,
        oracle_success=True,
        render_success=True,
        rendered_test_modules=["test_partial_basic"],
        test_module_results=[
            RTLLMModuleRunResult(
                test_module="test_partial_basic",
                run_status="runtime_error",
                triage_category="runtime_test_failure",
                passed_tests_count=0,
                failed_tests_count=1,
                return_code=1,
                run_dir="run/basic",
                triage_dir="triage/basic",
            )
        ],
        assertion_strength_counts={"exact": 0, "guarded": 4, "unresolved": 5},
        task_status="failed",
    )

    summary = _build_batch_summary(
        config=RTLLMBatchConfig(benchmark_root=Path("/tmp/bench")),
        task_summaries=[task_ok, task_partial],
    )

    metrics = summary["aggregate_metrics"]
    assert metrics["discovered_tasks"] == 2
    assert metrics["tasks_with_valid_render"] == 2
    assert metrics["tasks_with_at_least_one_successful_run"] == 1
    assert metrics["tasks_with_all_rendered_test_modules_successful"] == 1
    assert metrics["false_positive_count_on_verified_rtl"] == 1
    assert metrics["triage_category_histogram"] == {"no_failure": 2, "runtime_test_failure": 1}
    assert metrics["assertion_strength_histogram"] == {"exact": 2, "guarded": 5, "unresolved": 8}


def test_run_rtllm_batch_continues_after_task_failure(tmp_path: Path) -> None:
    for name in ("task_a", "task_b"):
        task_dir = tmp_path / name
        task_dir.mkdir()
        (task_dir / f"verified_{name}.v").write_text("module m; endmodule", encoding="utf-8")
        (task_dir / "design_description.txt").write_text(f"{name} spec", encoding="utf-8")

    def fake_runner(task_input, config, task_out_dir):  # noqa: ANN001
        if task_input.task_name == "task_a":
            raise RuntimeError("boom")
        return RTLLMTaskSummary(
            task_name=task_input.task_name,
            task_dir=str(task_input.task_dir),
            artifact_root=str(task_out_dir),
            rtl_sources=[str(path) for path in task_input.rtl_sources],
            spec_present=task_input.spec_path is not None,
            plan_generation_mode=config.generation_mode.value,
            oracle_generation_mode=config.generation_mode.value,
            contract_success=True,
            plan_success=True,
            oracle_success=True,
            render_success=True,
            rendered_test_modules=["test_task_b_basic"],
            test_module_results=[
                RTLLMModuleRunResult(
                    test_module="test_task_b_basic",
                    run_status="success",
                    triage_category="no_failure",
                    passed_tests_count=1,
                    failed_tests_count=0,
                    return_code=0,
                    run_dir=str(task_out_dir / "runs" / "test_task_b_basic" / "run"),
                    triage_dir=str(task_out_dir / "runs" / "test_task_b_basic" / "triage"),
                )
            ],
            assertion_strength_counts={"exact": 1, "guarded": 0, "unresolved": 0},
            task_status="success",
        )

    batch_summary = run_rtllm_batch(
        RTLLMBatchConfig(benchmark_root=tmp_path, out_dir=tmp_path / "out"),
        task_runner=fake_runner,
    )

    tasks = {item["task_name"]: item for item in batch_summary["tasks"]}
    assert tasks["task_a"]["task_status"] == "failed"
    assert "batch_harness_error" in tasks["task_a"]["failure_reason_summary"]
    assert tasks["task_b"]["task_status"] == "success"
    assert (tmp_path / "out" / "summary.json").exists()
    assert (tmp_path / "out" / "summary.csv").exists()
    assert (tmp_path / "out" / "summary.md").exists()
