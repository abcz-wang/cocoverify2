"""Helpers for parsing Verilog ANSI-style port declarations."""

from __future__ import annotations

import re
from dataclasses import dataclass

from cocoverify2.core.models import PortSpec
from cocoverify2.core.types import PortDirection

_DIRECTION_KEYWORDS = {"input", "output", "inout"}
_TYPE_KEYWORDS = {"wire", "reg", "logic", "bit", "tri", "signed", "unsigned"}
_DIRECTION_RE = re.compile(r"^(input|output|inout)\b", flags=re.IGNORECASE)
_BODY_DECLARATION_RE = re.compile(r"^\s*(input|output|inout)\b(?P<body>[^;]*);", flags=re.IGNORECASE | re.MULTILINE)


@dataclass(slots=True)
class _PortContext:
    direction: PortDirection
    width: int | str | None
    raw_range: str | None
    signed: bool
    data_type: str | None


def parse_port_block(port_block: str) -> tuple[list[PortSpec], list[str]]:
    """Parse a Verilog ANSI-style port block into ``PortSpec`` entries."""
    ports: list[PortSpec] = []
    warnings: list[str] = []
    context: _PortContext | None = None

    for raw_segment in _split_top_level_commas(port_block):
        segment = raw_segment.strip()
        if not segment:
            continue
        port, context, port_warnings = _parse_port_segment(segment, context)
        warnings.extend(port_warnings)
        if port is not None:
            ports.append(port)
    return ports, warnings


def _parse_port_segment(segment: str, context: _PortContext | None) -> tuple[PortSpec | None, _PortContext | None, list[str]]:
    warnings: list[str] = []
    working = segment.strip()
    lower = working.lower()
    new_context = context

    direction_match = _DIRECTION_RE.match(working)
    if direction_match is not None:
        direction = PortDirection(direction_match.group(1).lower())
        width: int | str | None = 1
        raw_range: str | None = None
        signed = False
        data_type_tokens: list[str] = []
        working = working[direction_match.end() :].strip()

        while True:
            token_match = re.match(r"^(wire|reg|logic|bit|tri|signed|unsigned)\b", working)
            if token_match is None:
                break
            token = token_match.group(1)
            if token == "signed":
                signed = True
            elif token != "unsigned":
                data_type_tokens.append(token)
            working = working[token_match.end() :].strip()

        if working.startswith("["):
            raw_range = _extract_leading_range(working)
            if raw_range is not None:
                width = _decode_range_width(raw_range)
                working = working[len(raw_range) :].strip()

        new_context = _PortContext(
            direction=direction,
            width=width,
            raw_range=raw_range,
            signed=signed,
            data_type=" ".join(data_type_tokens) or None,
        )
    elif context is None:
        warnings.append(f"Port segment is missing a direction keyword: {segment}")

    active_context = new_context or _PortContext(
        direction=PortDirection.UNKNOWN,
        width=None,
        raw_range=None,
        signed=False,
        data_type=None,
    )

    name = _normalize_port_name(working)
    if name is None:
        warnings.append(f"Could not identify a port name in segment: {segment}")
        return None, new_context, warnings

    confidence = 1.0 if active_context.direction != PortDirection.UNKNOWN else 0.25
    source = "rtl_header" if active_context.direction != PortDirection.UNKNOWN else "rtl_header_partial"
    port = PortSpec(
        name=name,
        direction=active_context.direction,
        width=active_context.width,
        raw_range=active_context.raw_range,
        signed=active_context.signed,
        data_type=active_context.data_type,
        source=source,
        confidence=confidence,
    )
    return port, new_context, warnings


def recover_port_declarations_from_body(ports: list[PortSpec], body_text: str) -> tuple[list[PortSpec], list[str]]:
    """Recover conservative direction/type hints from legacy non-ANSI body declarations."""
    if not ports or not body_text.strip():
        return list(ports), []

    recovered_ports = [port.model_copy(deep=True) for port in ports]
    by_name = {port.name: port for port in recovered_ports}
    warnings: list[str] = []

    for match in _BODY_DECLARATION_RE.finditer(body_text):
        direction = PortDirection(match.group(1).lower())
        declaration_body = match.group("body").strip()
        context, remainder, context_warnings = _parse_declaration_context(direction, declaration_body)
        warnings.extend(context_warnings)
        for raw_name in _split_top_level_commas(remainder):
            port_name = _normalize_port_name(raw_name)
            if port_name is None or port_name not in by_name:
                continue
            port = by_name[port_name]
            if port.direction == PortDirection.UNKNOWN:
                port.direction = context.direction
                port.source = "rtl_body_declaration"
                port.confidence = max(port.confidence, 0.85)
            if port.raw_range is None and context.raw_range is not None:
                port.raw_range = context.raw_range
                port.width = context.width
            if port.data_type is None and context.data_type is not None:
                port.data_type = context.data_type
            if not port.signed and context.signed:
                port.signed = True
    return recovered_ports, warnings


def _parse_declaration_context(
    direction: PortDirection,
    declaration_body: str,
) -> tuple[_PortContext, str, list[str]]:
    warnings: list[str] = []
    working = declaration_body.strip()
    width: int | str | None = 1
    raw_range: str | None = None
    signed = False
    data_type_tokens: list[str] = []

    while True:
        token_match = re.match(r"^(wire|reg|logic|bit|tri|signed|unsigned)\b", working)
        if token_match is None:
            break
        token = token_match.group(1).lower()
        if token == "signed":
            signed = True
        elif token != "unsigned":
            data_type_tokens.append(token)
        working = working[token_match.end() :].strip()

    if working.startswith("["):
        raw_range = _extract_leading_range(working)
        if raw_range is not None:
            width = _decode_range_width(raw_range)
            working = working[len(raw_range) :].strip()
        else:
            warnings.append(f"Could not parse declaration range in body fragment: {declaration_body}")

    return (
        _PortContext(
            direction=direction,
            width=width,
            raw_range=raw_range,
            signed=signed,
            data_type=" ".join(data_type_tokens) or None,
        ),
        working,
        warnings,
    )


def _normalize_port_name(raw_name: str) -> str | None:
    working = raw_name.strip()
    if not working:
        return None
    if "=" in working:
        working = working.split("=", 1)[0].strip()
    working = re.sub(r"\[[^\]]+\]\s*$", "", working).strip()
    tokens = working.split()
    if not tokens:
        return None
    candidate = tokens[0].strip().strip(",")
    if not re.match(r"^[A-Za-z_][A-Za-z0-9_$]*$", candidate):
        return None
    return candidate


def _extract_leading_range(text: str) -> str | None:
    depth = 0
    current: list[str] = []
    for index, char in enumerate(text):
        current.append(char)
        if char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return "".join(current)
        elif index == 0 and char != "[":
            return None
    return None


def _decode_range_width(raw_range: str) -> int | str:
    inner = raw_range.strip()[1:-1].strip()
    if ":" not in inner:
        return inner
    msb, lsb = [part.strip() for part in inner.split(":", 1)]
    if _is_int_literal(msb) and _is_int_literal(lsb):
        return abs(int(msb) - int(lsb)) + 1
    return inner


def _is_int_literal(value: str) -> bool:
    return re.fullmatch(r"-?\d+", value) is not None


def _split_top_level_commas(text: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    for char in text:
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth = max(0, depth - 1)
        if char == "," and depth == 0:
            items.append("".join(current))
            current = []
            continue
        current.append(char)
    if current:
        items.append("".join(current))
    return items
