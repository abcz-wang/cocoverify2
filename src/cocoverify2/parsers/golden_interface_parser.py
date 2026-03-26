"""Minimal parsing helpers for optional golden interface text hints."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from cocoverify2.core.models import ClockSpec, ResetSpec


@dataclass(slots=True)
class GoldenInterfaceHints:
    """Structured hints extracted from optional golden interface text."""

    port_names: list[str] = field(default_factory=list)
    clocks: list[ClockSpec] = field(default_factory=list)
    resets: list[ResetSpec] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    ambiguities: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def parse_golden_interface_text(text: str | None) -> GoldenInterfaceHints:
    """Extract low-risk interface hints from free-form golden interface text."""
    hints = GoldenInterfaceHints()
    if text is None or not text.strip():
        return hints

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        normalized = re.sub(r"^[\-*]\s*", "", line)
        match = re.match(r"^(?P<name>[A-Za-z_][A-Za-z0-9_$]*)\s*[:\-]\s*(?P<desc>.+)$", normalized)
        if match is not None:
            _consume_structured_line(hints, match.group("name"), match.group("desc"))
            continue
        if normalized.lower().startswith("ports") and ":" in normalized:
            _, raw_ports = normalized.split(":", 1)
            for token in re.findall(r"[A-Za-z_][A-Za-z0-9_$]*", raw_ports):
                _append_unique(hints.port_names, token)
            continue
        hints.assumptions.append(normalized)
    return hints


def _consume_structured_line(hints: GoldenInterfaceHints, name: str, description: str) -> None:
    desc_lower = description.lower()
    if any(token in desc_lower for token in ("input", "output", "inout", "port", "signal")):
        _append_unique(hints.port_names, name)
    if "clock" in desc_lower or name.lower() in {"clk", "clock", "i_clk", "aclk"}:
        hints.clocks.append(ClockSpec(name=name, source="golden_interface", confidence=0.85))
    if "reset" in desc_lower or name.lower() in {"rst", "rst_n", "reset", "resetn", "aresetn"}:
        active_level = None
        confidence = 0.7
        if "active low" in desc_lower or "active-low" in desc_lower or name.lower().endswith("_n"):
            active_level = 0
            confidence = 0.9
        elif "active high" in desc_lower or "active-high" in desc_lower:
            active_level = 1
            confidence = 0.9
        hints.resets.append(
            ResetSpec(
                name=name,
                active_level=active_level,
                source="golden_interface",
                confidence=confidence,
            )
        )


def _append_unique(items: list[str], value: str) -> None:
    if value not in items:
        items.append(value)
