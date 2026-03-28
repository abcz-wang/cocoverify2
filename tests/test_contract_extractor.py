"""Contract extraction tests for Phase 1."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from cocoverify2.stages.contract_extractor import ContractExtractor

_FIXTURES = Path(__file__).parent / "fixtures"
_RTL = _FIXTURES / "rtl"
_GOLDEN = _FIXTURES / "golden"
_SRC = Path(__file__).resolve().parents[1] / "src"


def test_simple_seq_detects_clock_reset_and_artifacts(tmp_path: Path) -> None:
    extractor = ContractExtractor()
    contract = extractor.run(
        rtl_paths=[_RTL / "simple_seq.v"],
        task_description="Sequential register with asynchronous active low reset.",
        spec_text="The rst_n signal is an active low reset.",
        golden_interface_text=(_GOLDEN / "simple_interface.txt").read_text(encoding="utf-8"),
        out_dir=tmp_path,
    )

    assert contract.module_name == "simple_seq"
    assert [clock.name for clock in contract.clocks] == ["clk"]
    assert [reset.name for reset in contract.resets] == ["rst_n"]
    assert contract.resets[0].active_level == 0
    assert contract.timing.sequential_kind == "seq"
    assert (tmp_path / "contract" / "contract.json").exists()
    assert (tmp_path / "contract" / "contract_summary.yaml").exists()

    payload = json.loads((tmp_path / "contract" / "contract.json").read_text(encoding="utf-8"))
    assert payload["module_name"] == "simple_seq"
    assert payload["rtl_sources"] == [str(_RTL / "simple_seq.v")]
    assert payload["source_map"]["clocks.clk"]
    assert payload["handshake_groups"] == []


def test_valid_ready_detection_and_observable_outputs(tmp_path: Path) -> None:
    contract = ContractExtractor().run(
        rtl_paths=[_RTL / "valid_ready.v"],
        task_description=None,
        spec_text=None,
        golden_interface_text=None,
        out_dir=tmp_path,
    )

    assert set(contract.handshake_signals) >= {"in_valid", "in_ready", "out_valid", "out_ready", "start", "done"}
    assert set(contract.observable_outputs) >= {"in_ready", "out_valid", "out_data", "done"}
    assert any(clock.name == "aclk" for clock in contract.clocks)
    assert any(reset.name == "aresetn" and reset.active_level == 0 for reset in contract.resets)
    assert {group.pattern for group in contract.handshake_groups} >= {"valid_ready", "start_done"}
    valid_ready_groups = [group for group in contract.handshake_groups if group.pattern == "valid_ready"]
    assert {group.group_name for group in valid_ready_groups} == {"in", "out"}


def test_valid_ready_timing_prefers_unknown_over_comb_when_control_interface_exists(tmp_path: Path) -> None:
    contract = ContractExtractor().run(
        rtl_paths=[_RTL / "valid_ready.v"],
        task_description=None,
        spec_text=None,
        golden_interface_text=None,
        out_dir=tmp_path,
    )

    assert contract.timing.sequential_kind == "unknown"
    assert contract.timing.source == "rtl_heuristic"
    assert any("handshake interface" in item or "clock/reset" in item for item in contract.ambiguities)


def test_partial_parse_still_generates_contract_with_ambiguities(tmp_path: Path) -> None:
    contract = ContractExtractor().run(
        rtl_paths=[_RTL / "legacy_non_ansi.v"],
        task_description=None,
        spec_text=None,
        golden_interface_text=None,
        out_dir=tmp_path,
    )

    assert contract.module_name == "legacy_non_ansi"
    assert contract.ambiguities
    assert contract.extraction_warnings
    payload = json.loads((tmp_path / "contract" / "contract.json").read_text(encoding="utf-8"))
    assert payload["ambiguities"]
    assert payload["extraction_warnings"]


def test_legacy_non_ansi_confidence_is_downgraded(tmp_path: Path) -> None:
    contract = ContractExtractor().run(
        rtl_paths=[_RTL / "legacy_non_ansi.v"],
        task_description=None,
        spec_text=None,
        golden_interface_text=None,
        out_dir=tmp_path,
    )

    assert contract.contract_confidence <= 0.35
    assert contract.timing.sequential_kind == "unknown"
    assert contract.observable_outputs == []


def test_stage_contract_cli_smoke(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cocoverify2.cli",
            "stage",
            "contract",
            "--rtl",
            str(_RTL / "simple_comb.v"),
            "--out-dir",
            str(tmp_path),
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
    assert "Contract extracted for module 'simple_comb'" in result.stdout
    assert (tmp_path / "contract" / "contract.json").exists()
