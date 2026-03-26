"""Parsing utilities for cocoverify2."""

from cocoverify2.parsers.golden_interface_parser import GoldenInterfaceHints, parse_golden_interface_text
from cocoverify2.parsers.parameter_parser import parse_parameter_block
from cocoverify2.parsers.port_parser import parse_port_block
from cocoverify2.parsers.rtl_parser import ParsedRTLModule, parse_rtl_file, parse_rtl_text, strip_comments

__all__ = [
    "GoldenInterfaceHints",
    "ParsedRTLModule",
    "parse_golden_interface_text",
    "parse_parameter_block",
    "parse_port_block",
    "parse_rtl_file",
    "parse_rtl_text",
    "strip_comments",
]
