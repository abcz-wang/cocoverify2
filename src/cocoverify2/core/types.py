"""Shared enums and literal-like types for cocoverify2."""

from __future__ import annotations

from enum import Enum


class StageName(str, Enum):
    """Supported pipeline stage names."""

    CONTRACT = "contract"
    PLAN = "plan"
    ORACLE = "oracle"
    RENDER = "render"
    FILL = "fill"
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


class OracleCheckType(str, Enum):
    """Structured oracle check categories."""

    PROTOCOL = "protocol"
    FUNCTIONAL = "functional"
    PROPERTY = "property"


class TemporalWindowMode(str, Enum):
    """Supported temporal window styles for oracle checks."""

    EXACT_CYCLE = "exact_cycle"
    BOUNDED_RANGE = "bounded_range"
    EVENT_BASED = "event_based"
    UNBOUNDED_SAFE = "unbounded_safe"


class OracleStrictness(str, Enum):
    """Strictness tags for conservative oracle generation."""

    STRICT = "strict"
    CONSERVATIVE = "conservative"
    GUARDED = "guarded"


class AssertionStrength(str, Enum):
    """Artifact-level value assertion strength for one observed signal."""

    EXACT = "exact"
    GUARDED = "guarded"
    UNRESOLVED = "unresolved"


class DefinednessMode(str, Enum):
    """When a rendered runtime should require an observed signal to be defined."""

    NOT_REQUIRED = "not_required"
    AT_OBSERVATION = "at_observation"


class GenerationMode(str, Enum):
    """Supported generation modes for plan/oracle stages."""

    RULE_BASED = "rule_based"
    HYBRID = "hybrid"


class SimulationMode(str, Enum):
    """Supported execution modes for the simulation stage."""

    AUTO = "auto"
    COCOTB_TOOLS = "cocotb_tools"
    MAKE = "make"
    FILELIST = "filelist"


class ExecutionStatus(str, Enum):
    """Coarse execution-layer status values for simulation results."""

    SUCCESS = "success"
    COMPILE_ERROR = "compile_error"
    ELABORATION_ERROR = "elaboration_error"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    ENVIRONMENT_ERROR = "environment_error"
    UNKNOWN_FAILURE = "unknown_failure"
