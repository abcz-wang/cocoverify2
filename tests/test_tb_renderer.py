"""Testbench rendering tests for Phase 4."""

from __future__ import annotations

import asyncio
import importlib
import json
import os
import py_compile
import pytest
import subprocess
import sys
import uuid
from pathlib import Path

from cocoverify2.cocotbgen.oracle import render_oracle_module
from cocoverify2.cocotbgen.runtime_helpers import render_runtime_helpers_module
from cocoverify2.cocotbgen.env import _build_deterministic_stimulus_steps
from cocoverify2.core.models import DUTContract, OracleCase, OracleCheck, OracleSpec, PortSpec, SignalAssertionPolicy, TemporalWindow, TestCasePlan, TimingSpec
from cocoverify2.core.types import AssertionStrength, DefinednessMode, OracleCheckType, OracleStrictness, PortDirection, SequentialKind, TemporalWindowMode, TestCategory
from cocoverify2.stages.contract_extractor import ContractExtractor
from cocoverify2.stages.oracle_generator import OracleGenerator
from cocoverify2.stages.tb_renderer import TBRenderer
from cocoverify2.stages.test_plan_generator import TestPlanGenerator

_FIXTURES = Path(__file__).parent / "fixtures"
_RTL = _FIXTURES / "rtl"
_SRC = Path(__file__).resolve().parents[1] / "src"


def _build_phase4_inputs(tmp_path: Path, rtl_name: str) -> tuple[Path, Path, Path]:
    stem = rtl_name.removesuffix(".v")
    artifact_root = tmp_path / f"artifacts_{stem}"
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
    return (
        artifact_root / "contract" / "contract.json",
        artifact_root / "plan" / "test_plan.json",
        artifact_root / "oracle" / "oracle.json",
    )


def _render_fixture(tmp_path: Path, rtl_name: str):
    contract_path, plan_path, oracle_path = _build_phase4_inputs(tmp_path, rtl_name)
    render_root = tmp_path / f"render_{rtl_name.removesuffix('.v')}"
    metadata = TBRenderer().run_from_artifacts(
        contract_path=contract_path,
        plan_path=plan_path,
        oracle_path=oracle_path,
        task_description=None,
        spec_text=None,
        out_dir=render_root,
    )
    package_dir = render_root / "render" / "cocotb_tests"
    return metadata, render_root, package_dir


def _compile_generated_python(package_dir: Path) -> None:
    for path in package_dir.glob("*.py"):
        py_compile.compile(str(path), doraise=True)


class _FakeCoverage:
    def __init__(self) -> None:
        self.records: list[tuple[str, str, str]] = []

    def record_oracle_check(self, check_id: str, check_type: str, strictness: str) -> None:
        self.records.append((check_id, check_type, strictness))


class _FakeEnv:
    def __init__(
        self,
        *,
        samples: list[dict[str, object]],
        widths: dict[str, int | None],
        case_inputs: dict[str, dict[str, object]],
        stimulus_history: dict[str, list[dict[str, object]]] | None = None,
        observation_history: dict[str, list[dict[str, object]]] | None = None,
    ) -> None:
        self._samples = list(samples)
        self._index = 0
        self._widths = dict(widths)
        self._case_inputs = dict(case_inputs)
        self._stimulus_history = dict(stimulus_history or {})
        self._observation_history = dict(observation_history or {})
        self.coverage = _FakeCoverage()
        self.oracle_results: list[dict[str, object]] = []

    async def wait_for_window(self, temporal_window: dict[str, object], label: str = "window") -> None:
        return None

    async def wait_event_based(self, label: str = "event_based") -> None:
        if self._index < len(self._samples) - 1:
            self._index += 1

    async def sample_outputs(self, names=None) -> dict[str, object]:
        sample = self._samples[min(self._index, len(self._samples) - 1)]
        selected = list(names or sample.keys())
        return {name: sample.get(name) for name in selected}

    def get_case_inputs(self, case_id: str) -> dict[str, object]:
        return dict(self._case_inputs.get(case_id, {}))

    def get_case_stimulus_history(self, case_id: str) -> list[dict[str, object]]:
        return [dict(step) for step in self._stimulus_history.get(case_id, [])]

    def get_case_observation_history(self, case_id: str) -> list[dict[str, object]]:
        return [dict(item) for item in self._observation_history.get(case_id, [])]

    def signal_width(self, signal_name: str) -> int | None:
        return self._widths.get(signal_name)

    def note_oracle_result(self, result: dict[str, object]) -> None:
        self.oracle_results.append(dict(result))


def _render_runtime_test_package(
    tmp_path: Path,
    *,
    module_name: str,
    check: OracleCheck,
    observed_widths: dict[str, int | None],
) -> object:
    package_name = f"rendered_oracle_{uuid.uuid4().hex[:8]}"
    package_dir = tmp_path / package_name
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "__init__.py").write_text("", encoding="utf-8")

    contract = DUTContract(
        module_name=module_name,
        ports=[
            PortSpec(name="in_data", direction=PortDirection.INPUT, width=1),
            *[
                PortSpec(name=signal_name, direction=PortDirection.OUTPUT, width=width or 1)
                for signal_name, width in observed_widths.items()
            ],
        ],
        observable_outputs=list(observed_widths),
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.7),
        contract_confidence=0.8,
    )
    oracle = OracleSpec(
        module_name=module_name,
        oracle_strategy="rule_based",
        functional_oracles=[
            OracleCase(
                case_id="functional_basic_001",
                linked_plan_case_id="basic_001",
                category=TestCategory.BASIC,
                checks=[check],
                confidence=0.8,
                source="hybrid_llm_enriched",
            )
        ],
    )

    runtime_content, _ = render_runtime_helpers_module(module_name)
    oracle_content, _ = render_oracle_module(contract, oracle, runtime_module=f"{module_name}_runtime")
    (package_dir / f"{module_name}_runtime.py").write_text(runtime_content, encoding="utf-8")
    (package_dir / f"{module_name}_oracle.py").write_text(oracle_content, encoding="utf-8")

    sys.path.insert(0, str(tmp_path))
    try:
        return importlib.import_module(f"{package_name}.{module_name}_oracle")
    finally:
        sys.path.remove(str(tmp_path))


def test_simple_comb_renders_basic_and_edge_without_protocol_file(tmp_path: Path) -> None:
    metadata, render_root, package_dir = _render_fixture(tmp_path, "simple_comb.v")
    env_text = (package_dir / "simple_comb_env.py").read_text(encoding="utf-8")
    oracle_text = (package_dir / "simple_comb_oracle.py").read_text(encoding="utf-8")
    basic_text = (package_dir / "test_simple_comb_basic.py").read_text(encoding="utf-8")

    assert (package_dir / "test_simple_comb_basic.py").exists()
    assert (package_dir / "test_simple_comb_edge.py").exists()
    assert not (package_dir / "test_simple_comb_protocol.py").exists()
    assert (package_dir / "simple_comb_interface.py").exists()
    assert metadata.interface_summary["clock_signals"] == []
    assert metadata.interface_summary["reset_signals"] == []
    assert "clk" not in metadata.interface_summary["business_inputs"]
    assert "rst" not in metadata.interface_summary["business_inputs"]
    payload = json.loads((render_root / "render" / "metadata.json").read_text(encoding="utf-8"))
    assert set(payload["template_inventory"]) == {
        "env_module.py.tmpl",
        "oracle_module.py.tmpl",
        "test_case.py.tmpl",
        "test_module.py.tmpl",
    }
    assert payload["fill_status"] == "experimental_available"
    assert payload["unfilled_todo_block_ids"] == []
    assert any("experimental" in item.lower() for item in payload["fill_warnings"])
    assert set(payload["test_modules"]) == {"test_simple_comb_basic", "test_simple_comb_edge"}
    assert "# TODO(cocoverify2:stimulus) BEGIN block_id=stimulus_basic_001 case_id=basic_001" in env_text
    assert "_apply_deterministic_case" in env_text
    assert "# TODO(cocoverify2:oracle_check) BEGIN block_id=oracle_basic_001_functional_001 case_id=basic_001 oracle_case_id=functional_basic_001 check_id=basic_001_functional_001" in oracle_text
    assert "# TODO(cocoverify2:testcase_setup) BEGIN block_id=testcase_setup_basic_001 case_id=basic_001" in basic_text
    assert "_apply_structured_signal_policy" in oracle_text
    assert "definedness_mode" in oracle_text
    _compile_generated_python(package_dir)


def test_render_metadata_tracks_llm_todo_blocks_and_template_names(tmp_path: Path) -> None:
    metadata, render_root, package_dir = _render_fixture(tmp_path, "simple_comb.v")

    payload = json.loads((render_root / "render" / "metadata.json").read_text(encoding="utf-8"))
    todo_blocks = payload["llm_todo_blocks"]
    stimulus_blocks = [block for block in todo_blocks if block["fill_kind"] == "stimulus"]
    oracle_blocks = [block for block in todo_blocks if block["fill_kind"] == "oracle_check"]
    setup_blocks = [block for block in todo_blocks if block["fill_kind"] == "testcase_setup"]
    generated_files = {item["relative_path"]: item for item in payload["generated_files"]}

    assert len(stimulus_blocks) == 2
    assert {block["case_id"] for block in stimulus_blocks} == {"basic_001", "edge_001"}
    assert all("stimulus_signals" in block["context"] for block in stimulus_blocks)
    assert all("semantic_tags" in block["context"] for block in stimulus_blocks)
    assert len(setup_blocks) == 2
    assert {block["block_id"] for block in setup_blocks} == {"testcase_setup_basic_001", "testcase_setup_edge_001"}
    assert all("semantic_tags" in block["context"] for block in setup_blocks)
    assert oracle_blocks
    assert all(block["check_id"] for block in oracle_blocks)
    assert all("semantic_tags" in block["context"] for block in oracle_blocks)
    assert all("signal_policies" in block["context"] for block in oracle_blocks)
    assert all("definedness_mode" in next(iter(block["context"]["signal_policies"].values())) for block in oracle_blocks if block["context"]["signal_policies"])
    assert all(block["relative_path"].startswith("cocotb_tests/") for block in todo_blocks)
    assert generated_files["cocotb_tests/simple_comb_env.py"]["template_name"] == "env_module.py.tmpl"
    assert generated_files["cocotb_tests/simple_comb_oracle.py"]["template_name"] == "oracle_module.py.tmpl"
    assert generated_files["cocotb_tests/test_simple_comb_basic.py"]["template_name"] == "test_module.py.tmpl"
    assert generated_files["cocotb_tests/simple_comb_env.py"]["todo_block_ids"] == ["stimulus_basic_001", "stimulus_edge_001"]
    assert generated_files["cocotb_tests/test_simple_comb_basic.py"]["todo_block_ids"] == ["testcase_setup_basic_001"]
    assert "_apply_structured_semantic_check" in (package_dir / "simple_comb_oracle.py").read_text(encoding="utf-8")
    _compile_generated_python(package_dir)


def test_simple_seq_renders_reset_helpers_without_exact_cycle_default(tmp_path: Path) -> None:
    metadata, _, package_dir = _render_fixture(tmp_path, "simple_seq.v")

    env_text = (package_dir / "simple_seq_env.py").read_text(encoding="utf-8")
    oracle_text = (package_dir / "simple_seq_oracle.py").read_text(encoding="utf-8")
    assert (package_dir / "test_simple_seq_basic.py").exists()
    assert "apply_reset_if_available" in env_text
    assert "_start_background_clocks" in env_text
    assert "Clock(" in env_text
    assert metadata.env_summary["has_reset_helper"] is True
    assert "wait_exact_cycle" not in env_text
    assert '"exact_cycle"' not in oracle_text
    _compile_generated_python(package_dir)


def test_multi_clock_render_uses_all_resets_and_all_clocks(tmp_path: Path) -> None:
    metadata, _, package_dir = _render_fixture(tmp_path, "multi_clock_bridge.v")

    env_text = (package_dir / "multi_clock_bridge_env.py").read_text(encoding="utf-8")
    interface_text = (package_dir / "multi_clock_bridge_interface.py").read_text(encoding="utf-8")

    assert metadata.interface_summary["clock_signals"] == ["clk_a", "clk_b"]
    assert metadata.interface_summary["reset_signals"] == ["arstn", "brstn"]
    assert "def clock_names(self) -> list[str]:" in interface_text
    assert "def reset_names(self) -> list[str]:" in interface_text
    assert "for signal_name in self.interface.reset_names()" in env_text
    assert "for signal_name in self.interface.clock_names()" in env_text
    _compile_generated_python(package_dir)


def test_valid_ready_renders_protocol_safe_modules_without_fixed_latency(tmp_path: Path) -> None:
    metadata, _, package_dir = _render_fixture(tmp_path, "valid_ready.v")

    protocol_text = (package_dir / "test_valid_ready_protocol.py").read_text(encoding="utf-8")
    oracle_text = (package_dir / "valid_ready_oracle.py").read_text(encoding="utf-8")
    interface_text = (package_dir / "valid_ready_interface.py").read_text(encoding="utf-8")

    assert (package_dir / "test_valid_ready_protocol.py").exists()
    assert "acceptance" in protocol_text.lower()
    assert "backpressure" in protocol_text.lower()
    assert "persistence" in protocol_text.lower() or "waiting" in protocol_text.lower()
    assert "ClockCycles(" not in protocol_text
    assert "wait_exact_cycle" not in protocol_text
    assert '"exact_cycle"' not in oracle_text
    assert metadata.interface_summary["protocol_signal_names"]
    assert "aclk" not in metadata.interface_summary["business_inputs"]
    assert "aresetn" not in metadata.interface_summary["business_outputs"]
    assert "BUSINESS_INPUTS" in interface_text
    _compile_generated_python(package_dir)


def test_legacy_non_ansi_renders_conservatively_and_keeps_unresolved_notes(tmp_path: Path) -> None:
    metadata, _, package_dir = _render_fixture(tmp_path, "legacy_non_ansi.v")

    interface_text = (package_dir / "legacy_non_ansi_interface.py").read_text(encoding="utf-8")
    basic_text = (package_dir / "test_legacy_non_ansi_basic.py").read_text(encoding="utf-8")

    assert metadata.render_warnings
    assert any("confidence is low" in item.lower() or "conservative" in item.lower() for item in metadata.render_warnings)
    assert metadata.oracle_summary["empty_functional_cases"]
    assert metadata.interface_summary["unknown_direction_signals"] == []
    assert "UNKNOWN_DIRECTION_SIGNALS" in interface_text
    assert "Conservative rendering" in basic_text
    assert "# Execution policy:" in basic_text
    assert metadata.render_confidence <= 0.5
    _compile_generated_python(package_dir)


def test_render_stage_writes_metadata_and_makefile(tmp_path: Path) -> None:
    metadata, render_root, package_dir = _render_fixture(tmp_path, "simple_seq.v")

    assert metadata.module_name == "simple_seq"
    assert (render_root / "render" / "metadata.json").exists()
    assert (package_dir / "Makefile").exists()
    makefile_text = (package_dir / "Makefile").read_text(encoding="utf-8")
    assert "TOPLEVEL ?= simple_seq" in makefile_text
    assert "static scaffold only" not in makefile_text
    assert "CV2_MAKEFILE_CONTRACT := executable-shell-v1" in makefile_text
    assert ".DEFAULT_GOAL := sim" in makefile_text
    assert "COCOTB_MAKEFILES_DIR ?=" in makefile_text
    assert "include $(COCOTB_MAKEFILES_DIR)/Makefile.sim" in makefile_text
    assert "VERILOG_SOURCES ?=" in makefile_text
    assert "INCLUDE_DIRS ?=" in makefile_text
    assert "DEFINE_OVERRIDES ?=" in makefile_text
    assert "PARAMETER_OVERRIDES ?=" in makefile_text
    assert "COCOTB_MAKEFILES_DIR must be provided by Phase 5 preflight" in makefile_text
    assert "VERILOG_SOURCES must be provided by Phase 5" in makefile_text
    assert not any("scaffold" in item.lower() for item in metadata.render_warnings)
    assert any("executable phase 4 shell" in item.lower() for item in metadata.render_warnings)


def test_stage_render_cli_smoke(tmp_path: Path) -> None:
    contract_path, plan_path, oracle_path = _build_phase4_inputs(tmp_path, "simple_comb.v")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cocoverify2.cli",
            "stage",
            "render",
            "--contract",
            str(contract_path),
            "--plan",
            str(plan_path),
            "--oracle",
            str(oracle_path),
            "--out-dir",
            str(tmp_path / "cli_render"),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={
            **os.environ,
            "PYTHONPATH": str(_SRC) if not os.environ.get("PYTHONPATH") else f"{_SRC}{os.pathsep}{os.environ['PYTHONPATH']}",
        },
    )

    assert result.returncode == 0, result.stderr
    assert "Render package generated for module 'simple_comb'" in result.stdout
    assert (tmp_path / "cli_render" / "render" / "metadata.json").exists()


def test_rendered_oracle_applies_eventual_high_semantics_for_exact_scalar_checks(tmp_path: Path) -> None:
    check = OracleCheck(
        check_id="basic_001_functional_002",
        check_type=OracleCheckType.FUNCTIONAL,
        description="operation-specific semantic check",
        observed_signals=["done"],
        pass_condition="done must become high in a later cycle.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED),
        strictness=OracleStrictness.CONSERVATIVE,
        signal_policies={
            "done": SignalAssertionPolicy(
                strength=AssertionStrength.EXACT,
                definedness_mode=DefinednessMode.NOT_REQUIRED,
                allow_unknown=False,
                allow_high_impedance=False,
                rationale="explicit_output_behavior",
            )
        },
        semantic_tags=["operation_specific"],
        source="hybrid_llm_generated",
        confidence=0.8,
    )
    oracle_module = _render_runtime_test_package(tmp_path, module_name="demo_eventual", check=check, observed_widths={"done": 1})
    env = _FakeEnv(samples=[{"done": 0}, {"done": 0}, {"done": 1}], widths={"done": 1}, case_inputs={"basic_001": {"in_data": 1}})

    result = asyncio.run(oracle_module._evaluate_check(env, "basic_001", "functional_basic_001", check.model_dump(mode="json")))

    assert result["semantic_status"] == "semantic_checked"
    assert result["semantic_kind"] == "eventual_level"
    assert result["semantic_details"]["matched_after_cycles"] == 2


def test_rendered_oracle_skips_complex_premise_semantics_without_failing(tmp_path: Path) -> None:
    check = OracleCheck(
        check_id="basic_001_functional_002",
        check_type=OracleCheckType.FUNCTIONAL,
        description="sequence semantic check",
        observed_signals=["sequence_detected"],
        pass_condition="Following the stimulus that drives the bitstream 1,0,0,1 on data_in, sequence_detected must become high in a later cycle.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED),
        strictness=OracleStrictness.CONSERVATIVE,
        signal_policies={
            "sequence_detected": SignalAssertionPolicy(
                strength=AssertionStrength.EXACT,
                definedness_mode=DefinednessMode.NOT_REQUIRED,
                allow_unknown=False,
                allow_high_impedance=False,
                rationale="explicit_output_behavior",
            )
        },
        semantic_tags=["operation_specific"],
        source="hybrid_llm_generated",
        confidence=0.8,
    )
    oracle_module = _render_runtime_test_package(
        tmp_path,
        module_name="demo_sequence",
        check=check,
        observed_widths={"sequence_detected": 1},
    )
    env = _FakeEnv(
        samples=[{"sequence_detected": 0}, {"sequence_detected": 0}, {"sequence_detected": 0}],
        widths={"sequence_detected": 1},
        case_inputs={"basic_001": {"data_in": 1}},
    )

    result = asyncio.run(oracle_module._evaluate_check(env, "basic_001", "functional_basic_001", check.model_dump(mode="json")))

    assert result["semantic_status"] == "semantic_skipped_complex_premise"
    assert result["semantic_kind"] == "eventual_level"


def test_rendered_oracle_applies_conditional_defined_binary_semantics(tmp_path: Path) -> None:
    check = OracleCheck(
        check_id="edge_001_property_002",
        check_type=OracleCheckType.PROPERTY,
        description="conditional binary definedness",
        observed_signals=["valid_out", "dout"],
        pass_condition="Whenever valid_out is 1, dout must be a defined binary value (0 or 1) and must not be X or Z; no timing guarantee is required.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED),
        strictness=OracleStrictness.GUARDED,
        signal_policies={
            "valid_out": SignalAssertionPolicy(
                strength=AssertionStrength.EXACT,
                definedness_mode=DefinednessMode.NOT_REQUIRED,
                allow_unknown=False,
                allow_high_impedance=False,
                rationale="explicit_output_behavior",
            ),
            "dout": SignalAssertionPolicy(
                strength=AssertionStrength.EXACT,
                definedness_mode=DefinednessMode.NOT_REQUIRED,
                allow_unknown=False,
                allow_high_impedance=False,
                rationale="explicit_output_behavior",
            ),
        },
        semantic_tags=["operation_specific", "ambiguity_preserving"],
        source="hybrid_llm_generated",
        confidence=0.75,
    )
    oracle_module = _render_runtime_test_package(
        tmp_path,
        module_name="demo_conditional",
        check=check,
        observed_widths={"valid_out": 1, "dout": 1},
    )

    good_env = _FakeEnv(
        samples=[{"valid_out": 0, "dout": "x"}, {"valid_out": 1, "dout": 1}, {"valid_out": 0, "dout": 0}],
        widths={"valid_out": 1, "dout": 1},
        case_inputs={"basic_001": {"in_data": 1}},
    )
    good_result = asyncio.run(
        oracle_module._evaluate_check(good_env, "basic_001", "functional_basic_001", check.model_dump(mode="json"))
    )
    assert good_result["semantic_status"] == "semantic_checked"
    assert good_result["semantic_kind"] == "conditional_defined_binary"
    assert good_result["semantic_details"]["activation_count"] == 1

    bad_env = _FakeEnv(
        samples=[{"valid_out": 1, "dout": "x"}],
        widths={"valid_out": 1, "dout": 1},
        case_inputs={"basic_001": {"in_data": 1}},
    )
    with pytest.raises(AssertionError, match="dout must not be unknown when valid_out=1"):
        asyncio.run(oracle_module._evaluate_check(bad_env, "basic_001", "functional_basic_001", check.model_dump(mode="json")))


def test_rendered_oracle_applies_exact_match_count_semantics(tmp_path: Path) -> None:
    check = OracleCheck(
        check_id="basic_001_functional_002",
        check_type=OracleCheckType.FUNCTIONAL,
        description="count valid output pulses",
        observed_signals=["valid_out", "dout"],
        pass_condition="After the input pattern is presented, within an unspecified number of clock cycles, exactly four cycles with valid_out=1 must be observed, each providing a dout bit.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED),
        strictness=OracleStrictness.CONSERVATIVE,
        signal_policies={
            "valid_out": SignalAssertionPolicy(
                strength=AssertionStrength.EXACT,
                definedness_mode=DefinednessMode.NOT_REQUIRED,
                allow_unknown=False,
                allow_high_impedance=False,
                rationale="explicit_output_behavior",
            ),
            "dout": SignalAssertionPolicy(
                strength=AssertionStrength.EXACT,
                definedness_mode=DefinednessMode.NOT_REQUIRED,
                allow_unknown=False,
                allow_high_impedance=False,
                rationale="explicit_output_behavior",
            ),
        },
        semantic_tags=["operation_specific", "ambiguity_preserving"],
        source="hybrid_llm_generated",
        confidence=0.8,
    )
    oracle_module = _render_runtime_test_package(
        tmp_path,
        module_name="demo_count",
        check=check,
        observed_widths={"valid_out": 1, "dout": 1},
    )
    env = _FakeEnv(
        samples=[
            {"valid_out": 0, "dout": 0},
            {"valid_out": 1, "dout": 1},
            {"valid_out": 1, "dout": 0},
            {"valid_out": 1, "dout": 1},
            {"valid_out": 1, "dout": 0},
            {"valid_out": 0, "dout": 0},
            {"valid_out": 0, "dout": 0},
        ],
        widths={"valid_out": 1, "dout": 1},
        case_inputs={"basic_001": {"in_data": 1}},
    )

    result = asyncio.run(oracle_module._evaluate_check(env, "basic_001", "functional_basic_001", check.model_dump(mode="json")))

    assert result["semantic_status"] == "semantic_checked"
    assert result["semantic_kind"] == "count_equals"
    assert result["semantic_details"]["matched_count"] == 4


def test_rendered_oracle_applies_serial_to_parallel_relation_from_stimulus_history(tmp_path: Path) -> None:
    check = OracleCheck(
        check_id="basic_001_functional_900",
        check_type=OracleCheckType.FUNCTIONAL,
        description="serial to parallel relation",
        observed_signals=["dout_parallel", "dout_valid"],
        pass_condition="After eight legal serial input bits, dout_valid must pulse exactly once and dout_parallel must equal the captured byte in the documented bit order.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED),
        strictness=OracleStrictness.CONSERVATIVE,
        relation_kind="serial_to_parallel_byte",
        comparison_operands=["din_serial", "din_valid", "dout_parallel", "dout_valid"],
        reference_domain="msb_to_lsb",
        expected_transition="eight_valid_bits_then_single_valid_pulse",
        semantic_tags=["operation_specific", "serial_history"],
        source="rule_based",
        confidence=0.85,
    )
    oracle_module = _render_runtime_test_package(
        tmp_path,
        module_name="demo_serial_relation",
        check=check,
        observed_widths={"dout_parallel": 8, "dout_valid": 1},
    )
    history = []
    for bit in [1, 0, 1, 0, 1, 0, 1, 0]:
        history.append({"action": "drive", "signals": {"din_serial": bit, "din_valid": 1}})
        history.append({"action": "wait_cycles", "cycles": 1})
    env = _FakeEnv(
        samples=[
            {"dout_parallel": 0x00, "dout_valid": 0},
            {"dout_parallel": 0x00, "dout_valid": 0},
            {"dout_parallel": 0xAA, "dout_valid": 1},
            {"dout_parallel": 0xAA, "dout_valid": 0},
        ],
        widths={"dout_parallel": 8, "dout_valid": 1},
        case_inputs={"basic_001": {"din_serial": 0, "din_valid": 0}},
        stimulus_history={"basic_001": history},
    )

    result = asyncio.run(oracle_module._evaluate_check(env, "basic_001", "functional_basic_001", check.model_dump(mode="json")))

    assert result["semantic_status"] == "semantic_checked"
    assert result["semantic_kind"] == "serial_to_parallel_byte"
    assert result["semantic_details"]["expected_value"] == 0xAA


def test_rendered_oracle_applies_byte_pack_pair_relation_from_stimulus_history(tmp_path: Path) -> None:
    check = OracleCheck(
        check_id="basic_001_functional_901",
        check_type=OracleCheckType.FUNCTIONAL,
        description="byte pack relation",
        observed_signals=["data_out", "valid_out"],
        pass_condition="After two valid input bytes, valid_out must assert and data_out must present the first byte in the high bits and the second byte in the low bits.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED),
        strictness=OracleStrictness.CONSERVATIVE,
        relation_kind="byte_pack_pair",
        comparison_operands=["data_in", "valid_in", "data_out", "valid_out"],
        reference_domain="high_byte_first",
        expected_transition="two_valid_bytes_then_output_valid",
        semantic_tags=["operation_specific", "data_packing"],
        source="rule_based",
        confidence=0.85,
    )
    oracle_module = _render_runtime_test_package(
        tmp_path,
        module_name="demo_pack_relation",
        check=check,
        observed_widths={"data_out": 16, "valid_out": 1},
    )
    env = _FakeEnv(
        samples=[
            {"data_out": 0x0000, "valid_out": 0},
            {"data_out": 0x1234, "valid_out": 1},
            {"data_out": 0x1234, "valid_out": 0},
        ],
        widths={"data_out": 16, "valid_out": 1},
        case_inputs={"basic_001": {"data_in": 0x34, "valid_in": 0}},
        stimulus_history={
            "basic_001": [
                {"action": "drive", "signals": {"valid_in": 1, "data_in": 0x12}},
                {"action": "wait_cycles", "cycles": 1},
                {"action": "drive", "signals": {"valid_in": 1, "data_in": 0x34}},
                {"action": "wait_cycles", "cycles": 1},
            ]
        },
    )

    result = asyncio.run(oracle_module._evaluate_check(env, "basic_001", "functional_basic_001", check.model_dump(mode="json")))

    assert result["semantic_status"] == "semantic_checked"
    assert result["semantic_kind"] == "byte_pack_pair"
    assert result["semantic_details"]["expected_value"] == 0x1234


def test_rendered_oracle_applies_fifo_readback_relation(tmp_path: Path) -> None:
    check = OracleCheck(
        check_id="basic_001_functional_902",
        check_type=OracleCheckType.FUNCTIONAL,
        description="fifo readback relation",
        observed_signals=["rdata", "rempty", "wfull"],
        pass_condition="A value written into the FIFO must later become observable on rdata during a legal read sequence, and rempty/wfull must remain externally consistent.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED),
        strictness=OracleStrictness.CONSERVATIVE,
        relation_kind="fifo_write_readback",
        comparison_operands=["wdata", "winc", "rinc", "rdata", "rempty", "wfull"],
        semantic_tags=["operation_specific", "fifo_relation"],
        source="rule_based",
        confidence=0.8,
    )
    oracle_module = _render_runtime_test_package(
        tmp_path,
        module_name="demo_fifo_relation",
        check=check,
        observed_widths={"rdata": 8, "rempty": 1, "wfull": 1},
    )
    env = _FakeEnv(
        samples=[
            {"rdata": 0x00, "rempty": 1, "wfull": 0},
            {"rdata": 0x00, "rempty": 0, "wfull": 0},
            {"rdata": 0xA5, "rempty": 0, "wfull": 0},
            {"rdata": 0xA5, "rempty": 1, "wfull": 0},
        ],
        widths={"rdata": 8, "rempty": 1, "wfull": 1},
        case_inputs={"basic_001": {"wdata": 0xA5}},
        stimulus_history={
            "basic_001": [
                {"action": "drive", "signals": {"winc": 1, "rinc": 0, "wdata": 0xA5}},
                {"action": "wait_cycles", "cycles": 2},
                {"action": "drive", "signals": {"winc": 0, "rinc": 1, "wdata": 0xA5}},
            ]
        },
    )

    result = asyncio.run(oracle_module._evaluate_check(env, "basic_001", "functional_basic_001", check.model_dump(mode="json")))

    assert result["semantic_status"] == "semantic_checked"
    assert result["semantic_kind"] == "fifo_write_readback"


def test_rendered_oracle_applies_unsigned_divide_relation(tmp_path: Path) -> None:
    check = OracleCheck(
        check_id="basic_001_functional_905",
        check_type=OracleCheckType.FUNCTIONAL,
        description="divide relation",
        observed_signals=["result", "odd"],
        pass_condition="result must equal A divided by B and odd must carry the zero-extended remainder for the observed inputs.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED),
        strictness=OracleStrictness.CONSERVATIVE,
        relation_kind="unsigned_divide_16_by_8",
        comparison_operands=["A", "B", "result", "odd"],
        semantic_tags=["operation_specific", "arithmetic_relation"],
        source="rule_based",
        confidence=0.8,
    )
    oracle_module = _render_runtime_test_package(
        tmp_path,
        module_name="demo_div_relation",
        check=check,
        observed_widths={"result": 16, "odd": 16},
    )
    env = _FakeEnv(
        samples=[{"result": 20, "odd": 0}],
        widths={"result": 16, "odd": 16},
        case_inputs={"basic_001": {"A": 200, "B": 10}},
    )

    result = asyncio.run(oracle_module._evaluate_check(env, "basic_001", "functional_basic_001", check.model_dump(mode="json")))

    assert result["semantic_status"] == "semantic_checked"
    assert result["semantic_kind"] == "unsigned_divide_16_by_8"
    assert result["semantic_details"]["expected_quotient"] == 20


def test_rendered_oracle_applies_fixed_point_sign_magnitude_relation(tmp_path: Path) -> None:
    check = OracleCheck(
        check_id="basic_001_functional_904",
        check_type=OracleCheckType.FUNCTIONAL,
        description="fixed point relation",
        observed_signals=["c"],
        pass_condition="Output c must equal the sign-magnitude addition/subtraction result of a and b for the observed operands.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED),
        strictness=OracleStrictness.CONSERVATIVE,
        relation_kind="fixed_point_sign_magnitude_add",
        comparison_operands=["a", "b", "c"],
        semantic_tags=["operation_specific", "arithmetic_relation"],
        source="rule_based",
        confidence=0.8,
    )
    oracle_module = _render_runtime_test_package(
        tmp_path,
        module_name="demo_fixed_point_relation",
        check=check,
        observed_widths={"c": 16},
    )
    env = _FakeEnv(
        samples=[{"c": 0x0002}],
        widths={"c": 16},
        case_inputs={"basic_001": {"a": 0x0003, "b": 0x8001}},
    )

    result = asyncio.run(oracle_module._evaluate_check(env, "basic_001", "functional_basic_001", check.model_dump(mode="json")))

    assert result["semantic_status"] == "semantic_checked"
    assert result["semantic_kind"] == "fixed_point_sign_magnitude_add"
    assert result["semantic_details"]["expected_value"] == 0x0002


def test_rendered_oracle_applies_grouped_valid_accumulation_relation(tmp_path: Path) -> None:
    check = OracleCheck(
        check_id="basic_002_functional_899",
        check_type=OracleCheckType.FUNCTIONAL,
        description="grouped valid accumulation",
        observed_signals=["valid_out", "data_out"],
        pass_condition="Before 4 accepted valid samples, valid_out remains low; after the completed group, one output event occurs and data_out equals the accumulated sum.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED),
        strictness=OracleStrictness.CONSERVATIVE,
        relation_kind="grouped_valid_accumulation",
        comparison_operands=["data_in", "valid_in", "data_out", "valid_out"],
        expected_transition="single_group_sum",
        reference_domain="group_size=4;allow_gaps=0;expected_groups=1",
        oracle_pattern=json.dumps({"group_size": 4, "allow_gaps": False, "expected_groups": 1}),
        semantic_tags=["operation_specific", "stream_grouping"],
        source="rule_based",
        confidence=0.85,
    )
    oracle_module = _render_runtime_test_package(
        tmp_path,
        module_name="demo_accu_relation",
        check=check,
        observed_widths={"valid_out": 1, "data_out": 10},
    )
    history = []
    for value in [1, 2, 3, 4]:
        history.append({"action": "drive", "signals": {"valid_in": 1, "data_in": value}})
        history.append({"action": "wait_cycles", "cycles": 1})
    history.append({"action": "drive", "signals": {"valid_in": 0, "data_in": 4}})
    history.append({"action": "wait_cycles", "cycles": 1})
    observation_history = {
        "basic_002": [
            {"step_index": 1, "action": "wait_cycles", "sampled_outputs": {"valid_out": 0, "data_out": 0}},
            {"step_index": 3, "action": "wait_cycles", "sampled_outputs": {"valid_out": 0, "data_out": 0}},
            {"step_index": 5, "action": "wait_cycles", "sampled_outputs": {"valid_out": 0, "data_out": 0}},
            {"step_index": 7, "action": "wait_cycles", "sampled_outputs": {"valid_out": 1, "data_out": 10}},
            {"step_index": 9, "action": "wait_cycles", "sampled_outputs": {"valid_out": 0, "data_out": 10}},
        ]
    }
    env = _FakeEnv(
        samples=[
            {"valid_out": 0, "data_out": 0},
            {"valid_out": 1, "data_out": 10},
            {"valid_out": 0, "data_out": 10},
        ],
        widths={"valid_out": 1, "data_out": 10},
        case_inputs={"basic_002": {"valid_in": 0, "data_in": 4}},
        stimulus_history={"basic_002": history},
        observation_history=observation_history,
    )

    result = asyncio.run(oracle_module._evaluate_check(env, "basic_002", "functional_basic_002", check.model_dump(mode="json")))

    assert result["semantic_status"] == "semantic_checked"
    assert result["semantic_kind"] == "grouped_valid_accumulation"
    assert result["semantic_details"]["expected_values"] == [10]


def test_rendered_oracle_applies_ring_counter_progression_relation(tmp_path: Path) -> None:
    check = OracleCheck(
        check_id="basic_001_functional_907",
        check_type=OracleCheckType.FUNCTIONAL,
        description="ring counter progression",
        observed_signals=["out"],
        pass_condition="The ring counter output remains one-hot and successive observed states rotate by one bit across the conservative observation window.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED),
        strictness=OracleStrictness.CONSERVATIVE,
        relation_kind="one_hot_rotation_progression",
        comparison_operands=["out"],
        oracle_pattern=json.dumps({"sample_count": 5}),
        semantic_tags=["operation_specific", "autonomous_progression"],
        source="rule_based",
        confidence=0.8,
    )
    oracle_module = _render_runtime_test_package(
        tmp_path,
        module_name="demo_ring_relation",
        check=check,
        observed_widths={"out": 8},
    )
    env = _FakeEnv(
        samples=[
            {"out": 0x01},
            {"out": 0x02},
            {"out": 0x04},
            {"out": 0x08},
            {"out": 0x10},
        ],
        widths={"out": 8},
        case_inputs={"basic_001": {}},
    )

    result = asyncio.run(oracle_module._evaluate_check(env, "basic_001", "functional_basic_001", check.model_dump(mode="json")))

    assert result["semantic_status"] == "semantic_checked"
    assert result["semantic_kind"] == "one_hot_rotation_progression"


def test_deterministic_stimulus_uses_available_inputs_for_serial_parallel_edge_case() -> None:
    contract = DUTContract(
        module_name="verified_serial2parallel",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="din_serial", direction=PortDirection.INPUT, width=1),
            PortSpec(name="din_valid", direction=PortDirection.INPUT, width=1),
            PortSpec(name="dout_parallel", direction=PortDirection.OUTPUT, width=8),
            PortSpec(name="dout_valid", direction=PortDirection.OUTPUT, width=1),
        ],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
    )
    case = TestCasePlan(
        case_id="edge_001",
        goal="Exercise width-sensitive edges.",
        category=TestCategory.EDGE,
        stimulus_intent=["Use control boundary patterns."],
        stimulus_signals=["din_valid"],
        expected_properties=["Observe externally visible progress."],
        observed_signals=["dout_parallel", "dout_valid"],
        timing_assumptions=["Conservative clocked observation."],
        coverage_tags=["edge"],
        semantic_tags=["width_sensitive"],
        confidence=0.8,
    )

    steps = _build_deterministic_stimulus_steps(contract=contract, case=case)
    drive_steps = [step for step in steps if step["action"] == "drive"]

    assert len(drive_steps) >= 9
    assert all("din_serial" in step["signals"] and "din_valid" in step["signals"] for step in drive_steps[:-1])
    assert drive_steps[-1]["signals"]["din_valid"] == 0


def test_deterministic_stimulus_ignores_weak_structured_serial_program_and_uses_richer_history() -> None:
    contract = DUTContract(
        module_name="verified_serial2parallel",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="din_serial", direction=PortDirection.INPUT, width=1),
            PortSpec(name="din_valid", direction=PortDirection.INPUT, width=1),
            PortSpec(name="dout_parallel", direction=PortDirection.OUTPUT, width=8),
            PortSpec(name="dout_valid", direction=PortDirection.OUTPUT, width=1),
        ],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
    )
    case = TestCasePlan(
        case_id="basic_001",
        goal="weak serial stimulus",
        category=TestCategory.BASIC,
        stimulus_intent=["serial transfer"],
        stimulus_signals=["din_serial", "din_valid"],
        stimulus_program=[
            {"action": "drive", "signals": {"din_serial": 0, "din_valid": 1}},
            {"action": "wait_cycles", "cycles": 8},
            {"action": "record_inputs", "signals": {"din_serial": 0, "din_valid": 1}},
        ],
        expected_properties=["Observe byte assembly."],
        observed_signals=["dout_parallel", "dout_valid"],
        timing_assumptions=["clocked"],
        coverage_tags=["basic"],
        semantic_tags=["operation_specific"],
        confidence=0.8,
    )

    steps = _build_deterministic_stimulus_steps(contract=contract, case=case)
    drive_steps = [step for step in steps if step["action"] == "drive"]

    assert len(drive_steps) >= 9
    assert drive_steps[0]["signals"] == {"din_serial": 1, "din_valid": 1}
    assert drive_steps[-1]["signals"]["din_valid"] == 0


def test_deterministic_stimulus_builds_two_byte_packing_sequence() -> None:
    contract = DUTContract(
        module_name="width_8to16",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="valid_in", direction=PortDirection.INPUT, width=1),
            PortSpec(name="data_in", direction=PortDirection.INPUT, width=8),
            PortSpec(name="valid_out", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="data_out", direction=PortDirection.OUTPUT, width=16),
        ],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
    )
    case = TestCasePlan(
        case_id="basic_001",
        goal="packing",
        category=TestCategory.BASIC,
        stimulus_intent=["present two bytes"],
        stimulus_signals=["valid_in", "data_in"],
        expected_properties=["Observe packed output."],
        observed_signals=["valid_out", "data_out"],
        timing_assumptions=["clocked"],
        coverage_tags=["basic"],
        semantic_tags=["operation_specific"],
        confidence=0.8,
    )

    steps = _build_deterministic_stimulus_steps(contract=contract, case=case)
    drive_steps = [step for step in steps if step["action"] == "drive"]

    assert drive_steps[0]["signals"] == {"valid_in": 1, "data_in": 0x12}
    assert drive_steps[1]["signals"] == {"valid_in": 1, "data_in": 0x34}
    assert drive_steps[2]["signals"] == {"valid_in": 0, "data_in": 0x34}


def test_deterministic_stimulus_uses_available_inputs_for_stack_buffer_edge_case() -> None:
    contract = DUTContract(
        module_name="LIFObuffer",
        ports=[
            PortSpec(name="Clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="Rst", direction=PortDirection.INPUT, width=1),
            PortSpec(name="dataIn", direction=PortDirection.INPUT, width=4),
            PortSpec(name="RW", direction=PortDirection.INPUT, width=1),
            PortSpec(name="EN", direction=PortDirection.INPUT, width=1),
            PortSpec(name="EMPTY", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="FULL", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="dataOut", direction=PortDirection.OUTPUT, width=4),
        ],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
    )
    case = TestCasePlan(
        case_id="edge_001",
        goal="Exercise boundary writes.",
        category=TestCategory.EDGE,
        stimulus_intent=["Use boundary data values."],
        stimulus_signals=["dataIn", "EN"],
        expected_properties=["Observe buffer status changes."],
        observed_signals=["EMPTY", "FULL", "dataOut"],
        timing_assumptions=["Conservative clocked observation."],
        coverage_tags=["edge"],
        semantic_tags=["width_sensitive"],
        confidence=0.8,
    )

    steps = _build_deterministic_stimulus_steps(contract=contract, case=case)
    drive_steps = [step for step in steps if step["action"] == "drive"]

    assert len(drive_steps) >= 2
    assert drive_steps[0]["signals"]["RW"] == 0
    assert drive_steps[1]["signals"]["RW"] == 1


def test_deterministic_stimulus_uses_tail_safe_accumulator_sequences() -> None:
    contract = DUTContract(
        module_name="accu",
        ports=[
            PortSpec(name="clk", direction=PortDirection.INPUT, width=1),
            PortSpec(name="rst_n", direction=PortDirection.INPUT, width=1),
            PortSpec(name="data_in", direction=PortDirection.INPUT, width=8),
            PortSpec(name="valid_in", direction=PortDirection.INPUT, width=1),
            PortSpec(name="valid_out", direction=PortDirection.OUTPUT, width=1),
            PortSpec(name="data_out", direction=PortDirection.OUTPUT, width=10),
        ],
        assumptions=["valid_out becomes 1 after 4 accepted accumulation samples."],
        observable_outputs=["valid_out", "data_out"],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.8),
    )
    case = TestCasePlan(
        case_id="back_to_back_001",
        goal="multi group stream",
        category=TestCategory.BACK_TO_BACK,
        stimulus_intent=["Drive grouped valid samples."],
        stimulus_signals=["data_in", "valid_in"],
        expected_properties=["Observe grouped output closure."],
        observed_signals=["valid_out", "data_out"],
        timing_assumptions=["clocked"],
        coverage_tags=["back_to_back"],
        semantic_tags=["operation_specific"],
        confidence=0.8,
    )

    steps = _build_deterministic_stimulus_steps(contract=contract, case=case)
    drive_steps = [step for step in steps if step["action"] == "drive"]
    valid_high_drives = [step for step in drive_steps if step["signals"].get("valid_in") == 1]

    assert len(valid_high_drives) >= 8
    assert drive_steps[-1]["signals"]["valid_in"] == 0


def test_deterministic_stimulus_prefers_structured_program_and_records_inputs() -> None:
    contract = DUTContract(
        module_name="demo_structured",
        ports=[
            PortSpec(name="a", direction=PortDirection.INPUT, width=8),
            PortSpec(name="b", direction=PortDirection.INPUT, width=8),
            PortSpec(name="y", direction=PortDirection.OUTPUT, width=8),
        ],
        timing=TimingSpec(sequential_kind=SequentialKind.COMB, latency_model="unknown", confidence=0.7),
    )
    case = TestCasePlan(
        case_id="edge_001",
        goal="structured",
        category=TestCategory.EDGE,
        stimulus_intent=["structured"],
        stimulus_signals=["a", "b"],
        stimulus_program=[
            {"action": "drive", "signals": {"a": 1, "b": 2, "ghost": 9}},
            {"action": "wait_cycles", "cycles": 2},
        ],
        expected_properties=["observe"],
        observed_signals=["y"],
        timing_assumptions=["settle"],
        coverage_tags=["edge"],
        semantic_tags=["width_sensitive"],
        confidence=0.8,
    )

    steps = _build_deterministic_stimulus_steps(contract=contract, case=case)

    assert steps[0] == {"action": "drive", "signals": {"a": 1, "b": 2}}
    assert steps[1] == {"action": "wait_cycles", "cycles": 2}
    assert steps[2] == {"action": "record_inputs", "signals": {"a": 1, "b": 2}}


def test_deterministic_stimulus_keeps_explicit_record_inputs_from_structured_program() -> None:
    contract = DUTContract(
        module_name="demo_structured_record",
        ports=[
            PortSpec(name="din", direction=PortDirection.INPUT, width=4),
            PortSpec(name="dout", direction=PortDirection.OUTPUT, width=4),
        ],
        timing=TimingSpec(sequential_kind=SequentialKind.SEQ, latency_model="unknown", confidence=0.7),
    )
    case = TestCasePlan(
        case_id="basic_001",
        goal="structured record",
        category=TestCategory.BASIC,
        stimulus_intent=["structured"],
        stimulus_signals=["din"],
        stimulus_program=[
            {"action": "drive", "signals": {"din": 10}},
            {"action": "record_inputs", "signals": {"din": 10}},
            {"action": "wait_cycles", "cycles": 1},
        ],
        expected_properties=["observe"],
        observed_signals=["dout"],
        timing_assumptions=["clock"],
        coverage_tags=["basic"],
        semantic_tags=["operation_specific"],
        confidence=0.8,
    )

    steps = _build_deterministic_stimulus_steps(contract=contract, case=case)

    assert steps.count({"action": "record_inputs", "signals": {"din": 10}}) == 1


def test_deterministic_stimulus_falls_back_when_structured_program_has_only_invalid_literals() -> None:
    contract = DUTContract(
        module_name="demo_structured_invalid",
        ports=[
            PortSpec(name="adda", direction=PortDirection.INPUT, width=64),
            PortSpec(name="addb", direction=PortDirection.INPUT, width=64),
            PortSpec(name="sum", direction=PortDirection.OUTPUT, width=64),
        ],
        timing=TimingSpec(sequential_kind=SequentialKind.COMB, latency_model="unknown", confidence=0.7),
    )
    case = TestCasePlan(
        case_id="basic_001",
        goal="structured invalid",
        category=TestCategory.BASIC,
        stimulus_intent=["structured"],
        stimulus_signals=["adda", "addb"],
        stimulus_program=[
            {"action": "drive", "signals": {"adda": "rand64", "addb": "random"}},
            {"action": "record_note", "text": "bad literals should not suppress deterministic fallback"},
        ],
        expected_properties=["observe"],
        observed_signals=["sum"],
        timing_assumptions=["settle"],
        coverage_tags=["basic"],
        semantic_tags=["operation_specific"],
        confidence=0.8,
    )

    steps = _build_deterministic_stimulus_steps(contract=contract, case=case)

    assert any(step["action"] == "drive" for step in steps)
    assert all("rand64" not in str(step) and "random" not in str(step) for step in steps)
    assert any(step["action"] == "record_inputs" for step in steps)
