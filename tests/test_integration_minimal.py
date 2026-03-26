"""Minimal integration smoke coverage for Phase 0."""

import pytest

from cocoverify2.core.errors import PhaseNotImplementedError
from cocoverify2.core.orchestrator import VerificationOrchestrator


def test_orchestrator_verify_is_declared_but_not_implemented() -> None:
    orchestrator = VerificationOrchestrator()
    with pytest.raises(PhaseNotImplementedError):
        orchestrator.verify(task_id="demo", task_description="phase 0 smoke")
