"""Minimal integration smoke coverage for the orchestrator shell."""

from cocoverify2.core.orchestrator import VerificationOrchestrator


def test_orchestrator_exposes_default_stage_dependencies() -> None:
    orchestrator = VerificationOrchestrator()
    assert "contract" in orchestrator.stages
    assert "repair" in orchestrator.stages
