"""TODO fill stage tests for Phase 4.5."""

from __future__ import annotations

import json
import py_compile
from pathlib import Path

from cocoverify2.core.config import LLMConfig
from cocoverify2.core.models import LLMTodoBlock, SimulationConfig
from cocoverify2.stages.contract_extractor import ContractExtractor
from cocoverify2.stages.oracle_generator import OracleGenerator
from cocoverify2.stages.simulator_runner import SimulatorRunnerStage, load_render_metadata_artifact
from cocoverify2.stages.tb_renderer import TBRenderer
from cocoverify2.stages.test_plan_generator import TestPlanGenerator
from cocoverify2.stages.todo_fill import TodoFillStage, _replace_todo_block_content

_FIXTURES = Path(__file__).parent / "fixtures"
_RTL = _FIXTURES / "rtl"


class _BlockAwareLLMClient:
    def __init__(self, *, broken_once_block: str = "", invalid_block: str = "") -> None:
        self.broken_once_block = broken_once_block
        self.invalid_block = invalid_block
        self.calls: dict[str, int] = {}

    def complete(self, *, system_prompt: str, user_prompt: str) -> str:
        assert system_prompt
        payload = json.loads(user_prompt)
        block = payload["target_block"]
        block_id = block["block_id"]
        self.calls[block_id] = self.calls.get(block_id, 0) + 1
        attempt = self.calls[block_id]

        if block_id == self.invalid_block:
            return "not json"
        if block_id == self.broken_once_block and attempt == 1:
            return json.dumps(
                {
                    "block_id": block_id,
                    "code_lines": ["await self.drive_inputs("],
                    "helper_calls": ["drive_inputs"],
                    "assumptions": [],
                    "unresolved_items": [],
                }
            )

        if block["fill_kind"] == "stimulus":
            case_id = block["case_id"]
            signals = {"a": 1, "b": 1} if case_id == "basic_001" else {"a": 0, "b": 1}
            return json.dumps(
                {
                    "block_id": block_id,
                    "code_lines": [
                        f"signals = {signals!r}",
                        "await self.drive_inputs(**signals)",
                        f"self.record_case_inputs({case_id!r}, signals)",
                        "await self.wait_for_settle()",
                    ],
                    "helper_calls": ["drive_inputs", "record_case_inputs", "wait_for_settle"],
                    "assumptions": [],
                    "unresolved_items": [],
                }
            )

        check_id = block["check_id"]
        if "functional" in check_id:
            return json.dumps(
                {
                    "block_id": block_id,
                    "code_lines": [
                        "inputs = env.get_case_inputs(plan_case_id)",
                        "outputs = await env.sample_outputs(observed_signals)",
                        "expected_y = int(inputs['a']) & int(inputs['b'])",
                        "assert_equal('y', outputs['y'], expected_y)",
                    ],
                    "helper_calls": ["get_case_inputs", "sample_outputs", "assert_equal"],
                    "assumptions": [],
                    "unresolved_items": [],
                }
            )
        return json.dumps(
            {
                "block_id": block_id,
                "code_lines": [
                    "outputs = await env.sample_outputs(observed_signals)",
                    "assert_true('y' in outputs, 'Expected y to remain observable.')",
                ],
                "helper_calls": ["sample_outputs", "assert_true"],
                "assumptions": [],
                "unresolved_items": [],
            }
        )


def _build_render_metadata(tmp_path: Path, rtl_name: str = "simple_comb.v") -> Path:
    root = tmp_path / rtl_name.removesuffix(".v")
    contract = ContractExtractor().run(
        rtl_paths=[_RTL / rtl_name],
        task_description=None,
        spec_text=None,
        golden_interface_text=None,
        out_dir=root,
    )
    TestPlanGenerator().run(
        contract=contract,
        task_description=None,
        spec_text=None,
        out_dir=root,
        based_on_contract=str(root / "contract" / "contract.json"),
    )
    OracleGenerator().run_from_artifacts(
        contract_path=root / "contract" / "contract.json",
        plan_path=root / "plan" / "test_plan.json",
        task_description=None,
        spec_text=None,
        out_dir=root,
    )
    TBRenderer().run_from_artifacts(
        contract_path=root / "contract" / "contract.json",
        plan_path=root / "plan" / "test_plan.json",
        oracle_path=root / "oracle" / "oracle.json",
        task_description=None,
        spec_text=None,
        out_dir=root,
    )
    return root / "render" / "metadata.json"


def _compile_generated_python(package_dir: Path) -> None:
    for path in package_dir.glob("*.py"):
        py_compile.compile(str(path), doraise=True)


def test_replace_todo_block_only_updates_target_body() -> None:
    original = "\n".join(
        [
            "def demo():",
            "    # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_001 case_id=basic_001",
            "    # comment",
            "    pass",
            "    # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_001 case_id=basic_001",
            "    value = 1",
            "",
        ]
    )
    updated = _replace_todo_block_content(
        original,
        LLMTodoBlock(
            block_id="stimulus_basic_001",
            fill_kind="stimulus",
            start_marker="    # TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_001 case_id=basic_001",
            end_marker="    # TODO(cocoverify2:stimulus) END block_id=stimulus_basic_001 case_id=basic_001",
        ),
        ["signals = {'a': 1}", "await self.drive_inputs(**signals)"],
    )
    assert "await self.drive_inputs(**signals)" in updated
    assert "value = 1" in updated
    assert updated.count("BEGIN block_id=stimulus_basic_001") == 1
    assert updated.count("END block_id=stimulus_basic_001") == 1


def test_fill_stage_writes_filled_metadata_and_compiles(tmp_path: Path) -> None:
    render_path = _build_render_metadata(tmp_path)
    stage = TodoFillStage(llm_client=_BlockAwareLLMClient())
    report = stage.run_from_artifact(
        render_metadata_path=render_path,
        out_dir=render_path.parent.parent,
        llm_config=LLMConfig(),
        task_description="simple comb demo",
        spec_text="simple_comb computes y = a & b.",
    )

    fill_metadata_path = render_path.parent.parent / "fill" / "metadata.json"
    fill_metadata = load_render_metadata_artifact(fill_metadata_path)
    env_text = (render_path.parent.parent / "fill" / "cocotb_tests" / "simple_comb_env.py").read_text(encoding="utf-8")
    oracle_text = (render_path.parent.parent / "fill" / "cocotb_tests" / "simple_comb_oracle.py").read_text(encoding="utf-8")

    assert report.fill_status == "success"
    assert report.compile_ok is True
    assert fill_metadata.artifact_stage == "fill"
    assert fill_metadata.fill_status == "success"
    assert set(fill_metadata.filled_todo_block_ids) >= {"stimulus_basic_001", "stimulus_edge_001"}
    assert "await self.drive_inputs(**signals)" in env_text
    assert "assert_equal('y', outputs['y'], expected_y)" in oracle_text
    _compile_generated_python(render_path.parent.parent / "fill" / "cocotb_tests")


def test_fill_stage_repairs_one_block_after_compile_error(tmp_path: Path) -> None:
    render_path = _build_render_metadata(tmp_path)
    client = _BlockAwareLLMClient(broken_once_block="stimulus_basic_001")
    report = TodoFillStage(llm_client=client).run_from_artifact(
        render_metadata_path=render_path,
        out_dir=render_path.parent.parent,
        llm_config=LLMConfig(),
        task_description="simple comb demo",
        spec_text="simple_comb computes y = a & b.",
    )

    assert report.fill_status == "success"
    assert "stimulus_basic_001" in report.repaired_block_ids
    assert client.calls["stimulus_basic_001"] == 2


def test_fill_stage_fails_closed_when_critical_block_is_not_filled(tmp_path: Path) -> None:
    render_path = _build_render_metadata(tmp_path)
    report = TodoFillStage(llm_client=_BlockAwareLLMClient(invalid_block="oracle_basic_001_functional_001")).run_from_artifact(
        render_metadata_path=render_path,
        out_dir=render_path.parent.parent,
        llm_config=LLMConfig(),
        task_description="simple comb demo",
        spec_text="simple_comb computes y = a & b.",
    )

    fill_metadata = load_render_metadata_artifact(render_path.parent.parent / "fill" / "metadata.json")
    assert report.fill_status == "failed"
    assert "oracle_basic_001_functional_001" in report.failed_block_ids
    assert fill_metadata.fill_status == "failed"


def test_render_fill_run_detects_incorrect_simple_comb(tmp_path: Path) -> None:
    render_path = _build_render_metadata(tmp_path)
    fill_root = render_path.parent.parent
    report = TodoFillStage(llm_client=_BlockAwareLLMClient()).run_from_artifact(
        render_metadata_path=render_path,
        out_dir=fill_root,
        llm_config=LLMConfig(),
        task_description="simple comb demo",
        spec_text="simple_comb computes y = a & b.",
    )
    assert report.fill_status == "success"

    fill_metadata_path = fill_root / "fill" / "metadata.json"
    stage = SimulatorRunnerStage()
    good_result = stage.run_from_artifact(
        render_metadata_path=fill_metadata_path,
        config=SimulationConfig(mode="make", rtl_sources=[_RTL / "simple_comb.v"], test_module="test_simple_comb_basic"),
        out_dir=tmp_path / "run_good",
    )

    bad_rtl = tmp_path / "bad_simple_comb.v"
    bad_rtl.write_text(
        "\n".join(
            [
                "module simple_comb (",
                "    input a,",
                "    input b,",
                "    output y",
                ");",
                "    assign y = 1'b0;",
                "endmodule",
                "",
            ]
        ),
        encoding="utf-8",
    )
    bad_result = stage.run_from_artifact(
        render_metadata_path=fill_metadata_path,
        config=SimulationConfig(mode="make", rtl_sources=[bad_rtl], test_module="test_simple_comb_basic"),
        out_dir=tmp_path / "run_bad",
    )

    assert good_result.status == "success"
    assert good_result.failed_tests == []
    assert bad_result.status != "success" or bad_result.failed_tests
