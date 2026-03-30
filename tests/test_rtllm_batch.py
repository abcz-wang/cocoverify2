"""Hermetic tests for the RTLLM batch evaluator."""

from __future__ import annotations

import json
from pathlib import Path

from cocoverify2.eval.rtllm_batch import (
    RTLLMBatchConfig,
    RTLLMModuleRunResult,
    RTLLMTaskSummary,
    _build_batch_summary,
    _write_task_summary,
    discover_rtllm_tasks,
    resolve_rtllm_task_inputs,
    run_rtllm_batch,
)
from cocoverify2.utils.spec_hints import extract_interface_hint_text


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


def test_extract_interface_hint_text_keeps_only_structured_interface_lines() -> None:
    spec_text = """
Please act as a professional verilog designer.

Implement an ALU for a 32-bit MIPS-ISA CPU.

Module name:
    alu

Input ports:
    a: a 32-bit input operand
    b: a 32-bit input operand
    aluc: a 6-bit control signal for selecting the operation

Output ports:
    r: a 32-bit output representing the result
    zero: a 1-bit output indicating whether the result is zero

Implementation:
The module uses a case statement to implement opcode semantics.
The zero output is set when the result is all zeros.
""".strip()

    extracted = extract_interface_hint_text(spec_text)

    assert extracted == "\n".join(
        [
            "a: a 32-bit input operand",
            "b: a 32-bit input operand",
            "aluc: a 6-bit control signal for selecting the operation",
            "r: a 32-bit output representing the result",
            "zero: a 1-bit output indicating whether the result is zero",
        ]
    )
    assert "Implementation" not in extracted
    assert "case statement" not in extracted


def test_extract_interface_hint_text_returns_none_without_structured_sections() -> None:
    extracted = extract_interface_hint_text("This is free-form behavior text without explicit interface sections.")

    assert extracted is None


def test_build_batch_summary_aggregates_histograms() -> None:
    task_ok = RTLLMTaskSummary(
        task_name="task_ok",
        contract_success=True,
        plan_success=True,
        oracle_success=True,
        render_success=True,
        llm_plan_attempted=True,
        llm_plan_succeeded=True,
        llm_plan_status="merged",
        llm_oracle_attempted=True,
        llm_oracle_succeeded=True,
        llm_oracle_status="merged",
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
        llm_plan_attempted=True,
        llm_plan_fallback_used=True,
        llm_plan_status="fallback",
        llm_plan_reason="Connection error.",
        llm_oracle_attempted=True,
        llm_oracle_fallback_used=True,
        llm_oracle_status="fallback",
        llm_oracle_reason="Connection error.",
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
    assert metrics["llm_plan_attempted"] == 2
    assert metrics["llm_plan_succeeded"] == 1
    assert metrics["llm_plan_fallback_used"] == 1
    assert metrics["llm_oracle_attempted"] == 2
    assert metrics["llm_oracle_succeeded"] == 1
    assert metrics["llm_oracle_fallback_used"] == 1
    assert metrics["llm_plan_status_histogram"] == {"fallback": 1, "merged": 1}
    assert metrics["llm_oracle_status_histogram"] == {"fallback": 1, "merged": 1}
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


def test_run_rtllm_batch_resume_reuses_existing_task_summary(tmp_path: Path) -> None:
    for name in ("task_a", "task_b"):
        task_dir = tmp_path / name
        task_dir.mkdir()
        (task_dir / f"verified_{name}.v").write_text("module m; endmodule", encoding="utf-8")
        (task_dir / "design_description.txt").write_text(f"{name} spec", encoding="utf-8")

    cached_summary = RTLLMTaskSummary(
        task_name="task_a",
        task_dir=str(tmp_path / "task_a"),
        artifact_root=str(tmp_path / "out" / "task_a"),
        rtl_sources=[str(tmp_path / "task_a" / "verified_task_a.v")],
        spec_present=True,
        contract_success=True,
        plan_success=True,
        oracle_success=True,
        render_success=True,
        rendered_test_modules=["test_task_a_basic"],
        test_module_results=[
            RTLLMModuleRunResult(
                test_module="test_task_a_basic",
                run_status="success",
                triage_category="no_failure",
                passed_tests_count=1,
                failed_tests_count=0,
                return_code=0,
                run_dir="run/basic",
                triage_dir="triage/basic",
            )
        ],
        assertion_strength_counts={"exact": 1, "guarded": 0, "unresolved": 0},
        task_status="success",
    )
    _write_task_summary(tmp_path / "out" / "task_a", cached_summary)

    executed: list[str] = []

    def fake_runner(task_input, config, task_out_dir):  # noqa: ANN001
        executed.append(task_input.task_name)
        return RTLLMTaskSummary(
            task_name=task_input.task_name,
            task_dir=str(task_input.task_dir),
            artifact_root=str(task_out_dir),
            rtl_sources=[str(path) for path in task_input.rtl_sources],
            spec_present=True,
            contract_success=True,
            plan_success=True,
            oracle_success=True,
            render_success=True,
            rendered_test_modules=[f"test_{task_input.task_name}_basic"],
            test_module_results=[
                RTLLMModuleRunResult(
                    test_module=f"test_{task_input.task_name}_basic",
                    run_status="success",
                    triage_category="no_failure",
                    passed_tests_count=1,
                    failed_tests_count=0,
                    return_code=0,
                    run_dir=str(task_out_dir / "run"),
                    triage_dir=str(task_out_dir / "triage"),
                )
            ],
            assertion_strength_counts={"exact": 1, "guarded": 0, "unresolved": 0},
            task_status="success",
        )

    batch_summary = run_rtllm_batch(
        RTLLMBatchConfig(benchmark_root=tmp_path, out_dir=tmp_path / "out", resume=True),
        task_runner=fake_runner,
    )

    assert executed == ["task_b"]
    assert batch_summary["aggregate_metrics"]["resumed_tasks"] == 1
    tasks = {item["task_name"]: item for item in batch_summary["tasks"]}
    assert tasks["task_a"]["resumed_from_cache"] is True


def test_run_rtllm_batch_supports_parallel_jobs(tmp_path: Path) -> None:
    for name in ("task_a", "task_b", "task_c"):
        task_dir = tmp_path / name
        task_dir.mkdir()
        (task_dir / f"verified_{name}.v").write_text("module m; endmodule", encoding="utf-8")
        (task_dir / "design_description.txt").write_text(f"{name} spec", encoding="utf-8")

    def fake_runner(task_input, config, task_out_dir):  # noqa: ANN001
        return RTLLMTaskSummary(
            task_name=task_input.task_name,
            task_dir=str(task_input.task_dir),
            artifact_root=str(task_out_dir),
            rtl_sources=[str(path) for path in task_input.rtl_sources],
            spec_present=True,
            plan_generation_mode=config.generation_mode.value,
            oracle_generation_mode=config.generation_mode.value,
            contract_success=True,
            plan_success=True,
            oracle_success=True,
            render_success=True,
            rendered_test_modules=[f"test_{task_input.task_name}_basic"],
            test_module_results=[
                RTLLMModuleRunResult(
                    test_module=f"test_{task_input.task_name}_basic",
                    run_status="success",
                    triage_category="no_failure",
                    passed_tests_count=1,
                    failed_tests_count=0,
                    return_code=0,
                    run_dir=str(task_out_dir / "run"),
                    triage_dir=str(task_out_dir / "triage"),
                )
            ],
            assertion_strength_counts={"exact": 1, "guarded": 0, "unresolved": 0},
            task_status="success",
        )

    batch_summary = run_rtllm_batch(
        RTLLMBatchConfig(benchmark_root=tmp_path, out_dir=tmp_path / "out", jobs=2),
        task_runner=fake_runner,
    )

    assert batch_summary["batch_execution_policy"]["jobs"] == 2
    assert [task["task_name"] for task in batch_summary["tasks"]] == ["task_a", "task_b", "task_c"]
    summary_payload = json.loads((tmp_path / "out" / "summary.json").read_text(encoding="utf-8"))
    assert summary_payload["batch_execution_policy"]["jobs"] == 2
