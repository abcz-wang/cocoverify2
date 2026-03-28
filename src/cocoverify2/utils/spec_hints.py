"""Helpers for extracting low-risk structured hints from free-form specs."""

from __future__ import annotations

import re

_INTERFACE_SECTION_ALIASES = {
    "module name": "module_name",
    "input port": "input_ports",
    "input ports": "input_ports",
    "output port": "output_ports",
    "output ports": "output_ports",
    "parameter": "parameters",
    "parameters": "parameters",
}
_BEHAVIOR_SECTION_PREFIXES = (
    "implementation:",
    "behavior:",
    "behaviour:",
    "algorithm:",
    "description:",
    "operation:",
    "operations:",
    "working:",
)


def extract_interface_hint_text(spec_text: str | None) -> str | None:
    """Extract an interface-only hint block from a structured RTLLM spec.

    The returned text is intentionally narrow: it keeps only explicit structured
    interface lines that can safely feed the ``golden_interface_text`` channel.
    Free-form behavioral or implementation prose is excluded.
    """

    if spec_text is None or not spec_text.strip():
        return None

    current_section: str | None = None
    saw_interface_section = False
    collected_lines: list[str] = []

    for raw_line in spec_text.splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue

        section_name = _match_section_name(stripped)
        if section_name is not None:
            current_section = section_name
            saw_interface_section = True
            continue

        if _is_behavioral_section_header(stripped):
            break
        if current_section is None:
            continue

        if current_section in {"input_ports", "output_ports"}:
            sanitized = _sanitize_port_line(stripped)
            if sanitized:
                collected_lines.append(sanitized)
            continue

        if current_section == "parameters":
            sanitized = _sanitize_parameter_line(stripped)
            if sanitized:
                collected_lines.append(sanitized)
            continue

        if current_section == "module_name":
            continue

    unique_lines: list[str] = []
    seen: set[str] = set()
    for line in collected_lines:
        if not line or line in seen:
            continue
        seen.add(line)
        unique_lines.append(line)

    if not saw_interface_section or not unique_lines:
        return None
    return "\n".join(unique_lines)


def _match_section_name(line: str) -> str | None:
    normalized = re.sub(r"\s+", " ", line.strip()).rstrip(":").lower()
    return _INTERFACE_SECTION_ALIASES.get(normalized)


def _is_behavioral_section_header(line: str) -> bool:
    lowered = line.strip().lower()
    return any(lowered.startswith(prefix) for prefix in _BEHAVIOR_SECTION_PREFIXES)


def _sanitize_port_line(line: str) -> str | None:
    match = re.match(
        r"^(?P<name>[A-Za-z_][A-Za-z0-9_$]*)(?:\s*\[[^\]]+\])?\s*:\s*(?P<desc>.+)$",
        line,
    )
    if match is None:
        return None
    description = match.group("desc").strip()
    if not description:
        return None
    return f"{match.group('name')}: {description}"


def _sanitize_parameter_line(line: str) -> str | None:
    match = re.match(r"^parameter\s+(?P<name>[A-Za-z_][A-Za-z0-9_$]*)\s*=", line, flags=re.IGNORECASE)
    if match is None:
        return None
    return f"{match.group('name')}: parameter from structured spec section"
