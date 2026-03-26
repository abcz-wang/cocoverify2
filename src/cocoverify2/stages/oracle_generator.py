"""Rule-based oracle generation for Phase 3."""

from __future__ import annotations

from pathlib import Path
from statistics import fmean

from cocoverify2.core.errors import ArtifactError, ConfigurationError
from cocoverify2.core.models import (
    DUTContract,
    OracleCase,
    OracleCheck,
    OracleConfidenceSummary,
    OracleSpec,
    TemporalWindow,
    TestCasePlan,
    TestPlan,
)
from cocoverify2.core.types import OracleCheckType, OracleStrictness, SequentialKind, TemporalWindowMode
from cocoverify2.utils.files import ensure_dir, read_json, write_json, write_yaml
from cocoverify2.utils.logging import get_logger


class OracleGenerator:
    """Generate a conservative oracle artifact from contract and test-plan artifacts."""

    __test__ = False

    def __init__(self) -> None:
        """Initialize the generator with a stage-scoped logger."""
        self.logger = get_logger(__name__)

    def run(
        self,
        *,
        contract: DUTContract,
        plan: TestPlan,
        task_description: str | None,
        spec_text: str | None,
        out_dir: Path,
        based_on_contract: str = "",
        based_on_plan: str = "",
    ) -> OracleSpec:
        """Generate and persist a structured oracle artifact."""
        if not contract.module_name:
            raise ConfigurationError("Oracle generation requires a contract with a module_name.")
        if not plan.module_name:
            raise ConfigurationError("Oracle generation requires a test plan with a module_name.")
        if contract.module_name != plan.module_name:
            raise ConfigurationError(
                f"Contract/plan module mismatch: contract='{contract.module_name}', plan='{plan.module_name}'."
            )

        self.logger.debug(
            "Generating oracle for module=%s plan_cases=%d contract_confidence=%.2f plan_confidence=%.2f",
            contract.module_name,
            len(plan.cases),
            contract.contract_confidence,
            plan.plan_confidence,
        )

        weak_contract = _is_weak_contract(contract, plan)
        assumptions = list(contract.assumptions) + list(plan.assumptions)
        unresolved_items = list(contract.ambiguities) + list(plan.unresolved_items)
        protocol_oracles: list[OracleCase] = []
        functional_oracles: list[OracleCase] = []
        property_oracles: list[OracleCase] = []
        covered_case_ids: set[str] = set()

        if contract.timing.sequential_kind == SequentialKind.UNKNOWN:
            unresolved_items.append(
                "Timing remains unresolved; oracle checks avoid exact-cycle requirements and prefer event-based or safety-style windows."
            )
        if weak_contract:
            unresolved_items.append(
                "Contract or plan confidence is limited; oracle generation is intentionally conservative and may omit value-level functional checks."
            )

        for plan_case in plan.cases:
            protocol_case = self._build_protocol_oracle_case(contract=contract, plan_case=plan_case, weak_contract=weak_contract)
            if protocol_case is not None:
                protocol_oracles.append(protocol_case)
                covered_case_ids.add(plan_case.case_id)

            functional_case = self._build_functional_oracle_case(contract=contract, plan_case=plan_case, weak_contract=weak_contract)
            if functional_case is not None:
                functional_oracles.append(functional_case)
                covered_case_ids.add(plan_case.case_id)

            property_case = self._build_property_oracle_case(contract=contract, plan_case=plan_case, weak_contract=weak_contract)
            if property_case is not None:
                property_oracles.append(property_case)
                covered_case_ids.add(plan_case.case_id)

            if protocol_case is None and functional_case is None and property_case is None:
                unresolved_items.append(
                    f"No concrete oracle checks were generated for plan case '{plan_case.case_id}'; the case remains unresolved until later runtime observation rules are added."
                )

        if task_description:
            assumptions.append("Task description was provided and only used as a low-risk oracle hint.")
        if spec_text:
            assumptions.append("Spec text was provided and only used where it reinforced already-known contract or plan constraints.")

        for plan_case in plan.cases:
            if plan_case.case_id not in covered_case_ids:
                unresolved_items.append(
                    f"Plan case '{plan_case.case_id}' is only partially covered by the Phase 3 oracle artifact and may need richer checks in later stages."
                )

        _dedupe_in_place(assumptions)
        _dedupe_in_place(unresolved_items)
        confidence_summary = _estimate_oracle_confidence(
            contract=contract,
            plan=plan,
            protocol_oracles=protocol_oracles,
            functional_oracles=functional_oracles,
            property_oracles=property_oracles,
            unresolved_items=unresolved_items,
            weak_contract=weak_contract,
        )
        oracle = OracleSpec(
            module_name=contract.module_name,
            based_on_contract=based_on_contract or plan.based_on_contract or contract.module_name,
            based_on_plan=based_on_plan or plan.module_name,
            oracle_strategy=_oracle_strategy(contract=contract, plan=plan, weak_contract=weak_contract),
            protocol_oracles=protocol_oracles,
            functional_oracles=functional_oracles,
            property_oracles=property_oracles,
            unresolved_items=unresolved_items,
            assumptions=assumptions,
            oracle_confidence=confidence_summary,
        )
        self._dump_oracle_artifacts(oracle, out_dir)
        self.logger.info(
            "Generated oracle artifact for '%s' with %d protocol, %d functional, %d property cases.",
            oracle.module_name,
            len(protocol_oracles),
            len(functional_oracles),
            len(property_oracles),
        )
        return oracle

    def run_from_artifacts(
        self,
        *,
        contract_path: Path,
        plan_path: Path,
        task_description: str | None,
        spec_text: str | None,
        out_dir: Path,
    ) -> OracleSpec:
        """Load contract/plan artifacts and generate an oracle artifact."""
        contract = load_contract_artifact(contract_path)
        plan = load_test_plan_artifact(plan_path)
        return self.run(
            contract=contract,
            plan=plan,
            task_description=task_description,
            spec_text=spec_text,
            out_dir=out_dir,
            based_on_contract=str(contract_path),
            based_on_plan=str(plan_path),
        )

    def _build_protocol_oracle_case(
        self,
        *,
        contract: DUTContract,
        plan_case: TestCasePlan,
        weak_contract: bool,
    ) -> OracleCase | None:
        checks: list[OracleCheck] = []
        assumptions: list[str] = []
        unresolved_items: list[str] = []
        notes: list[str] = []
        observed_signals = _sanitize_observed_signals(plan_case.observed_signals, contract)
        coverage_tags = set(plan_case.coverage_tags)

        if plan_case.category == "reset" and contract.resets:
            reset_name = contract.resets[0].name
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.PROTOCOL,
                    ordinal=1,
                    description="Treat reset assertion/release as a control event and require reset-safe interface behavior.",
                    observed_signals=observed_signals,
                    trigger_condition=f"When reset '{reset_name}' is asserted and later released according to the inferred polarity.",
                    pass_condition="No acceptance, completion, or externally visible functional progress is claimed solely during reset; post-release observation waits for stable, externally visible behavior.",
                    temporal_window=_reset_window(contract),
                    strictness=OracleStrictness.CONSERVATIVE,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.02),
                    notes=["Reset is used as an anchor only; it is not treated as a business output."],
                )
            )
            notes.append("Reset oracle focuses on control-safe behavior instead of value-specific output claims.")
        elif "valid_ready" in coverage_tags:
            valid_signal = _signal_for_tag(contract, coverage_tags, "valid_ready", "valid")
            ready_signal = _signal_for_tag(contract, coverage_tags, "valid_ready", "ready")
            if valid_signal and ready_signal:
                if "acceptance" in coverage_tags:
                    checks.append(
                        _make_check(
                            case_id=plan_case.case_id,
                            check_type=OracleCheckType.PROTOCOL,
                            ordinal=len(checks) + 1,
                            description="Recognize acceptance only when valid and ready are simultaneously asserted.",
                            observed_signals=_merge_signals(observed_signals, [valid_signal, ready_signal]),
                            trigger_condition=f"When '{valid_signal}' and '{ready_signal}' overlap in the observation window.",
                            pass_condition="A transaction may be considered accepted only on valid/ready overlap; downstream completion is not required in the same observation point or any predetermined later observation point.",
                            temporal_window=_protocol_window(contract, guarded=False),
                            strictness=OracleStrictness.CONSERVATIVE,
                            confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.03),
                            notes=["Acceptance-safe oracle; not a completion oracle."],
                        )
                    )
                if "backpressure" in coverage_tags:
                    checks.append(
                        _make_check(
                            case_id=plan_case.case_id,
                            check_type=OracleCheckType.PROTOCOL,
                            ordinal=len(checks) + 1,
                            description="Guard against claiming acceptance or completion while ready is low.",
                            observed_signals=_merge_signals(observed_signals, [valid_signal, ready_signal]),
                            trigger_condition=f"When '{valid_signal}' is asserted while '{ready_signal}' remains low or unavailable for acceptance.",
                            pass_condition="Progress may stall or be deferred; the oracle does not require completion or acceptance until a later legal handshake is observed.",
                            temporal_window=_protocol_window(contract, guarded=True),
                            strictness=OracleStrictness.GUARDED,
                            confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.03),
                            notes=["Backpressure-safe oracle avoids fixed-throughput assumptions."],
                        )
                    )
                if "persistence" in coverage_tags:
                    checks.append(
                        _make_check(
                            case_id=plan_case.case_id,
                            check_type=OracleCheckType.PROTOCOL,
                            ordinal=len(checks) + 1,
                            description="Observe source-side persistence or other safe waiting behavior before acceptance.",
                            observed_signals=_merge_signals(observed_signals, [valid_signal, ready_signal]),
                            trigger_condition=f"When '{valid_signal}' stays asserted across multiple conservative observation opportunities before '{ready_signal}' allows acceptance.",
                            pass_condition="The interface remains externally consistent while waiting; completion is not claimed before a legal acceptance event is visible.",
                            temporal_window=_protocol_window(contract, guarded=True),
                            strictness=OracleStrictness.GUARDED,
                            confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.05),
                            notes=["Persistence semantics remain heuristic and are intentionally checked in a safety-style form."],
                        )
                    )
            else:
                unresolved_items.append(
                    f"Plan case '{plan_case.case_id}' references valid_ready behavior, but the matching handshake signals could not be resolved confidently from the contract."
                )
        elif "start_done" in coverage_tags:
            start_signal = _signal_for_tag(contract, coverage_tags, "start_done", "start")
            done_signal = _signal_for_tag(contract, coverage_tags, "start_done", "done")
            if start_signal and done_signal:
                checks.append(
                    _make_check(
                        case_id=plan_case.case_id,
                        check_type=OracleCheckType.PROTOCOL,
                        ordinal=1,
                        description="Observe completion only after a visible start event has occurred.",
                        observed_signals=_merge_signals(observed_signals, [start_signal, done_signal]),
                        trigger_condition=f"When '{start_signal}' is pulsed or asserted for a legal operation.",
                        pass_condition=f"'{done_signal}' may be treated as completion only after the start event; no predetermined completion latency is assumed.",
                        temporal_window=_protocol_window(contract, guarded=True),
                        strictness=OracleStrictness.CONSERVATIVE,
                        confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.03),
                        notes=["Completion-safe oracle uses event ordering, not cycle counting."],
                    )
                )
        elif "req_ack" in coverage_tags:
            req_signal = _signal_for_tag(contract, coverage_tags, "req_ack", "req")
            ack_signal = _signal_for_tag(contract, coverage_tags, "req_ack", "ack")
            if req_signal and ack_signal:
                checks.append(
                    _make_check(
                        case_id=plan_case.case_id,
                        check_type=OracleCheckType.PROTOCOL,
                        ordinal=1,
                        description="Pair request and acknowledge conservatively without requiring exact-cycle acknowledgement.",
                        observed_signals=_merge_signals(observed_signals, [req_signal, ack_signal]),
                        trigger_condition=f"When '{req_signal}' is asserted for a legal request.",
                        pass_condition=f"'{ack_signal}' may indicate acceptance or completion only after a visible request; the oracle remains event-based when timing is not explicit.",
                        temporal_window=_protocol_window(contract, guarded=True),
                        strictness=OracleStrictness.CONSERVATIVE,
                        confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.03),
                        notes=["Req/ack protocol semantics remain heuristic until later stages add stronger runtime evidence."],
                    )
                )
        elif plan_case.category == "back_to_back" and contract.handshake_groups:
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.PROTOCOL,
                    ordinal=1,
                    description="Require repeated operations to be distinguished by separate protocol-visible acceptance or completion events.",
                    observed_signals=observed_signals,
                    trigger_condition="When the linked plan applies repeated or back-to-back operations with minimal spacing.",
                    pass_condition="A second operation is not treated as accepted or complete unless a distinct later protocol-visible event is observed.",
                    temporal_window=_protocol_window(contract, guarded=True),
                    strictness=OracleStrictness.GUARDED,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.05),
                    notes=["Repeated-operation oracle avoids throughput and queue-depth assumptions."],
                )
            )

        if not checks:
            return None
        assumptions.append("Handshake groups are treated as heuristic anchors, not fully proven protocol specifications.")
        if weak_contract:
            notes.append("Protocol oracle strictness is downgraded because the contract or plan is weak.")
        return _make_oracle_case(
            prefix="protocol",
            plan_case=plan_case,
            checks=checks,
            assumptions=assumptions,
            unresolved_items=unresolved_items,
            confidence=_average_check_confidence(checks),
            notes=notes,
        )

    def _build_functional_oracle_case(
        self,
        *,
        contract: DUTContract,
        plan_case: TestCasePlan,
        weak_contract: bool,
    ) -> OracleCase | None:
        checks: list[OracleCheck] = []
        assumptions: list[str] = []
        unresolved_items: list[str] = []
        notes: list[str] = []
        observed_signals = _functional_observed_signals(plan_case.observed_signals, contract)

        if not observed_signals:
            unresolved_items.append(
                f"No functional oracle was generated for plan case '{plan_case.case_id}' because no observable non-control outputs were available."
            )
            return _make_oracle_case(
                prefix="functional",
                plan_case=plan_case,
                checks=[],
                assumptions=assumptions,
                unresolved_items=unresolved_items,
                confidence=0.05,
                notes=["Functional oracle intentionally omitted due to missing observable outputs."],
            ) if _should_emit_empty_functional_case(contract, plan_case) else None

        if weak_contract and contract.timing.sequential_kind != SequentialKind.COMB:
            unresolved_items.append(
                f"Value-level functional oracle for case '{plan_case.case_id}' is intentionally deferred because timing or interface confidence is too weak."
            )
            return _make_oracle_case(
                prefix="functional",
                plan_case=plan_case,
                checks=[],
                assumptions=assumptions,
                unresolved_items=unresolved_items,
                confidence=0.08,
                notes=["Weak-contract path emits an explicit empty functional oracle case instead of guessing values."],
            ) if _should_emit_empty_functional_case(contract, plan_case) else None

        if plan_case.category == "basic" and contract.timing.sequential_kind == SequentialKind.COMB:
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.FUNCTIONAL,
                    ordinal=1,
                    description="Observe that legal input changes are reflected on the observable outputs without state dependence.",
                    observed_signals=observed_signals,
                    trigger_condition="When the linked basic stimulus applies legal representative input patterns.",
                    pass_condition="Observable outputs respond consistently to the applied inputs without relying on hidden state or exact-cycle timing.",
                    temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="input_stable"),
                    strictness=OracleStrictness.CONSERVATIVE,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case),
                    notes=["Combinational functional oracle stays descriptive and avoids inventing a full truth table."],
                )
            )
        elif plan_case.category == "edge" and contract.timing.sequential_kind == SequentialKind.COMB:
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.FUNCTIONAL,
                    ordinal=1,
                    description="Observe stable, externally consistent response to boundary-value input patterns.",
                    observed_signals=observed_signals,
                    trigger_condition="When the linked edge case applies zero-like, one-like, or width-boundary patterns.",
                    pass_condition="Boundary-value outputs remain externally consistent and do not require hidden state or fixed-latency interpretation.",
                    temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="boundary_inputs_stable"),
                    strictness=OracleStrictness.CONSERVATIVE,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.02),
                    notes=["Boundary oracle is value-oriented but intentionally generic."],
                )
            )
        elif plan_case.category == "reset":
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.FUNCTIONAL,
                    ordinal=1,
                    description="After reset release, observable outputs should reach a stable externally visible state before functional checking resumes.",
                    observed_signals=observed_signals,
                    trigger_condition="When reset is released after a valid assertion interval.",
                    pass_condition="Observable outputs settle to a stable, externally usable state without relying on undocumented exact-cycle convergence.",
                    temporal_window=_reset_window(contract),
                    strictness=OracleStrictness.CONSERVATIVE,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.03),
                    notes=["Reset functional oracle does not invent specific reset values."],
                )
            )
        elif plan_case.category in {"basic", "edge", "back_to_back"} and contract.timing.sequential_kind == SequentialKind.SEQ:
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.FUNCTIONAL,
                    ordinal=1,
                    description="Observe externally visible state progress after a legal operation.",
                    observed_signals=observed_signals,
                    trigger_condition="When the linked plan applies one or more legal sequential operations.",
                    pass_condition="At least one observable output or progress indicator eventually updates in a manner consistent with state progress; no exact-cycle update is required.",
                    temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="operation_applied"),
                    strictness=OracleStrictness.CONSERVATIVE,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.02),
                    notes=["Sequential functional oracle remains event-based unless a future contract explicitly provides fixed latency."],
                )
            )

        if not checks and _should_emit_empty_functional_case(contract, plan_case):
            unresolved_items.append(
                f"No value-level functional oracle was generated for case '{plan_case.case_id}' because the case is safer to cover with protocol/property checks only."
            )
            return _make_oracle_case(
                prefix="functional",
                plan_case=plan_case,
                checks=[],
                assumptions=assumptions,
                unresolved_items=unresolved_items,
                confidence=0.05,
                notes=["Functional oracle intentionally omitted for this case."],
            )

        if not checks:
            return None
        if contract.timing.sequential_kind == SequentialKind.UNKNOWN:
            assumptions.append("Functional checks remain event-based because timing is unresolved.")
        return _make_oracle_case(
            prefix="functional",
            plan_case=plan_case,
            checks=checks,
            assumptions=assumptions,
            unresolved_items=unresolved_items,
            confidence=_average_check_confidence(checks),
            notes=notes,
        )

    def _build_property_oracle_case(
        self,
        *,
        contract: DUTContract,
        plan_case: TestCasePlan,
        weak_contract: bool,
    ) -> OracleCase | None:
        checks: list[OracleCheck] = []
        assumptions: list[str] = []
        unresolved_items: list[str] = []
        notes: list[str] = []
        observed_signals = _sanitize_observed_signals(plan_case.observed_signals, contract)
        coverage_tags = set(plan_case.coverage_tags)

        if plan_case.category == "reset":
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.PROPERTY,
                    ordinal=1,
                    description="Do not infer business-level completion or acceptance solely from reset activity.",
                    observed_signals=observed_signals,
                    trigger_condition="While reset is asserted or being released.",
                    pass_condition="No safety property is violated by treating reset as control-only; later functional claims require separate post-reset evidence.",
                    temporal_window=_reset_window(contract),
                    strictness=OracleStrictness.GUARDED,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.01),
                    notes=["Clock/reset remain anchors and are not emitted as business outputs."],
                )
            )
        elif "backpressure" in coverage_tags:
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.PROPERTY,
                    ordinal=1,
                    description="Guardrail: do not declare acceptance or completion while backpressure is active.",
                    observed_signals=observed_signals,
                    trigger_condition="When ready is low during an attempted transfer.",
                    pass_condition="The design is only required to avoid premature acceptance/completion claims; it is not required to make progress under backpressure.",
                    temporal_window=_protocol_window(contract, guarded=True),
                    strictness=OracleStrictness.GUARDED,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.02),
                    notes=["Property oracle is ambiguity-aware and avoids overcommitting to stall behavior."],
                )
            )
        elif "acceptance" in coverage_tags and "valid_ready" in coverage_tags:
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.PROPERTY,
                    ordinal=1,
                    description="Guardrail: acceptance requires legal valid/ready overlap.",
                    observed_signals=observed_signals,
                    trigger_condition="Whenever the case tries to interpret a transfer as accepted.",
                    pass_condition="Acceptance is only credited on legal handshake overlap and is never inferred from a later output alone.",
                    temporal_window=_protocol_window(contract, guarded=True),
                    strictness=OracleStrictness.GUARDED,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.01),
                    notes=["Prevents false positives from incorrectly inferring transaction acceptance."],
                )
            )
        elif "persistence" in coverage_tags:
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.PROPERTY,
                    ordinal=1,
                    description="Guardrail: do not declare completion before a legal acceptance event becomes visible.",
                    observed_signals=observed_signals,
                    trigger_condition="While a source is waiting for the protocol to permit acceptance.",
                    pass_condition="Completion or success is not credited before a later legal acceptance or progress event is externally visible.",
                    temporal_window=_protocol_window(contract, guarded=True),
                    strictness=OracleStrictness.GUARDED,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.03),
                    notes=["Safety-style property used because persistence semantics are not fully proven."],
                )
            )
        elif "start_done" in coverage_tags:
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.PROPERTY,
                    ordinal=1,
                    description="Guardrail: done cannot be treated as completion without a prior visible start event.",
                    observed_signals=observed_signals,
                    trigger_condition="Whenever completion is claimed for the linked start/done interaction.",
                    pass_condition="A completion claim requires an earlier start event in the same scenario; exact-cycle completion is not required.",
                    temporal_window=_protocol_window(contract, guarded=True),
                    strictness=OracleStrictness.GUARDED,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.02),
                    notes=["Avoids false positives from orphan done pulses or misinterpreted combinational outputs."],
                )
            )
        elif "req_ack" in coverage_tags:
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.PROPERTY,
                    ordinal=1,
                    description="Guardrail: acknowledge must be paired with a prior request, not inferred in isolation.",
                    observed_signals=observed_signals,
                    trigger_condition="Whenever the linked case interprets an acknowledge event as progress.",
                    pass_condition="Progress requires a request-before-ack ordering; no exact-cycle ack timing is assumed.",
                    temporal_window=_protocol_window(contract, guarded=True),
                    strictness=OracleStrictness.GUARDED,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.02),
                    notes=["Pairing-safe property for heuristic req/ack interfaces."],
                )
            )
        elif plan_case.category == "negative":
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.PROPERTY,
                    ordinal=1,
                    description="Guardrail: illegal or constrained inputs do not require normal completion or success signaling.",
                    observed_signals=observed_signals,
                    trigger_condition="When the linked plan probes documented illegal or constrained inputs.",
                    pass_condition="The oracle only requires safe non-violation behavior and does not invent undocumented error responses.",
                    temporal_window=TemporalWindow(mode=TemporalWindowMode.UNBOUNDED_SAFE, anchor="illegal_input_observation"),
                    strictness=OracleStrictness.GUARDED,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.04),
                    notes=["Negative behavior is guarded by explicit contract constraints only."],
                )
            )
        elif plan_case.category == "back_to_back":
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.PROPERTY,
                    ordinal=1,
                    description="Guardrail: repeated operations must not collapse into a single ambiguous completion claim.",
                    observed_signals=observed_signals,
                    trigger_condition="When the linked case applies repeated or back-to-back operations.",
                    pass_condition="Observed progress remains order-aware and non-contradictory even when exact queueing semantics are unresolved.",
                    temporal_window=TemporalWindow(mode=TemporalWindowMode.UNBOUNDED_SAFE, anchor="repeated_operations"),
                    strictness=OracleStrictness.GUARDED,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.03),
                    notes=["Stability-style property used instead of throughput-specific claims."],
                )
            )
        else:
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.PROPERTY,
                    ordinal=1,
                    description="Guardrail: avoid fixed-cycle expectations unless the contract later proves them.",
                    observed_signals=observed_signals,
                    trigger_condition="Whenever the linked case evaluates externally visible progress.",
                    pass_condition="The oracle only requires conservative, externally visible progress or stability and forbids hidden exact-cycle assumptions.",
                    temporal_window=_safe_window(contract),
                    strictness=OracleStrictness.GUARDED,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, penalty=0.01),
                    notes=["Default property oracle protects against over-specific later render behavior."],
                )
            )

        if weak_contract:
            unresolved_items.append(
                f"Property oracle for case '{plan_case.case_id}' is acting as a guardrail because stronger functional semantics are not yet justified."
            )
        return _make_oracle_case(
            prefix="property",
            plan_case=plan_case,
            checks=checks,
            assumptions=assumptions,
            unresolved_items=unresolved_items,
            confidence=_average_check_confidence(checks),
            notes=notes,
        )

    def _dump_oracle_artifacts(self, oracle: OracleSpec, out_dir: Path) -> None:
        oracle_dir = ensure_dir(out_dir / "oracle")
        write_json(oracle_dir / "oracle.json", oracle.model_dump(mode="json"))
        write_yaml(oracle_dir / "oracle_summary.yaml", _build_oracle_summary(oracle))
        self.logger.info("Wrote oracle artifacts to %s", oracle_dir)


def load_contract_artifact(path: Path) -> DUTContract:
    """Load a ``DUTContract`` artifact from JSON."""
    if not path.exists():
        raise ArtifactError(f"Contract artifact does not exist: {path}")
    return DUTContract.model_validate(read_json(path))



def load_test_plan_artifact(path: Path) -> TestPlan:
    """Load a ``TestPlan`` artifact from JSON."""
    if not path.exists():
        raise ArtifactError(f"Test plan artifact does not exist: {path}")
    return TestPlan.model_validate(read_json(path))



def _functional_observed_signals(plan_observed_signals: list[str], contract: DUTContract) -> list[str]:
    signals = _sanitize_observed_signals(plan_observed_signals, contract)
    excluded = {clock.name for clock in contract.clocks} | {reset.name for reset in contract.resets} | set(contract.handshake_signals)
    filtered = [signal for signal in signals if signal not in excluded]
    if filtered:
        return filtered
    fallback = [signal for signal in contract.observable_outputs if signal not in excluded]
    return fallback



def _sanitize_observed_signals(plan_observed_signals: list[str], contract: DUTContract) -> list[str]:
    excluded = {clock.name for clock in contract.clocks} | {reset.name for reset in contract.resets}
    filtered = [signal for signal in plan_observed_signals if signal not in excluded]
    if filtered:
        return _deduped(filtered)
    fallback = [signal for signal in contract.observable_outputs + contract.handshake_signals if signal not in excluded]
    return _deduped(fallback)



def _signal_for_tag(contract: DUTContract, coverage_tags: set[str], pattern: str, role: str) -> str | None:
    preferred_groups = [tag for tag in coverage_tags if tag not in {"protocol", pattern, "acceptance", "backpressure", "persistence", "completion"}]
    for group in contract.handshake_groups:
        if group.pattern != pattern:
            continue
        if preferred_groups and group.group_name not in preferred_groups:
            continue
        signal_name = group.signals.get(role)
        if signal_name:
            return signal_name
    for group in contract.handshake_groups:
        if group.pattern == pattern and role in group.signals:
            return group.signals[role]
    return None



def _reset_window(contract: DUTContract) -> TemporalWindow:
    if contract.resets and contract.resets[0].stabilization_cycles is not None:
        return TemporalWindow(
            mode=TemporalWindowMode.BOUNDED_RANGE,
            min_cycles=0,
            max_cycles=contract.resets[0].stabilization_cycles,
            anchor="reset_release",
        )
    return TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="reset_release")



def _protocol_window(contract: DUTContract, *, guarded: bool) -> TemporalWindow:
    if guarded or contract.timing.sequential_kind == SequentialKind.UNKNOWN:
        return TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="protocol_event")
    if contract.timing.sequential_kind == SequentialKind.SEQ:
        return TemporalWindow(mode=TemporalWindowMode.BOUNDED_RANGE, min_cycles=0, max_cycles=contract.timing.sampling_window_cycles, anchor="protocol_event")
    return TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="protocol_event")



def _safe_window(contract: DUTContract) -> TemporalWindow:
    if contract.timing.sequential_kind == SequentialKind.COMB:
        return TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="input_stable")
    if contract.timing.sequential_kind == SequentialKind.SEQ:
        return TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="operation_applied")
    return TemporalWindow(mode=TemporalWindowMode.UNBOUNDED_SAFE, anchor="externally_visible_progress")



def _should_emit_empty_functional_case(contract: DUTContract, plan_case: TestCasePlan) -> bool:
    return plan_case.category in {"basic", "reset", "edge"} and (not contract.observable_outputs or contract.contract_confidence < 0.6)



def _is_weak_contract(contract: DUTContract, plan: TestPlan) -> bool:
    return (
        contract.contract_confidence < 0.6
        or plan.plan_confidence < 0.6
        or contract.timing.sequential_kind == SequentialKind.UNKNOWN
        or len(contract.ambiguities) >= 3
        or len(plan.unresolved_items) >= 3
        or not contract.observable_outputs
    )



def _oracle_case_confidence(
    *,
    contract: DUTContract,
    plan_case: TestCasePlan,
    bonus: float = 0.0,
    penalty: float = 0.0,
) -> float:
    base = min(contract.contract_confidence, plan_case.confidence)
    return max(0.05, min(base + bonus - penalty, 0.95))



def _oracle_strategy(contract: DUTContract, plan: TestPlan, weak_contract: bool) -> str:
    if weak_contract:
        return "conservative_rule_based_oracle_with_unresolved_safe_bias"
    if contract.timing.sequential_kind == SequentialKind.COMB:
        return "rule_based_oracle_comb_contract_and_plan_first"
    if contract.timing.sequential_kind == SequentialKind.SEQ:
        return "rule_based_oracle_seq_contract_and_plan_first"
    return "conservative_rule_based_oracle_from_contract_and_plan"



def _estimate_oracle_confidence(
    *,
    contract: DUTContract,
    plan: TestPlan,
    protocol_oracles: list[OracleCase],
    functional_oracles: list[OracleCase],
    property_oracles: list[OracleCase],
    unresolved_items: list[str],
    weak_contract: bool,
) -> OracleConfidenceSummary:
    protocol_confidence = _average_case_confidence(protocol_oracles)
    functional_confidence = _average_case_confidence(functional_oracles)
    property_confidence = _average_case_confidence(property_oracles)
    active_confidences = [
        confidence
        for confidence in (protocol_confidence, functional_confidence, property_confidence)
        if confidence > 0.0
    ]
    overall_confidence = fmean(active_confidences) if active_confidences else 0.1
    overall_confidence -= min(0.25, 0.02 * len(unresolved_items))
    if weak_contract:
        overall_confidence -= 0.12
    if not functional_oracles and contract.observable_outputs:
        overall_confidence -= 0.08
    overall_confidence = max(0.05, min(overall_confidence, 0.95))
    return OracleConfidenceSummary(
        overall_confidence=overall_confidence,
        protocol_confidence=protocol_confidence,
        functional_confidence=functional_confidence,
        property_confidence=property_confidence,
    )



def _average_case_confidence(cases: list[OracleCase]) -> float:
    if not cases:
        return 0.0
    return max(0.05, min(fmean(case.confidence for case in cases), 0.95))



def _average_check_confidence(checks: list[OracleCheck]) -> float:
    if not checks:
        return 0.05
    return max(0.05, min(fmean(check.confidence for check in checks), 0.95))



def _make_oracle_case(
    *,
    prefix: str,
    plan_case: TestCasePlan,
    checks: list[OracleCheck],
    assumptions: list[str],
    unresolved_items: list[str],
    confidence: float,
    notes: list[str],
) -> OracleCase:
    _dedupe_in_place(assumptions)
    _dedupe_in_place(unresolved_items)
    _dedupe_in_place(notes)
    return OracleCase(
        case_id=f"{prefix}_{plan_case.case_id}",
        linked_plan_case_id=plan_case.case_id,
        category=plan_case.category,
        checks=checks,
        assumptions=assumptions,
        unresolved_items=unresolved_items,
        confidence=max(0.05, min(confidence, 0.95)),
        source="rule_based",
        notes=notes,
    )



def _make_check(
    *,
    case_id: str,
    check_type: OracleCheckType,
    ordinal: int,
    description: str,
    observed_signals: list[str],
    trigger_condition: str,
    pass_condition: str,
    temporal_window: TemporalWindow,
    strictness: OracleStrictness,
    confidence: float,
    notes: list[str],
) -> OracleCheck:
    return OracleCheck(
        check_id=f"{case_id}_{check_type.value}_{ordinal:03d}",
        check_type=check_type,
        description=description,
        observed_signals=_deduped(observed_signals),
        trigger_condition=trigger_condition,
        pass_condition=pass_condition,
        temporal_window=temporal_window,
        strictness=strictness,
        confidence=max(0.05, min(confidence, 0.95)),
        source="rule_based",
        notes=notes,
    )



def _build_oracle_summary(oracle: OracleSpec) -> dict[str, object]:
    return {
        "module_name": oracle.module_name,
        "based_on_contract": oracle.based_on_contract,
        "based_on_plan": oracle.based_on_plan,
        "oracle_strategy": oracle.oracle_strategy,
        "protocol_case_count": len(oracle.protocol_oracles),
        "functional_case_count": len(oracle.functional_oracles),
        "property_case_count": len(oracle.property_oracles),
        "unresolved_items": oracle.unresolved_items,
        "oracle_confidence": oracle.oracle_confidence.model_dump(mode="json"),
    }



def _merge_signals(primary: list[str], extra: list[str]) -> list[str]:
    return _deduped(primary + extra)



def _deduped(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items



def _dedupe_in_place(items: list[str]) -> None:
    items[:] = _deduped(items)
