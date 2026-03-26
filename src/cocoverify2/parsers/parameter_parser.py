"""Helpers for parsing Verilog module parameter blocks."""

from __future__ import annotations

import re


def parse_parameter_block(parameter_block: str) -> tuple[dict[str, str], list[str]]:
    """Parse a Verilog parameter block into a name-to-value mapping.

    The parser is intentionally lightweight and supports common header forms such
    as ``parameter WIDTH = 8`` and ``parameter int DEPTH = 16``.
    """
    parameters: dict[str, str] = {}
    warnings: list[str] = []
    if not parameter_block.strip():
        return parameters, warnings

    for raw_segment in _split_top_level_commas(parameter_block):
        segment = raw_segment.strip()
        if not segment:
            continue
        segment = re.sub(r"^(parameter|localparam)\b", "", segment).strip()
        if "=" not in segment:
            warnings.append(f"Could not parse parameter segment without '=': {raw_segment.strip()}")
            continue
        left, value = segment.split("=", 1)
        name = _extract_parameter_name(left)
        if name is None:
            warnings.append(f"Could not identify parameter name in segment: {raw_segment.strip()}")
            continue
        parameters[name] = value.strip()
    return parameters, warnings


def _extract_parameter_name(left_hand_side: str) -> str | None:
    normalized = re.sub(r"\[[^\]]+\]", " ", left_hand_side)
    tokens = normalized.split()
    if not tokens:
        return None
    return tokens[-1]


def _split_top_level_commas(text: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    for char in text:
        if char in "([{" :
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
