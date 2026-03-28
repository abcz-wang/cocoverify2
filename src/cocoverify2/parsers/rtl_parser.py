"""Lightweight Verilog RTL parsing helpers for contract extraction."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from cocoverify2.core.errors import ParserError
from cocoverify2.core.models import PortSpec
from cocoverify2.parsers.parameter_parser import parse_parameter_block
from cocoverify2.parsers.port_parser import parse_port_block, recover_port_declarations_from_body
from cocoverify2.utils.files import read_text

_MODULE_HEADER_RE = re.compile(
    r"\bmodule\s+(?P<name>[A-Za-z_][A-Za-z0-9_$]*)\s*"
    r"(?P<param_block>#\s*\((?P<params>.*?)\))?\s*"
    r"\((?P<ports>.*?)\)\s*;",
    re.DOTALL,
)


@dataclass(slots=True)
class ParsedRTLModule:
    """Parsed view of a single Verilog module header and body."""

    module_name: str
    parameters: dict[str, str]
    ports: list[PortSpec]
    source_path: Path
    cleaned_text: str
    body_text: str
    warnings: list[str]


def parse_rtl_file(path: Path) -> ParsedRTLModule:
    """Load and parse the first module found in a Verilog source file."""
    return parse_rtl_text(read_text(path), source_path=path)


def parse_rtl_text(text: str, *, source_path: Path) -> ParsedRTLModule:
    """Parse the first module header from a Verilog source string."""
    cleaned = strip_comments(text)
    matches = list(_MODULE_HEADER_RE.finditer(cleaned))
    if not matches:
        raise ParserError(
            parser_name="rtl_parser",
            message="Could not find a supported module header.",
            path=source_path,
            snippet=cleaned[:200],
        )

    match = matches[0]
    warnings: list[str] = []
    if len(matches) > 1:
        warnings.append(
            f"Multiple module headers were found in {source_path.name}; using the first module '{match.group('name')}'."
        )

    parameters, parameter_warnings = parse_parameter_block(match.group("params") or "")
    ports, port_warnings = parse_port_block(match.group("ports") or "")
    warnings.extend(parameter_warnings)
    warnings.extend(port_warnings)

    body_text = _extract_module_body(cleaned, match.end())
    recovered_ports, recovery_warnings = recover_port_declarations_from_body(ports, body_text)
    ports = recovered_ports
    warnings.extend(recovery_warnings)
    if not body_text.strip():
        warnings.append(f"Module '{match.group('name')}' body could not be isolated cleanly.")
    if not ports:
        warnings.append(f"Module '{match.group('name')}' has no parsed ports from the header.")

    return ParsedRTLModule(
        module_name=match.group("name"),
        parameters=parameters,
        ports=ports,
        source_path=source_path,
        cleaned_text=cleaned,
        body_text=body_text,
        warnings=warnings,
    )


def strip_comments(text: str) -> str:
    """Remove line and block comments from Verilog text."""
    without_block = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    without_line = re.sub(r"//.*", "", without_block)
    return without_line


def _extract_module_body(cleaned_text: str, header_end: int) -> str:
    endmodule_match = re.search(r"\bendmodule\b", cleaned_text[header_end:], flags=re.DOTALL)
    if endmodule_match is None:
        return cleaned_text[header_end:]
    body_end = header_end + endmodule_match.start()
    return cleaned_text[header_end:body_end]
