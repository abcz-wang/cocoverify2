"""Rule-based test plan generation for Phase 2."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from statistics import fmean

from cocoverify2.core.config import LLMConfig
from cocoverify2.core.errors import ArtifactError, ConfigurationError
from cocoverify2.core.models import DUTContract, HandshakeGroup, TestCasePlan, TestPlan
from cocoverify2.core.types import GenerationMode, PortDirection, SequentialKind, TestCategory
from cocoverify2.llm.client import LLMClient
from cocoverify2.llm.prompts import build_plan_system_prompt, build_plan_user_prompt
from cocoverify2.llm.validators import parse_plan_augmentation, validate_plan_augmentation
from cocoverify2.utils.files import ensure_dir, read_json, write_json, write_text, write_yaml
from cocoverify2.utils.logging import get_logger


class TestPlanGenerator:
    """Generate a conservative, structured test plan from a ``DUTContract``."""

    __test__ = False

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """Initialize the generator with a stage-scoped logger."""
        self.logger = get_logger(__name__)
        self.llm_client = llm_client

    def run(
        self,
        *,
        contract: DUTContract,
        task_description: str | None,
        spec_text: str | None,
        out_dir: Path,
        based_on_contract: str = "",
        generation_mode: GenerationMode | str = GenerationMode.RULE_BASED,
        llm_config: LLMConfig | None = None,
    ) -> TestPlan:
        """Generate and persist a ``TestPlan`` from a validated contract."""
        generation_mode = GenerationMode(generation_mode)
        baseline_plan = self._generate_rule_based_plan(
            contract=contract,
            task_description=task_description,
            spec_text=spec_text,
            based_on_contract=based_on_contract,
        )
        if generation_mode == GenerationMode.RULE_BASED:
            baseline_plan.plan_strategy = "rule_based_conservative"
            self._dump_plan_artifacts(baseline_plan, out_dir)
            self.logger.info(
                "Generated %d rule-based plan cases for module '%s' with plan_confidence=%.2f",
                len(baseline_plan.cases),
                baseline_plan.module_name,
                baseline_plan.plan_confidence,
            )
            return baseline_plan

        llm_config = llm_config or LLMConfig()
        hybrid_plan = self._apply_hybrid_augmentation(
            contract=contract,
            baseline_plan=baseline_plan,
            task_description=task_description,
            spec_text=spec_text,
            out_dir=out_dir,
            llm_config=llm_config,
        )
        self._dump_plan_artifacts(hybrid_plan, out_dir)
        self.logger.info(
            "Generated %d hybrid plan cases for module '%s' with plan_confidence=%.2f",
            len(hybrid_plan.cases),
            hybrid_plan.module_name,
            hybrid_plan.plan_confidence,
        )
        return hybrid_plan

    def _generate_rule_based_plan(
        self,
        *,
        contract: DUTContract,
        task_description: str | None,
        spec_text: str | None,
        based_on_contract: str = "",
    ) -> TestPlan:
        """Generate the baseline conservative rule-based plan without persisting it."""
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
        drivable_inputs = _drivable_input_names(contract)
        minimal_plan_only = _should_minimize_plan(
            contract=contract,
            observed_signals=observed_signals,
            drivable_inputs=drivable_inputs,
        )
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
                    stimulus_signals=[reset.name for reset in contract.resets[:1]],
                    expected_properties=[
                        "Observed outputs or protocol-visible signals settle to a stable, non-X post-reset state.",
                        "No fixed-cycle completion is assumed during reset recovery.",
                    ],
                    observed_signals=observed_signals,
                    timing_assumptions=_safe_timing_assumptions(contract),
                    dependencies=[],
                    coverage_tags=["reset", "initialization", "stability"],
                    semantic_tags=["ambiguity_preserving"],
                    priority=1,
                    confidence=_case_confidence(contract, bonus=0.05),
                    notes=["Reset polarity may still be heuristic if the contract marks it ambiguous."],
                )
            )

        cases.append(self._build_basic_case(contract=contract, counters=counters, observed_signals=observed_signals))

        if not minimal_plan_only and _should_add_edge_case(contract):
            cases.append(self._build_edge_case(contract=contract, counters=counters, observed_signals=observed_signals))

        if not minimal_plan_only:
            for group in contract.handshake_groups:
                cases.extend(self._build_handshake_cases(contract=contract, group=group, counters=counters, observed_signals=observed_signals))

        if not minimal_plan_only and _should_add_back_to_back_case(contract):
            cases.append(self._build_back_to_back_case(contract=contract, counters=counters, observed_signals=observed_signals))

        if not minimal_plan_only and contract.illegal_input_constraints:
            cases.append(self._build_negative_case(contract=contract, counters=counters, observed_signals=observed_signals))
        elif contract.illegal_input_constraints:
            unresolved_items.append(
                "Negative or illegal-input behavior is documented, but the current contract does not support deterministic mainline stimulus for those constraints."
            )
        elif weak_contract and contract.timing.sequential_kind == SequentialKind.UNKNOWN:
            unresolved_items.append("Negative or illegal-input behavior is not planned because the contract does not provide reliable constraints.")

        if task_description:
            assumptions.append("Task description was provided and only used as a low-risk planning hint.")
        if spec_text:
            assumptions.append("Spec text was provided and only used where it did not contradict the contract.")

        cases = [_calibrate_case_execution_policy(contract=contract, case=case) for case in cases]
        _dedupe_in_place(unresolved_items)
        _dedupe_in_place(assumptions)
        return TestPlan(
            module_name=contract.module_name,
            based_on_contract=based_on_contract or contract.module_name,
            plan_strategy="rule_based_conservative",
            cases=cases,
            unresolved_items=unresolved_items,
            assumptions=assumptions,
            plan_confidence=_estimate_plan_confidence(contract=contract, cases=cases, unresolved_items=unresolved_items, weak_contract=weak_contract),
        )

    def run_from_artifact(
        self,
        *,
        contract_path: Path,
        task_description: str | None,
        spec_text: str | None,
        out_dir: Path,
        generation_mode: GenerationMode | str = GenerationMode.RULE_BASED,
        llm_config: LLMConfig | None = None,
    ) -> TestPlan:
        """Load a contract artifact and generate a plan from it."""
        contract = load_contract_artifact(contract_path)
        return self.run(
            contract=contract,
            task_description=task_description,
            spec_text=spec_text,
            out_dir=out_dir,
            based_on_contract=str(contract_path),
            generation_mode=generation_mode,
            llm_config=llm_config,
        )

    def _apply_hybrid_augmentation(
        self,
        *,
        contract: DUTContract,
        baseline_plan: TestPlan,
        task_description: str | None,
        spec_text: str | None,
        out_dir: Path,
        llm_config: LLMConfig,
    ) -> TestPlan:
        plan_dir = ensure_dir(out_dir / "plan")
        system_prompt = build_plan_system_prompt()
        user_prompt = build_plan_user_prompt(
            contract=contract,
            baseline_plan=baseline_plan,
            task_description=task_description,
            spec_text=spec_text,
        )
        request_payload = {
            "generation_mode": GenerationMode.HYBRID.value,
            "provider": llm_config.provider,
            "model": llm_config.model,
            "base_url": llm_config.base_url,
            "temperature": llm_config.temperature,
            "timeout_seconds": llm_config.timeout_seconds,
            "max_retries": llm_config.max_retries,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        }
        write_json(plan_dir / "llm_request.json", request_payload)

        raw_response = ""
        parsed_payload: dict[str, object] = {}
        merge_report: dict[str, object] = {}
        try:
            client = self.llm_client or LLMClient(llm_config)
            raw_response = client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
            parsed = parse_plan_augmentation(raw_response)
            validated, validation_report = validate_plan_augmentation(
                parsed,
                contract=contract,
                baseline_plan=baseline_plan,
            )
            parsed_payload = validated.model_dump(mode="json")
            merged_plan, merge_report = self._merge_plan_augmentation(
                contract=contract,
                baseline_plan=baseline_plan,
                augmentation=validated,
                validation_report=validation_report,
            )
            write_text(plan_dir / "llm_response_raw.txt", raw_response)
            write_json(plan_dir / "llm_response_parsed.json", parsed_payload)
            write_json(plan_dir / "llm_merge_report.json", merge_report)
            return merged_plan
        except Exception as exc:
            fallback = baseline_plan.model_copy(deep=True)
            fallback.plan_strategy = "hybrid_rule_based_plus_llm"
            fallback.assumptions = _deduped(
                baseline_plan.assumptions
                + [f"LLM hybrid fallback activated for plan stage: {_single_line(str(exc))}"]
            )
            fallback.unresolved_items = _deduped(
                baseline_plan.unresolved_items
                + ["Hybrid LLM plan augmentation failed; retained baseline rule-based coverage."]
            )
            merge_report = {
                "status": "fallback",
                "reason": _single_line(str(exc)),
                "baseline_case_count": len(baseline_plan.cases),
                "final_case_count": len(fallback.cases),
            }
            write_text(plan_dir / "llm_response_raw.txt", raw_response)
            write_json(plan_dir / "llm_response_parsed.json", parsed_payload or {"error": _single_line(str(exc))})
            write_json(plan_dir / "llm_merge_report.json", merge_report)
            return fallback

    def _merge_plan_augmentation(
        self,
        *,
        contract: DUTContract,
        baseline_plan: TestPlan,
        augmentation,
        validation_report: dict[str, object],
    ) -> tuple[TestPlan, dict[str, object]]:
        working_cases = [case.model_copy(deep=True) for case in baseline_plan.cases]
        by_case_id = {case.case_id: case for case in working_cases}
        applied_enrichments: list[str] = []
        for enrichment in augmentation.baseline_case_enrichments:
            case = by_case_id[enrichment.case_id]
            if enrichment.goal:
                case.goal = enrichment.goal.strip()
            case.stimulus_intent = _append_unique(case.stimulus_intent, enrichment.stimulus_intent)
            case.timing_assumptions = _append_unique(case.timing_assumptions, enrichment.timing_assumptions)
            case.observed_signals = _append_unique(case.observed_signals, enrichment.observed_signals)
            case.stimulus_signals = _append_unique(case.stimulus_signals, enrichment.stimulus_signals)
            case.expected_properties = _append_unique(case.expected_properties, enrichment.expected_properties)
            case.coverage_tags = _append_unique(case.coverage_tags, enrichment.coverage_tags)
            case.semantic_tags = _append_unique(case.semantic_tags, enrichment.semantic_tags)
            case.notes = _append_unique(case.notes, enrichment.notes)
            if enrichment.priority is not None:
                case.priority = enrichment.priority
            case.source = "hybrid_llm_enriched"
            applied_enrichments.append(case.case_id)

        counters = _case_counters(working_cases)
        draft_to_case_id: dict[str, str] = {}
        for additional_case in augmentation.additional_cases:
            counters[additional_case.category] += 1
            draft_to_case_id[additional_case.draft_id] = f"{additional_case.category}_{counters[additional_case.category]:03d}"

        added_case_ids: list[str] = []
        for additional_case in augmentation.additional_cases:
            final_case_id = draft_to_case_id[additional_case.draft_id]
            mapped_dependencies = [
                draft_to_case_id.get(dependency, dependency)
                for dependency in additional_case.dependencies
                if dependency in by_case_id or dependency in draft_to_case_id
            ]
            new_case = TestCasePlan(
                case_id=final_case_id,
                goal=additional_case.goal,
                category=additional_case.category,
                preconditions=list(additional_case.preconditions),
                stimulus_intent=list(additional_case.stimulus_intent),
                stimulus_signals=list(additional_case.stimulus_signals),
                expected_properties=list(additional_case.expected_properties),
                observed_signals=list(additional_case.observed_signals),
                timing_assumptions=list(additional_case.timing_assumptions),
                dependencies=mapped_dependencies,
                coverage_tags=list(additional_case.coverage_tags),
                semantic_tags=list(additional_case.semantic_tags),
                priority=additional_case.priority,
                confidence=_hybrid_case_confidence(contract=contract, baseline_plan=baseline_plan),
                source="hybrid_llm_generated",
                notes=list(additional_case.notes),
            )
            working_cases.append(new_case)
            by_case_id[new_case.case_id] = new_case
            added_case_ids.append(new_case.case_id)

        assumptions = _deduped(
            baseline_plan.assumptions
            + augmentation.assumptions
            + [f"LLM planning note: {note}" for note in augmentation.planning_notes]
        )
        unresolved_items = _deduped(baseline_plan.unresolved_items + augmentation.unresolved_items)
        if not applied_enrichments and not added_case_ids:
            unresolved_items = _deduped(
                unresolved_items + ["Hybrid LLM planning produced no accepted enrichments beyond the baseline rule-based cases."]
            )

        working_cases = [_calibrate_case_execution_policy(contract=contract, case=case) for case in working_cases]

        merged_plan = TestPlan(
            module_name=baseline_plan.module_name,
            based_on_contract=baseline_plan.based_on_contract,
            plan_strategy="hybrid_rule_based_plus_llm",
            cases=working_cases,
            unresolved_items=unresolved_items,
            assumptions=assumptions,
            plan_confidence=_hybrid_plan_confidence(
                baseline_plan=baseline_plan,
                added_case_count=len(added_case_ids),
                enriched_case_count=len(applied_enrichments),
            ),
        )
        merge_report = {
            "status": "merged",
            "baseline_case_count": len(baseline_plan.cases),
            "final_case_count": len(merged_plan.cases),
            "applied_baseline_case_enrichments": applied_enrichments,
            "accepted_additional_case_ids": added_case_ids,
            "validation_report": validation_report,
        }
        return merged_plan, merge_report

    def _build_basic_case(
        self,
        *,
        contract: DUTContract,
        counters: dict[str, int],
        observed_signals: list[str],
    ) -> TestCasePlan:
        input_names = _drivable_input_names(contract)
        if contract.timing.sequential_kind == SequentialKind.COMB and input_names:
            goal = "Exercise representative legal input combinations and observe output mapping."
            expected_properties = [
                "Observable outputs respond to legal input changes without assuming internal state.",
                "Checks focus on input/output consistency rather than cycle-accurate timing.",
            ]
            stimulus_intent = [f"Drive a representative legal input pattern across known non-control inputs: {input_names}"]
        elif contract.timing.sequential_kind == SequentialKind.SEQ and input_names:
            goal = "Apply one legal operation and observe stable post-operation behavior."
            expected_properties = [
                "A legal operation causes an observable state or output change after conservative observation.",
                "The plan does not assume a completion event before it is externally visible.",
            ]
            stimulus_intent = [f"Drive a representative legal input pattern across known non-control inputs: {input_names}"]
        elif contract.timing.sequential_kind == SequentialKind.SEQ and contract.clocks and observed_signals:
            goal = "Observe clock-driven state progress after reset or conservative initialization."
            expected_properties = [
                "Externally visible outputs remain defined and can change across conservative clocked observation windows.",
                "The plan observes progress without assuming a fixed-cycle protocol or hidden internal state access.",
            ]
            stimulus_intent = ["Release reset if present and observe a small number of conservative clock edges for externally visible progress."]
        else:
            goal = "Observe any externally visible progress without inventing unresolved stimulus semantics."
            expected_properties = [
                "Checks are limited to reset-safe, protocol-safe, or output-visible behavior.",
                "No fixed latency or exact cycle count is assumed.",
            ]
            stimulus_intent = ["Only deterministic, contract-supported stimulus is used; otherwise the case is downgraded."]
        return self._make_case(
            counters=counters,
            category=TestCategory.BASIC,
            goal=goal,
            preconditions=["Use only ports and observable signals present in the contract."],
            stimulus_intent=stimulus_intent,
            stimulus_signals=input_names,
            expected_properties=expected_properties,
            observed_signals=observed_signals,
            timing_assumptions=_safe_timing_assumptions(contract),
            dependencies=["reset_001"] if contract.resets else [],
            coverage_tags=["basic", "sanity", contract.timing.sequential_kind],
            semantic_tags=["ambiguity_preserving"],
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
        vector_inputs = [
            port.name
            for port in contract.ports
            if port.direction == PortDirection.INPUT and port.name in _drivable_input_names(contract) and port.width not in (None, 1)
        ]
        fallback_inputs = _drivable_input_names(contract)
        control_inputs = [name for name in fallback_inputs if name in _control_like_input_names(contract)]
        stimulus_signals = _deduped(vector_inputs + control_inputs) or fallback_inputs
        expected = [
            "Boundary-value stimulation does not rely on hidden state or undocumented latency.",
            "When width expressions are symbolic, only conservative min/max-style exploration is planned.",
        ]
        return self._make_case(
            counters=counters,
            category=TestCategory.EDGE,
            goal="Exercise boundary-value and width-sensitive input patterns.",
            preconditions=["At least one input or symbolic-width input is available."],
            stimulus_intent=[f"Use zero-like, one-like, and boundary patterns on {stimulus_signals or ['resolved non-control inputs']}"],
            stimulus_signals=stimulus_signals,
            expected_properties=expected,
            observed_signals=observed_signals,
            timing_assumptions=_safe_timing_assumptions(contract),
            dependencies=["basic_001"],
            coverage_tags=["edge", "boundary"],
            semantic_tags=["width_sensitive"],
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
                    stimulus_signals=[group.signals["valid"], group.signals["ready"]],
                    expected_properties=[
                        "When valid and ready overlap, observe externally visible acceptance or progress.",
                        "Do not assume a fixed completion cycle after acceptance.",
                    ],
                    observed_signals=protocol_signals,
                    timing_assumptions=_protocol_safe_timing_assumptions(contract),
                    dependencies=["reset_001"] if contract.resets else [],
                    coverage_tags=["protocol", "valid_ready", "acceptance", group.group_name],
                    semantic_tags=["operation_specific"],
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
                    stimulus_signals=[group.signals["valid"], group.signals["ready"]],
                    expected_properties=[
                        "Progress is deferred, stalled, or otherwise safely withheld while ready is low.",
                        "The plan does not assume a single exact stall policy beyond safe non-acceptance observation.",
                    ],
                    observed_signals=protocol_signals,
                    timing_assumptions=_protocol_safe_timing_assumptions(contract),
                    dependencies=["basic_001"],
                    coverage_tags=["protocol", "valid_ready", "backpressure", group.group_name],
                    semantic_tags=["ambiguity_preserving"],
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
                    stimulus_signals=[group.signals["valid"], group.signals["ready"]],
                    expected_properties=[
                        "Source-side behavior remains safe and externally consistent until acceptance is observed.",
                        "No exact persistence policy is assumed beyond safe observation.",
                    ],
                    observed_signals=protocol_signals,
                    timing_assumptions=_protocol_safe_timing_assumptions(contract),
                    dependencies=["protocol_001"],
                    coverage_tags=["protocol", "valid_ready", "persistence", group.group_name],
                    semantic_tags=["ambiguity_preserving"],
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
                    stimulus_signals=[group.signals["start"]],
                    expected_properties=[
                        "A legal start request eventually results in a visible completion or completion-related observation.",
                        "No exact completion latency is assumed.",
                    ],
                    observed_signals=protocol_signals,
                    timing_assumptions=_protocol_safe_timing_assumptions(contract),
                    dependencies=["basic_001"],
                    coverage_tags=["protocol", "start_done", "completion"],
                    semantic_tags=["operation_specific"],
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
                    stimulus_signals=[group.signals["req"]],
                    expected_properties=[
                        "A legal request eventually receives an externally visible acknowledge or progress indicator.",
                        "No fixed-latency acknowledge timing is assumed.",
                    ],
                    observed_signals=protocol_signals,
                    timing_assumptions=_protocol_safe_timing_assumptions(contract),
                    dependencies=["basic_001"],
                    coverage_tags=["protocol", "req_ack", "acceptance"],
                    semantic_tags=["operation_specific"],
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
            stimulus_signals=_drivable_input_names(contract)[:3],
            expected_properties=[
                "Repeated operations do not rely on hidden fixed-latency assumptions.",
                "The second operation is observed only through externally visible acceptance, completion, or output change.",
            ],
            observed_signals=observed_signals,
            timing_assumptions=_safe_timing_assumptions(contract),
            dependencies=["basic_001"],
            coverage_tags=["back_to_back", "repeated_operation"],
            semantic_tags=["operation_specific"],
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
            stimulus_signals=_drivable_input_names(contract)[:3],
            expected_properties=[
                "Observe safe handling, rejection, or non-progress for documented illegal input conditions.",
                "Do not assume undocumented error signaling semantics.",
            ],
            observed_signals=observed_signals,
            timing_assumptions=_safe_timing_assumptions(contract),
            dependencies=["basic_001"],
            coverage_tags=["negative", "illegal_input"],
            semantic_tags=["invalid_illegal_input", "ambiguity_preserving"],
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
        stimulus_signals: list[str] | None = None,
        semantic_tags: list[str] | None = None,
    ) -> TestCasePlan:
        counters[category.value] += 1
        case_id = f"{category.value}_{counters[category.value]:03d}"
        return TestCasePlan(
            case_id=case_id,
            goal=goal,
            category=category,
            preconditions=preconditions,
            stimulus_intent=stimulus_intent,
            stimulus_signals=list(stimulus_signals or []),
            expected_properties=expected_properties,
            observed_signals=observed_signals,
            timing_assumptions=timing_assumptions,
            dependencies=dependencies,
            coverage_tags=coverage_tags,
            semantic_tags=list(semantic_tags or []),
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
    output_like_ports = [port.name for port in contract.ports if port.direction in {PortDirection.OUTPUT, PortDirection.INOUT}]
    if output_like_ports:
        return output_like_ports
    if contract.handshake_signals:
        return list(contract.handshake_signals)
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
    return bool(_drivable_input_names(contract)) and contract.contract_confidence >= 0.5


def _should_add_back_to_back_case(contract: DUTContract) -> bool:
    return bool(contract.handshake_groups) or (
        contract.timing.sequential_kind == SequentialKind.SEQ and bool(_drivable_input_names(contract))
    )


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


def _drivable_input_names(contract: DUTContract) -> list[str]:
    excluded = {clock.name for clock in contract.clocks} | {reset.name for reset in contract.resets}
    return [
        port.name
        for port in contract.ports
        if port.direction == PortDirection.INPUT and port.name not in excluded
    ]


def _control_like_input_names(contract: DUTContract) -> list[str]:
    control_tokens = ("en", "enable", "valid", "ready", "start", "done", "read", "write", "req", "ack", "load")
    result: list[str] = []
    for signal_name in _drivable_input_names(contract):
        lowered = signal_name.lower()
        if any(token in lowered for token in control_tokens):
            result.append(signal_name)
    return result


def _should_minimize_plan(
    *,
    contract: DUTContract,
    observed_signals: list[str],
    drivable_inputs: list[str],
) -> bool:
    if contract.contract_confidence < 0.3:
        return True
    if not observed_signals:
        return True
    if not drivable_inputs and contract.timing.sequential_kind == SequentialKind.UNKNOWN:
        return True
    return False


def _calibrate_case_execution_policy(*, contract: DUTContract, case: TestCasePlan) -> TestCasePlan:
    calibrated = case.model_copy(deep=True)
    allowed_inputs = set(_drivable_input_names(contract))
    if calibrated.category != TestCategory.RESET:
        calibrated.stimulus_signals = [signal for signal in calibrated.stimulus_signals if signal in allowed_inputs]

    if not calibrated.observed_signals:
        calibrated.execution_policy = "deferred"
        calibrated.defer_reason = "No resolved observable outputs were available for deterministic mainline execution."
        calibrated.notes = _append_unique(calibrated.notes, [calibrated.defer_reason])
        return calibrated

    if calibrated.category == TestCategory.RESET:
        calibrated.execution_policy = "deterministic" if contract.resets else "deferred"
        calibrated.defer_reason = "" if contract.resets else "No resolved reset signal was available."
        if calibrated.defer_reason:
            calibrated.notes = _append_unique(calibrated.notes, [calibrated.defer_reason])
        return calibrated

    if calibrated.category == TestCategory.NEGATIVE:
        calibrated.execution_policy = "deferred"
        calibrated.defer_reason = "Negative cases require stronger structured illegal-input semantics than the current contract provides."
        calibrated.notes = _append_unique(calibrated.notes, [calibrated.defer_reason])
        return calibrated

    if calibrated.category in {TestCategory.METAMORPHIC, TestCategory.REGRESSION} and contract.contract_confidence < 0.8:
        calibrated.execution_policy = "deferred"
        calibrated.defer_reason = "Advanced derived cases were downgraded because the contract does not yet justify deterministic mainline semantics."
        calibrated.notes = _append_unique(calibrated.notes, [calibrated.defer_reason])
        return calibrated

    if calibrated.stimulus_signals:
        calibrated.execution_policy = "deterministic"
        return calibrated

    if contract.timing.sequential_kind == SequentialKind.SEQ and contract.clocks:
        calibrated.execution_policy = "deterministic"
        calibrated.notes = _append_unique(
            calibrated.notes,
            ["Case relies on deterministic clock-driven observation because no non-control inputs were resolved."],
        )
        return calibrated

    calibrated.execution_policy = "deferred"
    calibrated.defer_reason = "No deterministic non-control stimulus could be derived from the current contract."
    calibrated.notes = _append_unique(calibrated.notes, [calibrated.defer_reason])
    return calibrated


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


def _deduped(items: list[str]) -> list[str]:
    unique_items = list(items)
    _dedupe_in_place(unique_items)
    return [item for item in unique_items if item]


def _append_unique(existing: list[str], additions: list[str]) -> list[str]:
    return _deduped(list(existing) + list(additions))


def _case_counters(cases: list[TestCasePlan]) -> dict[str, int]:
    counters: dict[str, int] = defaultdict(int)
    for case in cases:
        counters[str(case.category)] += 1
    return counters


def _hybrid_case_confidence(*, contract: DUTContract, baseline_plan: TestPlan) -> float:
    return max(0.2, min(fmean([contract.contract_confidence, baseline_plan.plan_confidence]), 0.9))


def _hybrid_plan_confidence(
    *,
    baseline_plan: TestPlan,
    added_case_count: int,
    enriched_case_count: int,
) -> float:
    score = baseline_plan.plan_confidence + min(0.12, 0.03 * added_case_count + 0.02 * enriched_case_count)
    return max(0.1, min(score, 0.95))


def _single_line(text: str) -> str:
    return " ".join(str(text or "").split())
