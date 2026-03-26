"""Model smoke tests for cocoverify2 Phase 0/1."""

from pathlib import Path

from cocoverify2.core.models import (
    ClockSpec,
    DUTContract,
    FinalVerdict,
    OracleSpec,
    PortSpec,
    ResetSpec,
    SimulationConfig,
    SimulationResult,
    TestCasePlan as CasePlanModel,
    TestPlan as PlanModel,
    TriageResult,
    VerificationReport,
)
from cocoverify2.core.types import PortDirection, TestCategory as PlanCategory, VerdictKind


def test_core_models_can_be_instantiated_and_serialized() -> None:
    contract = DUTContract(
        module_name="demo",
        rtl_sources=[Path("dut.v")],
        ports=[PortSpec(name="clk", direction=PortDirection.INPUT, width=1)],
        clocks=[ClockSpec(name="clk", period_ns_guess=10.0)],
        resets=[ResetSpec(name="rst_n", active_level=0, synchronous=False)],
        observable_outputs=["done"],
        assumptions=["demo assumption"],
        source_map={"module_name": ["rtl:dut.v"]},
    )
    plan = PlanModel(
        module_name="demo",
        based_on_contract="artifacts/contract/contract.json",
        plan_strategy="rule_based_demo",
        cases=[
            CasePlanModel(
                case_id="reset_001",
                goal="reset should initialize outputs",
                category=PlanCategory.RESET,
                expected_properties=["done == 0 after reset"],
                observed_signals=["done"],
                timing_assumptions=["observe after reset release"],
                source="rule_based",
            )
        ],
        assumptions=["plan assumption"],
    )
    oracle = OracleSpec(protocol_oracle={"mode": "placeholder"})
    sim_cfg = SimulationConfig(rtl_sources=[Path("dut.v")], toplevel="demo")
    sim_result = SimulationResult(executed_cases=["reset_001"])
    triage = TriageResult(primary_category="unclassified")
    verdict = FinalVerdict(verdict=VerdictKind.INCONCLUSIVE, rationale=["phase smoke"])
    report = VerificationReport(
        contract=contract,
        test_plan_summary=plan,
        oracle_summary=oracle,
        simulation_summary=sim_result,
        triage=triage,
        final_verdict=verdict,
    )

    payload = report.model_dump(mode="json")
    assert payload["contract"]["module_name"] == "demo"
    assert payload["contract"]["rtl_sources"] == ["dut.v"]
    assert payload["test_plan_summary"]["cases"][0]["category"] == "reset"
    assert payload["test_plan_summary"]["based_on_contract"] == "artifacts/contract/contract.json"
    assert payload["final_verdict"]["verdict"] == "inconclusive"
    assert sim_cfg.model_dump(mode="json")["toplevel"] == "demo"
