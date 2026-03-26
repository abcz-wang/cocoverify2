"""Rule-based test plan generation for Phase 2."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from cocoverify2.core.errors import ArtifactError, ConfigurationError
from cocoverify2.core.models import DUTContract, HandshakeGroup, TestCasePlan, TestPlan
from cocoverify2.core.types import PortDirection, SequentialKind, TestCategory
from cocoverify2.utils.files import ensure_dir, read_json, write_json, write_yaml
from cocoverify2.utils.logging import get_logger


class TestPlanGenerator:
    """Generate a conservative, structured test plan from a ``DUTContract``."""

    __test__ = False

    def __init__(self) -> None:
        """Initialize the generator with a stage-scoped logger."""
        self.logger = get_logger(__name__)

    def run(
        self,
        *,
        contract: DUTContract,
        task_description: str | None,
        spec_text: str | None,
        out_dir: Path,
        based_on_contract: str = "",
    ) -> TestPlan:
        """Generate and persist a ``TestPlan`` from a validated contract."""
        if not contract.module_name:
            raise ConfigurationError("Test plan generation requires a contract with a module_name.")

        self.logger.debug(
            "Generating test plan for module=%s timing=%s handshake_groups=%d contract_confidence=%.2f",
            contract.module_name,
            contract.timing.sequential_kind,
            len(contract.handshake_groups),
            contract.contract_confidence,
        )
        assumptions = list(contract.assumptions)
        unresolved_items = list(contract.ambiguities)
        weak_contract = _is_weak_contract(contract)
        observed_signals = _default_observed_signals(contract)
        counters: dict[str, int] = defaultdict(int)
        cases: list[TestCasePlan] = []

        if contract.timing.sequential_kind == SequentialKind.UNKNOWN:
            unresolved_items.append("Timing model is unresolved; generated cases avoid fixed-latency checks.")
        if weak_contract:
            unresolved_items.append("Contract strength is limited; generated cases favor safe observation over precise timing assumptions.")
        if not contract.observable_outputs:
            unresolved_items.append("Observable outputs are incomplete or unresolved; some cases rely on protocol-visible or port-level observation.")
        if any(port.direction == PortDirection.UNKNOWN for port in contract.ports):
            unresolved_items.append("Some port directions are unresolved; case intents avoid strong source/sink assumptions for those signals.")

        if contract.resets:
            cases.append(
                self._make_case(
                    counters=counters,
                    category=TestCategory.RESET,
                    goal="Establish a stable post-reset baseline before functional checking.",
                    preconditions=["Reset signal is available in the contract."],
                    stimulus_intent=["Assert the detected reset using the inferred polarity.", "Release reset conservatively and observe interface stabilization."],
                    expected_properties=[
                        "Observed outputs or protocol-visible signals settle to a stable, non-X post-reset state.",
                        "No fixed-cycle completion is assumed during reset recovery.",
                    ],
                    observed_signals=observed_signals,
                    timing_assumptions=_safe_timing_assumptions(contract),
                    dependencies=[],
                    coverage_tags=["reset", "initialization", "stability"],
                    priority=1,
                    confidence=_case_confidence(contract, bonus=0.05),
                    notes=["Reset polarity may still be heuristic if the contract marks it ambiguous."],
                )
            )

        cases.append(self._build_basic_case(contract=contract, counters=counters, observed_signals=observed_signals))

        if _should_add_edge_case(contract):
            cases.append(self._build_edge_case(contract=contract, counters=counters, observed_signals=observed_signals))

        for group in contract.handshake_groups:
            cases.extend(self._build_handshake_cases(contract=contract, group=group, counters=counters, observed_signals=observed_signals))

        if _should_add_back_to_back_case(contract):
            cases.append(self._build_back_to_back_case(contract=contract, counters=counters, observed_signals=observed_signals))

        if contract.illegal_input_constraints:
            cases.append(self._build_negative_case(contract=contract, counters=counters, observed_signals=observed_signals))
        elif weak_contract and contract.timing.sequential_kind == SequentialKind.UNKNOWN:
            unresolved_items.append("Negative or illegal-input behavior is not planned because the contract does not provide reliable constraints.")

        if task_description:
            assumptions.append("Task description was provided and only used as a low-risk planning hint.")
        if spec_text:
            assumptions.append("Spec text was provided and only used where it did not contradict the contract.")

        _dedupe_in_place(unresolved_items)
        _dedupe_in_place(assumptions)
        plan = TestPlan(
            module_name=contract.module_name,
            based_on_contract=based_on_contract or contract.module_name,
            plan_strategy=_plan_strategy(contract, weak_contract),
            cases=cases,
            unresolved_items=unresolved_items,
            assumptions=assumptions,
            plan_confidence=_estimate_plan_confidence(contract=contract, cases=cases, unresolved_items=unresolved_items, weak_contract=weak_contract),
        )
        self._dump_plan_artifacts(plan, out_dir)
        self.logger.info(
            "Generated %d conservative plan cases for module '%s' with plan_confidence=%.2f",
            len(plan.cases),
            plan.module_name,
            plan.plan_confidence,
        )
        return plan

    def run_from_artifact(
        self,
        *,
        contract_path: Path,
        task_description: str | None,
        spec_text: str | None,
        out_dir: Path,
    ) -> TestPlan:
        """Load a contract artifact and generate a plan from it."""
        contract = load_contract_artifact(contract_path)
        return self.run(
            contract=contract,
            task_description=task_description,
            spec_text=spec_text,
            out_dir=out_dir,
            based_on_contract=str(contract_path),
        )

    def _build_basic_case(
        self,
        *,
        contract: DUTContract,
        counters: dict[str, int],
        observed_signals: list[str],
    ) -> TestCasePlan:
        input_names = [port.name for port in contract.ports if port.direction == PortDirection.INPUT]
        if contract.timing.sequential_kind == SequentialKind.COMB:
            goal = "Exercise representative legal input combinations and observe output mapping."
            expected_properties = [
                "Observable outputs respond to legal input changes without assuming internal state.",
                "Checks focus on input/output consistency rather than cycle-accurate timing.",
            ]
        elif contract.timing.sequential_kind == SequentialKind.SEQ:
            goal = "Apply one legal operation and observe stable post-operation behavior."
            expected_properties = [
                "A legal operation causes an observable state or output change after conservative observation.",
                "The plan does not assume a completion event before it is externally visible.",
            ]
        else:
            goal = "Apply one legal operation or transaction and observe any externally visible progress."
            expected_properties = [
                "Checks are limited to reset-safe, protocol-safe, or output-visible behavior.",
                "No fixed latency or exact cycle count is assumed.",
            ]
        return self._make_case(
            counters=counters,
            category=TestCategory.BASIC,
            goal=goal,
            preconditions=["Use only ports and observable signals present in the contract."],
            stimulus_intent=[f"Drive a representative legal input pattern across known inputs: {input_names or ['<no resolved inputs>']}"],
            expected_properties=expected_properties,
            observed_signals=observed_signals,
            timing_assumptions=_safe_timing_assumptions(contract),
            dependencies=["reset_001"] if contract.resets else [],
            coverage_tags=["basic", "sanity", contract.timing.sequential_kind],
            priority=1,
            confidence=_case_confidence(contract),
            notes=["Case intent is conservative when the contract is weak or timing is unresolved."],
        )

    def _build_edge_case(
        self,
        *,
        contract: DUTContract,
        counters: dict[str, int],
        observed_signals: list[str],
    ) -> TestCasePlan:
        vector_inputs = [port.name for port in contract.ports if port.direction == PortDirection.INPUT and port.width not in (None, 1)]
        expected = [
            "Boundary-value stimulation does not rely on hidden state or undocumented latency.",
            "When width expressions are symbolic, only conservative min/max-style exploration is planned.",
        ]
        return self._make_case(
            counters=counters,
            category=TestCategory.EDGE,
            goal="Exercise boundary-value and width-sensitive input patterns.",
            preconditions=["At least one input or symbolic-width input is available."],
            stimulus_intent=[f"Use zero-like, one-like, and boundary patterns on {vector_inputs or ['known inputs']}"],
            expected_properties=expected,
            observed_signals=observed_signals,
            timing_assumptions=_safe_timing_assumptions(contract),
            dependencies=["basic_001"],
            coverage_tags=["edge", "boundary"],
            priority=2,
            confidence=_case_confidence(contract, penalty=0.05),
            notes=["Edge coverage remains value-oriented and avoids fixed-latency assumptions."],
        )

    def _build_handshake_cases(
        self,
        *,
        contract: DUTContract,
        group: HandshakeGroup,
        counters: dict[str, int],
        observed_signals: list[str],
    ) -> list[TestCasePlan]:
        cases: list[TestCasePlan] = []
        protocol_signals = list(group.signals.values()) + [signal for signal in observed_signals if signal not in group.signals.values()]

        if group.pattern == "valid_ready":
            cases.append(
                self._make_case(
                    counters=counters,
                    category=TestCategory.PROTOCOL,
                    goal=f"Observe basic {group.group_name} valid/ready handshake acceptance.",
                    preconditions=["Both valid and ready signals are present in the contract."],
                    stimulus_intent=[f"Drive {group.signals['valid']} with a legal transaction while allowing {group.signals['ready']} to indicate acceptance."],
                    expected_properties=[
                        "When valid and ready overlap, observe externally visible acceptance or progress.",
                        "Do not assume a fixed completion cycle after acceptance.",
                    ],
                    observed_signals=protocol_signals,
                    timing_assumptions=_protocol_safe_timing_assumptions(contract),
                    dependencies=["reset_001"] if contract.resets else [],
                    coverage_tags=["protocol", "valid_ready", "acceptance", group.group_name],
                    priority=1,
                    confidence=_case_confidence(contract, bonus=0.05),
                    notes=["Protocol case is intentionally acceptance-oriented, not latency-committing."],
                )
            )
            cases.append(
                self._make_case(
                    counters=counters,
                    category=TestCategory.PROTOCOL,
                    goal=f"Observe {group.group_name} backpressure behavior when ready is low.",
                    preconditions=[f"{group.signals['ready']} can be held low or observed low."],
                    stimulus_intent=[f"Attempt a transaction while {group.signals['ready']} remains low or unavailable for acceptance."],
                    expected_properties=[
                        "Progress is deferred, stalled, or otherwise safely withheld while ready is low.",
                        "The plan does not assume a single exact stall policy beyond safe non-acceptance observation.",
                    ],
                    observed_signals=protocol_signals,
                    timing_assumptions=_protocol_safe_timing_assumptions(contract),
                    dependencies=["basic_001"],
                    coverage_tags=["protocol", "valid_ready", "backpressure", group.group_name],
                    priority=2,
                    confidence=_case_confidence(contract, penalty=0.05),
                    notes=["Backpressure case is protocol-safe and avoids precise throughput claims."],
                )
            )
            cases.append(
                self._make_case(
                    counters=counters,
                    category=TestCategory.PROTOCOL,
                    goal=f"Observe safe valid persistence or safe-source behavior for {group.group_name} traffic.",
                    preconditions=[f"{group.signals['valid']} is visible in the contract."],
                    stimulus_intent=[f"Maintain or re-assert {group.signals['valid']} across conservative observation windows until acceptance is visible."],
                    expected_properties=[
                        "Source-side behavior remains safe and externally consistent until acceptance is observed.",
                        "No exact persistence policy is assumed beyond safe observation.",
                    ],
                    observed_signals=protocol_signals,
                    timing_assumptions=_protocol_safe_timing_assumptions(contract),
                    dependencies=["protocol_001"],
                    coverage_tags=["protocol", "valid_ready", "persistence", group.group_name],
                    priority=3,
                    confidence=_case_confidence(contract, penalty=0.08),
                    notes=["This case is intentionally unresolved-safe when the contract does not define source obligations exactly."],
                )
            )
        elif group.pattern == "start_done":
            cases.append(
                self._make_case(
                    counters=counters,
                    category=TestCategory.PROTOCOL,
                    goal="Observe whether start eventually leads to externally visible completion.",
                    preconditions=["Start and done signals are both present."],
                    stimulus_intent=[f"Pulse or assert {group.signals['start']} conservatively and watch for {group.signals['done']} or related output progress."],
                    expected_properties=[
                        "A legal start request eventually results in a visible completion or completion-related observation.",
                        "No exact completion latency is assumed.",
                    ],
                    observed_signals=protocol_signals,
                    timing_assumptions=_protocol_safe_timing_assumptions(contract),
                    dependencies=["basic_001"],
                    coverage_tags=["protocol", "start_done", "completion"],
                    priority=2,
                    confidence=_case_confidence(contract, penalty=0.05),
                    notes=["Completion is checked conservatively because the contract does not guarantee exact latency."],
                )
            )
        elif group.pattern == "req_ack":
            cases.append(
                self._make_case(
                    counters=counters,
                    category=TestCategory.PROTOCOL,
                    goal="Observe a basic req/ack exchange without assuming exact timing.",
                    preconditions=["Request and acknowledge signals are both present."],
                    stimulus_intent=[f"Issue {group.signals['req']} and observe whether {group.signals['ack']} indicates acceptance or completion."],
                    expected_properties=[
                        "A legal request eventually receives an externally visible acknowledge or progress indicator.",
                        "No fixed-latency acknowledge timing is assumed.",
                    ],
                    observed_signals=protocol_signals,
                    timing_assumptions=_protocol_safe_timing_assumptions(contract),
                    dependencies=["basic_001"],
                    coverage_tags=["protocol", "req_ack", "acceptance"],
                    priority=2,
                    confidence=_case_confidence(contract, penalty=0.05),
                    notes=["Req/ack planning remains conservative unless the contract later states stronger semantics."],
                )
            )
        return cases

    def _build_back_to_back_case(
        self,
        *,
        contract: DUTContract,
        counters: dict[str, int],
        observed_signals: list[str],
    ) -> TestCasePlan:
        return self._make_case(
            counters=counters,
            category=TestCategory.BACK_TO_BACK,
            goal="Observe repeated or back-to-back legal operations under conservative timing assumptions.",
            preconditions=["At least one legal operation is already defined by the basic case."],
            stimulus_intent=["Apply two legal operations with minimal idle spacing that remains safe for the current contract strength."],
            expected_properties=[
                "Repeated operations do not rely on hidden fixed-latency assumptions.",
                "The second operation is observed only through externally visible acceptance, completion, or output change.",
            ],
            observed_signals=observed_signals,
            timing_assumptions=_safe_timing_assumptions(contract),
            dependencies=["basic_001"],
            coverage_tags=["back_to_back", "repeated_operation"],
            priority=3,
            confidence=_case_confidence(contract, penalty=0.08),
            notes=["When timing is unresolved, this case stays unresolved-safe and does not require deterministic overlap behavior."],
        )

    def _build_negative_case(
        self,
        *,
        contract: DUTContract,
        counters: dict[str, int],
        observed_signals: list[str],
    ) -> TestCasePlan:
        return self._make_case(
            counters=counters,
            category=TestCategory.NEGATIVE,
            goal="Exercise documented illegal or constrained input behavior conservatively.",
            preconditions=["Contract provides illegal input constraints."],
            stimulus_intent=[f"Probe one or more documented constrained inputs: {contract.illegal_input_constraints}"],
            expected_properties=[
                "Observe safe handling, rejection, or non-progress for documented illegal input conditions.",
                "Do not assume undocumented error signaling semantics.",
            ],
            observed_signals=observed_signals,
            timing_assumptions=_safe_timing_assumptions(contract),
            dependencies=["basic_001"],
            coverage_tags=["negative", "illegal_input"],
            priority=3,
            confidence=_case_confidence(contract, penalty=0.1),
            notes=["Negative planning is limited to constraints explicitly present in the contract or spec hints."],
        )

    def _make_case(
        self,
        *,
        counters: dict[str, int],
        category: TestCategory,
        goal: str,
        preconditions: list[str],
        stimulus_intent: list[str],
        expected_properties: list[str],
        observed_signals: list[str],
        timing_assumptions: list[str],
        dependencies: list[str],
        coverage_tags: list[str],
        priority: int,
        confidence: float,
        notes: list[str],
    ) -> TestCasePlan:
        counters[category.value] += 1
        case_id = f"{category.value}_{counters[category.value]:03d}"
        return TestCasePlan(
            case_id=case_id,
            goal=goal,
            category=category,
            preconditions=preconditions,
            stimulus_intent=stimulus_intent,
            expected_properties=expected_properties,
            observed_signals=observed_signals,
            timing_assumptions=timing_assumptions,
            dependencies=dependencies,
            coverage_tags=coverage_tags,
            priority=priority,
            confidence=confidence,
            source="rule_based",
            notes=notes,
        )

    def _dump_plan_artifacts(self, plan: TestPlan, out_dir: Path) -> None:
        plan_dir = ensure_dir(out_dir / "plan")
        write_json(plan_dir / "test_plan.json", plan.model_dump(mode="json"))
        write_yaml(plan_dir / "test_plan_summary.yaml", _build_plan_summary(plan))
        self.logger.info("Wrote test plan artifacts to %s", plan_dir)


def load_contract_artifact(path: Path) -> DUTContract:
    """Load a ``DUTContract`` from a JSON artifact path."""
    if not path.exists():
        raise ArtifactError(f"Contract artifact does not exist: {path}")
    payload = read_json(path)
    return DUTContract.model_validate(payload)


def _default_observed_signals(contract: DUTContract) -> list[str]:
    if contract.observable_outputs:
        return list(contract.observable_outputs)
    if contract.handshake_signals:
        return list(contract.handshake_signals)
    if contract.ports:
        return [port.name for port in contract.ports[: min(3, len(contract.ports))]]
    return []


def _safe_timing_assumptions(contract: DUTContract) -> list[str]:
    if contract.timing.sequential_kind == SequentialKind.COMB:
        return ["Observe outputs after input stabilization.", "Do not infer internal state or undocumented storage."]
    if contract.timing.sequential_kind == SequentialKind.SEQ:
        return ["Advance through conservative clocked observations.", "Do not assume completion before it becomes externally visible."]
    return ["Do not assume fixed latency.", "Use reset-safe or protocol-safe observation windows only."]


def _protocol_safe_timing_assumptions(contract: DUTContract) -> list[str]:
    assumptions = _safe_timing_assumptions(contract)
    assumptions.append("Avoid fixed-cycle acceptance or completion checks unless the contract explicitly provides them.")
    return assumptions


def _should_add_edge_case(contract: DUTContract) -> bool:
    return any(port.direction == PortDirection.INPUT for port in contract.ports)


def _should_add_back_to_back_case(contract: DUTContract) -> bool:
    return bool(contract.handshake_groups) or contract.timing.sequential_kind == SequentialKind.SEQ


def _is_weak_contract(contract: DUTContract) -> bool:
    unknown_directions = sum(1 for port in contract.ports if port.direction == PortDirection.UNKNOWN)
    port_count = len(contract.ports) or 1
    return (
        contract.contract_confidence < 0.6
        or len(contract.ambiguities) >= 3
        or unknown_directions / port_count >= 0.4
        or contract.timing.sequential_kind == SequentialKind.UNKNOWN
        or not contract.observable_outputs
    )


def _case_confidence(contract: DUTContract, *, bonus: float = 0.0, penalty: float = 0.0) -> float:
    base = contract.contract_confidence - penalty + bonus
    return max(0.1, min(base, 0.95))


def _plan_strategy(contract: DUTContract, weak_contract: bool) -> str:
    if weak_contract:
        return "conservative_rule_based_from_contract_with_unresolved_safe_bias"
    if contract.timing.sequential_kind == SequentialKind.COMB:
        return "rule_based_comb_contract_first"
    if contract.timing.sequential_kind == SequentialKind.SEQ:
        return "rule_based_seq_contract_first"
    return "conservative_rule_based_from_contract"


def _estimate_plan_confidence(
    *,
    contract: DUTContract,
    cases: list[TestCasePlan],
    unresolved_items: list[str],
    weak_contract: bool,
) -> float:
    score = contract.contract_confidence
    if len(cases) >= 3:
        score += 0.05
    if any(case.category == TestCategory.PROTOCOL for case in cases):
        score += 0.05
    if any(case.category == TestCategory.RESET for case in cases):
        score += 0.03
    if weak_contract:
        score -= 0.15
    score -= min(0.25, 0.03 * len(unresolved_items))
    return max(0.1, min(score, 0.95))


def _build_plan_summary(plan: TestPlan) -> dict[str, object]:
    return {
        "module_name": plan.module_name,
        "based_on_contract": plan.based_on_contract,
        "plan_strategy": plan.plan_strategy,
        "case_count": len(plan.cases),
        "categories": [case.category for case in plan.cases],
        "unresolved_items": plan.unresolved_items,
        "plan_confidence": plan.plan_confidence,
    }


def _dedupe_in_place(items: list[str]) -> None:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    items[:] = unique_items
