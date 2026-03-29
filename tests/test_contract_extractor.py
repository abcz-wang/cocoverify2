"""Contract extraction tests for Phase 1."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from cocoverify2.stages.contract_extractor import ContractExtractor
from cocoverify2.utils.spec_hints import extract_interface_hint_text

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


def test_legacy_non_ansi_recovers_body_port_declarations(tmp_path: Path) -> None:
    contract = ContractExtractor().run(
        rtl_paths=[_RTL / "legacy_non_ansi.v"],
        task_description=None,
        spec_text=None,
        golden_interface_text=None,
        out_dir=tmp_path,
    )

    directions = {port.name: port.direction for port in contract.ports}
    assert directions == {"clk": "input", "rst_n": "input", "data": "input", "done": "output"}
    assert contract.observable_outputs == ["done"]
    assert any(port.source == "rtl_body_declaration" for port in contract.ports if port.name == "done")
    assert contract.contract_confidence >= 0.3
    assert contract.timing.sequential_kind == "unknown"


def test_mixed_clock_reset_line_does_not_cross_classify_clk_as_reset(tmp_path: Path) -> None:
    spec_text = "Signals clk and rst_n provide the clock and active-low reset respectively."
    contract = ContractExtractor().run(
        rtl_paths=[_RTL / "simple_seq.v"],
        task_description="Sequential register with clk and rst_n.",
        spec_text=spec_text,
        golden_interface_text=None,
        out_dir=tmp_path,
    )

    assert [clock.name for clock in contract.clocks] == ["clk"]
    assert [reset.name for reset in contract.resets] == ["rst_n"]


def test_spec_text_does_not_promote_outputs_into_clock_or_reset_roles(tmp_path: Path) -> None:
    rtl_path = tmp_path / "calendar_like.v"
    rtl_path.write_text(
        "\n".join(
            [
                "module verified_calendar(CLK, RST, Hours, Mins, Secs);",
                "input CLK;",
                "input RST;",
                "output [5:0] Hours;",
                "output [5:0] Mins;",
                "output [5:0] Secs;",
                "endmodule",
            ]
        ),
        encoding="utf-8",
    )
    spec_text = """
Module name:
    calendar

Input ports:
    CLK: Clock input
    RST: Active high reset signal

Output ports:
    Hours: 6-bit output representing the current hours
    Mins: 6-bit output representing the current minutes
    Secs: 6-bit output representing the current seconds

Implementation:
The third always block triggers on the positive edge of the clock signal or the positive edge of the reset signal.
It handles the hours value (Hours) and keeps the minutes value (Mins) unchanged otherwise.
""".strip()

    contract = ContractExtractor().run(
        rtl_paths=[rtl_path],
        task_description=None,
        spec_text=spec_text,
        golden_interface_text=extract_interface_hint_text(spec_text),
        out_dir=tmp_path / "out",
    )

    assert [clock.name for clock in contract.clocks] == ["CLK"]
    assert [reset.name for reset in contract.resets] == ["RST"]
    assert "Hours" not in {clock.name for clock in contract.clocks}
    assert "Hours" not in {reset.name for reset in contract.resets}
    assert "Mins" not in {clock.name for clock in contract.clocks}
    assert "Mins" not in {reset.name for reset in contract.resets}


def test_vector_frequency_input_is_not_promoted_to_clock(tmp_path: Path) -> None:
    rtl_path = tmp_path / "square_wave_like.v"
    rtl_path.write_text(
        "\n".join(
            [
                "module square_wave(clk, freq, wave_out);",
                "input clk;",
                "input [7:0] freq;",
                "output reg wave_out;",
                "endmodule",
            ]
        ),
        encoding="utf-8",
    )
    spec_text = """
Module name:
    square_wave

Input ports:
    clk: clock input
    freq: 8-bit divider frequency input

Output ports:
    wave_out: square wave output

Implementation:
The output toggles according to the clock and the requested frequency.
""".strip()

    contract = ContractExtractor().run(
        rtl_paths=[rtl_path],
        task_description=None,
        spec_text=spec_text,
        golden_interface_text=extract_interface_hint_text(spec_text),
        out_dir=tmp_path / "out",
    )

    assert [clock.name for clock in contract.clocks] == ["clk"]
    assert "freq" not in {clock.name for clock in contract.clocks}


def test_interface_hint_extraction_feeds_contract_without_reusing_full_spec(tmp_path: Path) -> None:
    spec_text = """
Module name:
    simple_seq

Input ports:
    clk: clock signal
    rst_n: active low reset signal
    d: data input

Output ports:
    q: registered output

Implementation:
The register captures d on the rising edge of clk.
""".strip()
    interface_hint_text = extract_interface_hint_text(spec_text)
    contract = ContractExtractor().run(
        rtl_paths=[_RTL / "simple_seq.v"],
        task_description=None,
        spec_text=spec_text,
        golden_interface_text=interface_hint_text,
        out_dir=tmp_path,
    )

    assert interface_hint_text is not None
    assert "Implementation" not in interface_hint_text
    assert "golden_interface" in contract.source_map["ports.clk"]
    assert "spec_hint" in contract.source_map["resets.rst_n"]


def test_spec_output_behavior_lines_are_preserved_as_assumptions(tmp_path: Path) -> None:
    rtl_path = tmp_path / "alu_like.v"
    rtl_path.write_text(
        "\n".join(
            [
                "module alu_like(a, b, aluc, r, zero, flag);",
                "input [31:0] a;",
                "input [31:0] b;",
                "input [5:0] aluc;",
                "output [31:0] r;",
                "output zero;",
                "output flag;",
                "endmodule",
            ]
        ),
        encoding="utf-8",
    )
    spec_text = """
Module name:
    alu

Input ports:
    a: operand
    b: operand
    aluc: opcode

Output ports:
    r: result output
    zero: zero flag
    flag: comparison flag

Implementation:
The output result (r) is assigned to the lower 32 bits of the register.
The zero output is set to '1' when the result is all zeros, and '0' otherwise.
The flag output is determined by the control signal and is set to '1' for SLT and 'z' otherwise.
""".strip()
    contract = ContractExtractor().run(
        rtl_paths=[rtl_path],
        task_description=None,
        spec_text=spec_text,
        golden_interface_text=extract_interface_hint_text(spec_text),
        out_dir=tmp_path / "out",
    )

    assumptions_text = "\n".join(contract.assumptions)
    assert "lower 32 bits" in assumptions_text
    assert "zero output is set" in assumptions_text.lower()
    assert "flag output is determined" in assumptions_text.lower()


def test_ansi_ports_with_tabs_parse_without_placeholder_names(tmp_path: Path) -> None:
    rtl_path = tmp_path / "tabbed_ports.v"
    rtl_path.write_text(
        "module demo(\n\tinput\tclk,\n\tinput\t\t[3:0]\tdata_in,\n\toutput reg [3:0]\tdata_out\n);\nendmodule\n",
        encoding="utf-8",
    )

    contract = ContractExtractor().run(
        rtl_paths=[rtl_path],
        task_description=None,
        spec_text=None,
        golden_interface_text=None,
        out_dir=tmp_path / "out",
    )

    assert [port.name for port in contract.ports] == ["clk", "data_in", "data_out"]


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
