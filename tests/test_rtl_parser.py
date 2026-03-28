"""Unit tests for the lightweight RTL parser helpers."""

from __future__ import annotations

from pathlib import Path

from cocoverify2.parsers.rtl_parser import parse_rtl_file

_FIXTURES = Path(__file__).parent / "fixtures" / "rtl"


def test_simple_comb_ports_are_extracted() -> None:
    parsed = parse_rtl_file(_FIXTURES / "simple_comb.v")

    assert parsed.module_name == "simple_comb"
    assert [port.name for port in parsed.ports] == ["a", "b", "y"]
    assert [port.direction for port in parsed.ports] == ["input", "input", "output"]
    assert [port.width for port in parsed.ports] == [1, 1, 1]


def test_parameterized_widths_are_preserved() -> None:
    parsed = parse_rtl_file(_FIXTURES / "simple_seq.v")

    assert parsed.parameters == {"WIDTH": "8"}
    d_port = next(port for port in parsed.ports if port.name == "d")
    q_port = next(port for port in parsed.ports if port.name == "q")
    done_port = next(port for port in parsed.ports if port.name == "done")

    assert d_port.width == "WIDTH-1:0"
    assert q_port.width == "WIDTH-1:0"
    assert done_port.width == 1


def test_non_ansi_header_recovers_body_port_information_conservatively() -> None:
    parsed = parse_rtl_file(_FIXTURES / "legacy_non_ansi.v")

    assert parsed.module_name == "legacy_non_ansi"
    assert [port.name for port in parsed.ports] == ["clk", "rst_n", "data", "done"]
    assert [port.direction for port in parsed.ports] == ["input", "input", "input", "output"]
    assert parsed.warnings
