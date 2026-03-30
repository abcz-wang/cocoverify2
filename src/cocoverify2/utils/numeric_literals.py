"""Helpers for validating deterministic numeric drive literals."""

from __future__ import annotations

import re
from typing import Any

_PLACEHOLDER_TOKENS = {
    "any",
    "any_value",
    "arbitrary",
    "arbitrary_value",
    "dont_care",
    "placeholder",
    "rand",
    "rand32",
    "rand64",
    "random",
}
_VERILOG_LITERAL_RE = re.compile(r"(?i)(\d+)?'([s]?)([bodh])([0-9a-f_xz]+)")


def normalize_deterministic_literal(value: Any) -> bool | int:
    """Return a reproducible literal value or raise ``ValueError``."""
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and not isinstance(value, bool):
        return value

    text = str(value or "").strip()
    if not text:
        raise ValueError("Drive literal must not be empty.")

    lowered = text.lower().replace("_", "")
    if lowered in _PLACEHOLDER_TOKENS:
        raise ValueError(f"Unsupported nondeterministic placeholder literal: {text!r}")

    verilog_match = _VERILOG_LITERAL_RE.fullmatch(lowered)
    if verilog_match:
        _, _, base_code, digits = verilog_match.groups()
        if any(ch in digits for ch in ("x", "z")):
            raise ValueError(f"Unsupported unknown/high-z drive literal: {text!r}")
        base = {"b": 2, "o": 8, "d": 10, "h": 16}[base_code]
        return int(digits.replace("_", ""), base)

    try:
        if re.fullmatch(r"[+-]?\d+", text):
            return int(text, 10)
        return int(text, 0)
    except ValueError as exc:
        raise ValueError(f"Unsupported deterministic drive literal: {text!r}") from exc


def is_deterministic_literal(value: Any) -> bool:
    """Return whether ``value`` can be used in deterministic mainline stimulus."""
    try:
        normalize_deterministic_literal(value)
    except ValueError:
        return False
    return True
