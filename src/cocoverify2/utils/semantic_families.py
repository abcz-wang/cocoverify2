"""Helpers for recognizing small, reusable semantic verification families."""

from __future__ import annotations

import re
from typing import Any

from cocoverify2.core.models import DUTContract
from cocoverify2.core.types import PortDirection, SequentialKind

_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
}
_GROUP_PATTERNS = (
    re.compile(
        r"\b(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\b"
        r"(?:\s+\w+){0,4}\s+\b(?:valid|accepted|received|input|inputs|sample|samples|word|words)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bafter\b(?:\s+\w+){0,3}\s+\b(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bevery\b(?:\s+\w+){0,2}\s+\b(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\b"
        r"(?:\s+\w+){0,5}\s+\b(?:accepted|received|valid|input|sample|samples)\b"
        r"(?:\s+\w+){0,3}\s+\b(?:accumulation|group|groups|closure|output)\b",
        re.IGNORECASE,
    ),
)
_ACCUM_HINT_RE = re.compile(r"\b(accu|accumulator|accumulation|sum|summing|accumulate)\b", re.IGNORECASE)


def infer_grouped_valid_accumulator_family(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    """Return grouped-valid accumulator metadata when the contract strongly hints it."""
    if contract.timing.sequential_kind != SequentialKind.SEQ:
        return None

    lower_ports = {port.name.lower(): port for port in contract.ports}
    required = {"data_in", "valid_in", "data_out", "valid_out"}
    if not required.issubset(lower_ports):
        return None
    if lower_ports["data_in"].direction != PortDirection.INPUT or lower_ports["valid_in"].direction != PortDirection.INPUT:
        return None
    if lower_ports["data_out"].direction not in {PortDirection.OUTPUT, PortDirection.INOUT}:
        return None
    if lower_ports["valid_out"].direction not in {PortDirection.OUTPUT, PortDirection.INOUT}:
        return None

    evidence = " ".join(
        text
        for text in [
            contract.module_name,
            task_description or "",
            spec_text or "",
            *contract.assumptions,
            *(additional_texts or []),
        ]
        if text
    ).strip()
    if not evidence:
        return None
    if not _ACCUM_HINT_RE.search(evidence):
        return None

    group_size = infer_group_size(evidence)
    if group_size is None or group_size < 2:
        return None

    data_in = lower_ports["data_in"]
    data_out = lower_ports["data_out"]
    if isinstance(data_in.width, int) and isinstance(data_out.width, int) and data_out.width < data_in.width:
        return None

    reset_name = contract.resets[0].name if contract.resets else ""
    reset_active_level = contract.resets[0].active_level if contract.resets else None
    return {
        "data_in": data_in.name,
        "valid_in": lower_ports["valid_in"].name,
        "data_out": data_out.name,
        "valid_out": lower_ports["valid_out"].name,
        "group_size": group_size,
        "data_width": data_in.width if isinstance(data_in.width, int) else None,
        "output_width": data_out.width if isinstance(data_out.width, int) else None,
        "reset_name": reset_name,
        "reset_active_level": reset_active_level,
        "evidence_text": evidence,
    }


def infer_group_size(text: str | None) -> int | None:
    """Infer a small grouped-transaction size from descriptive text."""
    content = str(text or "").strip()
    if not content:
        return None
    pattern_candidates: list[int] = []
    for pattern in _GROUP_PATTERNS:
        for match in pattern.finditer(content):
            parsed = _parse_small_number(match.group("count"))
            if parsed is not None and parsed >= 2:
                pattern_candidates.append(parsed)
    if pattern_candidates:
        return max(pattern_candidates)

    fallback_candidates: list[int] = []
    for match in re.finditer(r"\b(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\b", content, re.IGNORECASE):
        parsed = _parse_small_number(match.group("count"))
        if parsed is None or parsed < 2:
            continue
        window = content[max(0, match.start() - 48) : min(len(content), match.end() + 96)]
        lower_window = window.lower()
        if any(token in lower_window for token in ("accum", "valid", "sample", "group", "closure", "received")):
            fallback_candidates.append(parsed)
    if fallback_candidates:
        return max(fallback_candidates)
    return None


def _parse_small_number(raw: str | None) -> int | None:
    token = str(raw or "").strip().lower()
    if not token:
        return None
    if token.isdigit():
        return int(token)
    return _NUMBER_WORDS.get(token)
