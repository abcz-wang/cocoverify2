"""Shared enums and literal-like types for cocoverify2."""

from __future__ import annotations

from enum import Enum


class StageName(str, Enum):
    """Supported pipeline stage names."""

    CONTRACT = "contract"
    PLAN = "plan"
    ORACLE = "oracle"
    RENDER = "render"
    RUN = "run"
    TRIAGE = "triage"
    REPAIR = "repair"
    REPORT = "report"


class VerdictKind(str, Enum):
    """High-level verification verdicts."""

    PASS = "pass"
    FAIL = "fail"
    SUSPICIOUS = "suspicious"
    INCONCLUSIVE = "inconclusive"


class PortDirection(str, Enum):
    """Supported DUT port directions."""

    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"
    UNKNOWN = "unknown"


class LatencyModel(str, Enum):
    """Latency model tags for timing assumptions."""

    FIXED = "fixed"
    VARIABLE = "variable"
    UNKNOWN = "unknown"


class SequentialKind(str, Enum):
    """Coarse DUT timing style classification."""

    COMB = "comb"
    SEQ = "seq"
    UNKNOWN = "unknown"


class TestCategory(str, Enum):
    """Named test categories for structured planning."""

    RESET = "reset"
    BASIC = "basic"
    EDGE = "edge"
    PROTOCOL = "protocol"
    BACK_TO_BACK = "back_to_back"
    NEGATIVE = "negative"
    REGRESSION = "regression"
    METAMORPHIC = "metamorphic"
