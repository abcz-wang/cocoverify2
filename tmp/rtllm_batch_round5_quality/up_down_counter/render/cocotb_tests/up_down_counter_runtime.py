"""Runtime helpers for filled cocotb TODO blocks in `up_down_counter`."""

from __future__ import annotations

from typing import Any


def mask_width(width: int | None) -> int:
    """Return an integer mask for a signal width."""
    if width is None:
        return (1 << 64) - 1
    width_int = max(1, int(width))
    return (1 << width_int) - 1


def to_uint(value: Any, width: int | None = None) -> int:
    """Convert a sampled value into an unsigned integer when resolvable."""
    raw = _extract_logic_text(value)
    if _contains_unknown(raw):
        raise AssertionError(f"Value is not fully resolvable as unsigned integer: {raw!r}")
    result = int(raw, 2) if set(raw) <= {"0", "1"} else int(raw, 0)
    return result & mask_width(width)


def to_sint(value: Any, width: int | None) -> int:
    """Convert a sampled value into a signed integer using two's complement."""
    unsigned = to_uint(value, width)
    width_int = max(1, int(width or 1))
    sign_bit = 1 << (width_int - 1)
    full_scale = 1 << width_int
    return unsigned - full_scale if unsigned & sign_bit else unsigned


def is_high_impedance(value: Any) -> bool:
    """Return whether a sampled value contains any Z bits."""
    return "z" in _extract_logic_text(value).lower()


def is_unknown(value: Any) -> bool:
    """Return whether a sampled value contains X/Z-like uncertainty."""
    return _contains_unknown(_extract_logic_text(value))


def assert_equal(name: str, observed: Any, expected: Any) -> None:
    """Assert equality, handling logic strings and integer-like values."""
    if isinstance(expected, str):
        expected_text = expected.strip().lower()
        if expected_text in {"z", "high_z", "high_impedance"}:
            assert is_high_impedance(observed), f"Expected {name} to be high impedance, got {observed!r}"
            return
        observed_text = _extract_logic_text(observed).lower()
        assert observed_text == expected_text, f"Mismatch for {name}: observed={observed_text!r} expected={expected_text!r}"
        return
    assert observed == expected, f"Mismatch for {name}: observed={observed!r} expected={expected!r}"


def assert_true(condition: bool, message: str) -> None:
    """Assert a truthy condition with a stable message."""
    assert bool(condition), message


def normalize_sampled_value(value: Any, width: int | None = None) -> Any:
    """Normalize a sampled signal value into int-or-string form."""
    text = _extract_logic_text(value)
    if _contains_unknown(text):
        return text.lower()
    if set(text) <= {"0", "1"}:
        return int(text, 2) & mask_width(width)
    try:
        return int(text, 0) & mask_width(width)
    except ValueError:
        return text


def normalize_driven_value(value: Any, width: int | None = None) -> Any:
    """Normalize a driven value before assigning it onto a DUT signal."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value & mask_width(width) if width is not None else value
    text = str(value).strip()
    if not text:
        raise AssertionError("Drive value must not be empty.")
    lowered = text.lower()
    if any(ch in lowered for ch in ("x", "z")):
        return lowered
    parsed = int(text, 0)
    return parsed & mask_width(width) if width is not None else parsed


def _extract_logic_text(value: Any) -> str:
    if hasattr(value, "binstr"):
        return str(value.binstr)
    if hasattr(value, "value") and hasattr(value.value, "binstr"):
        return str(value.value.binstr)
    if isinstance(value, int):
        return bin(value if value >= 0 else -value)[2:]
    return str(value).strip()


def _contains_unknown(text: str) -> bool:
    lowered = str(text or "").strip().lower()
    return any(ch in lowered for ch in ("x", "z", "u", "w", "-"))
