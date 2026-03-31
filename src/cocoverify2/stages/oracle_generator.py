"""Rule-based oracle generation for Phase 3."""

from __future__ import annotations

import json
from pathlib import Path
import re
from statistics import fmean

from cocoverify2.core.config import LLMConfig
from cocoverify2.core.errors import ArtifactError, ConfigurationError
from cocoverify2.core.models import (
    DUTContract,
    OracleCase,
    OracleCheck,
    OracleConfidenceSummary,
    OracleSpec,
    SignalAssertionPolicy,
    TemporalWindow,
    TestCasePlan,
    TestPlan,
)
from cocoverify2.core.types import (
    AssertionStrength,
    DefinednessMode,
    GenerationMode,
    LatencyModel,
    OracleCheckType,
    OracleStrictness,
    PortDirection,
    SequentialKind,
    TemporalWindowMode,
)
from cocoverify2.llm.client import LLMClient
from cocoverify2.llm.prompts import build_oracle_system_prompt, build_oracle_user_prompt
from cocoverify2.llm.validators import (
    extract_json_payload,
    normalize_oracle_augmentation_payload,
    parse_oracle_augmentation,
    validate_oracle_augmentation,
)
from cocoverify2.utils.files import ensure_dir, read_json, write_json, write_text, write_yaml
from cocoverify2.utils.logging import get_logger
from cocoverify2.utils.semantic_families import (
    infer_divide_relation_family,
    infer_fifo_readback_family,
    infer_fixed_point_add_family,
    infer_grouped_valid_accumulator_family,
    infer_packed_stream_conversion_family,
    infer_pipelined_multiply_family,
    infer_ring_progression_family,
    infer_sequence_detect_family,
    infer_serial_to_parallel_family,
    infer_traffic_light_phase_family,
)


class OracleGenerator:
    """Generate a conservative oracle artifact from contract and test-plan artifacts."""

    __test__ = False

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        """Initialize the generator with a stage-scoped logger."""
        self.logger = get_logger(__name__)
        self.llm_client = llm_client

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
        generation_mode: GenerationMode | str = GenerationMode.RULE_BASED,
        llm_config: LLMConfig | None = None,
    ) -> OracleSpec:
        """Generate and persist a structured oracle artifact."""
        generation_mode = GenerationMode(generation_mode)
        baseline_oracle = self._generate_rule_based_oracle(
            contract=contract,
            plan=plan,
            task_description=task_description,
            spec_text=spec_text,
            based_on_contract=based_on_contract,
            based_on_plan=based_on_plan,
        )
        if generation_mode == GenerationMode.RULE_BASED:
            baseline_oracle.oracle_strategy = "rule_based_conservative"
            self._dump_oracle_artifacts(baseline_oracle, out_dir)
            self.logger.info(
                "Generated oracle artifact for '%s' with %d protocol, %d functional, %d property cases.",
                baseline_oracle.module_name,
                len(baseline_oracle.protocol_oracles),
                len(baseline_oracle.functional_oracles),
                len(baseline_oracle.property_oracles),
            )
            return baseline_oracle

        llm_config = llm_config or LLMConfig()
        hybrid_oracle = self._apply_hybrid_augmentation(
            contract=contract,
            plan=plan,
            baseline_oracle=baseline_oracle,
            spec_text=spec_text,
            out_dir=out_dir,
            llm_config=llm_config,
        )
        self._dump_oracle_artifacts(hybrid_oracle, out_dir)
        self.logger.info(
            "Generated hybrid oracle artifact for '%s' with %d protocol, %d functional, %d property cases.",
            hybrid_oracle.module_name,
            len(hybrid_oracle.protocol_oracles),
            len(hybrid_oracle.functional_oracles),
            len(hybrid_oracle.property_oracles),
        )
        return hybrid_oracle

    def _generate_rule_based_oracle(
        self,
        *,
        contract: DUTContract,
        plan: TestPlan,
        task_description: str | None,
        spec_text: str | None,
        based_on_contract: str = "",
        based_on_plan: str = "",
    ) -> OracleSpec:
        """Generate the baseline conservative rule-based oracle without persisting it."""
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
            oracle_strategy="rule_based_conservative",
            protocol_oracles=protocol_oracles,
            functional_oracles=functional_oracles,
            property_oracles=property_oracles,
            unresolved_items=unresolved_items,
            assumptions=assumptions,
            oracle_confidence=confidence_summary,
        )
        _attach_signal_policies(oracle=oracle, contract=contract, plan=plan)
        return oracle

    def run_from_artifacts(
        self,
        *,
        contract_path: Path,
        plan_path: Path,
        task_description: str | None,
        spec_text: str | None,
        out_dir: Path,
        generation_mode: GenerationMode | str = GenerationMode.RULE_BASED,
        llm_config: LLMConfig | None = None,
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
            generation_mode=generation_mode,
            llm_config=llm_config,
        )

    def _apply_hybrid_augmentation(
        self,
        *,
        contract: DUTContract,
        plan: TestPlan,
        baseline_oracle: OracleSpec,
        spec_text: str | None,
        out_dir: Path,
        llm_config: LLMConfig,
    ) -> OracleSpec:
        oracle_dir = ensure_dir(out_dir / "oracle")
        system_prompt = build_oracle_system_prompt()
        user_prompt = build_oracle_user_prompt(
            contract=contract,
            final_plan=plan,
            baseline_oracle=baseline_oracle,
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
        write_json(oracle_dir / "llm_request.json", request_payload)

        raw_response = ""
        parsed_payload: dict[str, object] = {}
        normalized_payload: dict[str, object] = {}
        merge_report: dict[str, object] = {}
        try:
            client = self.llm_client or LLMClient(llm_config)
            raw_response = client.complete(system_prompt=system_prompt, user_prompt=user_prompt)
            parsed_payload = extract_json_payload(raw_response)
            normalized_payload, normalization_report = normalize_oracle_augmentation_payload(parsed_payload)
            parsed = parse_oracle_augmentation(raw_response)
            validated, validation_report = validate_oracle_augmentation(
                parsed,
                contract=contract,
                plan=plan,
                baseline_oracle=baseline_oracle,
            )
            merged_oracle, merge_report = self._merge_oracle_augmentation(
                contract=contract,
                plan=plan,
                baseline_oracle=baseline_oracle,
                augmentation=validated,
                validation_report={
                    "normalization_report": normalization_report,
                    **validation_report,
                },
            )
            write_text(oracle_dir / "llm_response_raw.txt", raw_response)
            write_json(oracle_dir / "llm_response_parsed.json", parsed_payload)
            write_json(oracle_dir / "llm_response_normalized.json", normalized_payload)
            write_json(oracle_dir / "llm_merge_report.json", merge_report)
            return merged_oracle
        except Exception as exc:
            fallback = baseline_oracle.model_copy(deep=True)
            fallback.oracle_strategy = "hybrid_rule_based_plus_llm"
            fallback.assumptions = _deduped(
                baseline_oracle.assumptions
                + [f"LLM hybrid fallback activated for oracle stage: {_single_line(str(exc))}"]
            )
            fallback.unresolved_items = _deduped(
                baseline_oracle.unresolved_items
                + ["Hybrid LLM oracle augmentation failed; retained baseline rule-based oracle checks."]
            )
            merge_report = {
                "status": "fallback",
                "reason": _single_line(str(exc)),
                "baseline_protocol_cases": len(baseline_oracle.protocol_oracles),
                "baseline_functional_cases": len(baseline_oracle.functional_oracles),
                "baseline_property_cases": len(baseline_oracle.property_oracles),
            }
            write_text(oracle_dir / "llm_response_raw.txt", raw_response)
            write_json(oracle_dir / "llm_response_parsed.json", parsed_payload or {"error": _single_line(str(exc))})
            write_json(oracle_dir / "llm_response_normalized.json", normalized_payload or {"error": _single_line(str(exc))})
            write_json(oracle_dir / "llm_merge_report.json", merge_report)
            return fallback

    def _merge_oracle_augmentation(
        self,
        *,
        contract: DUTContract,
        plan: TestPlan,
        baseline_oracle: OracleSpec,
        augmentation,
        validation_report: dict[str, object],
    ) -> tuple[OracleSpec, dict[str, object]]:
        protocol_cases = [case.model_copy(deep=True) for case in baseline_oracle.protocol_oracles]
        functional_cases = [case.model_copy(deep=True) for case in baseline_oracle.functional_oracles]
        property_cases = [case.model_copy(deep=True) for case in baseline_oracle.property_oracles]
        plan_cases = {case.case_id: case for case in plan.cases}
        accepted_checks: list[str] = []
        created_case_ids: list[str] = []
        dropped_checks: list[dict[str, str]] = []

        for enrichment in augmentation.case_enrichments:
            target_case = _find_oracle_case(
                protocol_cases=protocol_cases,
                functional_cases=functional_cases,
                property_cases=property_cases,
                oracle_class=enrichment.oracle_class,
                linked_plan_case_id=enrichment.linked_plan_case_id,
            )
            if target_case is None:
                continue
            target_case.assumptions = _append_unique(target_case.assumptions, enrichment.assumptions)
            target_case.unresolved_items = _append_unique(target_case.unresolved_items, enrichment.unresolved_items)
            target_case.notes = _append_unique(target_case.notes, enrichment.notes)
            target_case.source = "hybrid_llm_enriched"
            self._append_llm_checks_to_case(
                contract=contract,
                plan_case=plan_cases[enrichment.linked_plan_case_id],
                target_case=target_case,
                checks=enrichment.checks,
                accepted_checks=accepted_checks,
                dropped_checks=dropped_checks,
            )

        for proposed_case in augmentation.additional_oracle_cases:
            target_case = _find_oracle_case(
                protocol_cases=protocol_cases,
                functional_cases=functional_cases,
                property_cases=property_cases,
                oracle_class=proposed_case.oracle_class,
                linked_plan_case_id=proposed_case.linked_plan_case_id,
            )
            if target_case is None:
                target_case = _make_hybrid_oracle_case(
                    oracle_class=proposed_case.oracle_class,
                    linked_plan_case_id=proposed_case.linked_plan_case_id,
                    category=plan_cases[proposed_case.linked_plan_case_id].category,
                )
                _oracle_case_list(
                    protocol_cases=protocol_cases,
                    functional_cases=functional_cases,
                    property_cases=property_cases,
                    oracle_class=proposed_case.oracle_class,
                ).append(target_case)
                created_case_ids.append(target_case.case_id)
            target_case.assumptions = _append_unique(target_case.assumptions, proposed_case.assumptions)
            target_case.unresolved_items = _append_unique(target_case.unresolved_items, proposed_case.unresolved_items)
            target_case.notes = _append_unique(target_case.notes, proposed_case.notes)
            target_case.source = "hybrid_llm_generated"
            self._append_llm_checks_to_case(
                contract=contract,
                plan_case=plan_cases[proposed_case.linked_plan_case_id],
                target_case=target_case,
                checks=proposed_case.checks,
                accepted_checks=accepted_checks,
                dropped_checks=dropped_checks,
            )

        for case in protocol_cases + functional_cases + property_cases:
            case.confidence = _average_check_confidence(case.checks)

        unresolved_items = _deduped(baseline_oracle.unresolved_items + augmentation.unresolved_items)
        if not accepted_checks and not created_case_ids:
            unresolved_items = _deduped(
                unresolved_items + ["Hybrid LLM oracle augmentation produced no accepted checks beyond the baseline oracle."]
            )
        assumptions = _deduped(
            baseline_oracle.assumptions
            + augmentation.assumptions
            + [f"LLM oracle note: {note}" for note in augmentation.oracle_notes]
        )
        weak_contract = _is_weak_contract(contract, plan)
        merged_oracle = OracleSpec(
            module_name=baseline_oracle.module_name,
            based_on_contract=baseline_oracle.based_on_contract,
            based_on_plan=baseline_oracle.based_on_plan,
            oracle_strategy="hybrid_rule_based_plus_llm",
            protocol_oracles=protocol_cases,
            functional_oracles=functional_cases,
            property_oracles=property_cases,
            unresolved_items=unresolved_items,
            assumptions=assumptions,
            oracle_confidence=_estimate_oracle_confidence(
                contract=contract,
                plan=plan,
                protocol_oracles=protocol_cases,
                functional_oracles=functional_cases,
                property_oracles=property_cases,
                unresolved_items=unresolved_items,
                weak_contract=weak_contract,
            ),
        )
        _attach_signal_policies(oracle=merged_oracle, contract=contract, plan=plan)
        merge_report = {
            "status": "merged",
            "accepted_check_ids": accepted_checks,
            "created_case_ids": created_case_ids,
            "dropped_checks": dropped_checks,
            "validation_report": validation_report,
        }
        return merged_oracle, merge_report

    def _append_llm_checks_to_case(
        self,
        *,
        contract: DUTContract,
        plan_case: TestCasePlan,
        target_case: OracleCase,
        checks,
        accepted_checks: list[str],
        dropped_checks: list[dict[str, str]],
    ) -> None:
        next_index = len(target_case.checks) + 1
        for proposed_check in checks:
            generated_check = _make_hybrid_check(
                case_id=target_case.linked_plan_case_id,
                ordinal=next_index,
                proposed_check=proposed_check,
                confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.02),
            )
            if _is_duplicate_oracle_check(generated_check, target_case.checks):
                dropped_checks.append({"case_id": target_case.case_id, "reason": "duplicate_check", "description": generated_check.description})
                continue
            if _is_conflicting_oracle_check(generated_check, target_case.checks):
                dropped_checks.append({"case_id": target_case.case_id, "reason": "conflicting_check", "description": generated_check.description})
                continue
            target_case.checks.append(generated_check)
            accepted_checks.append(generated_check.check_id)
            next_index += 1

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
        operation_specific_checks = _build_operation_specific_functional_checks(contract=contract, plan_case=plan_case)

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
            if operation_specific_checks:
                assumptions.append(
                    "Operation-specific functional checks were emitted from stable interface patterns even though the broader contract remains conservative."
                )
            else:
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

        checks.extend(operation_specific_checks)

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



def _build_operation_specific_functional_checks(*, contract: DUTContract, plan_case: TestCasePlan) -> list[OracleCheck]:
    checks: list[OracleCheck] = []
    if plan_case.category == "reset":
        return checks
    additional_texts = [
        plan_case.goal,
        *plan_case.stimulus_intent,
        *plan_case.expected_properties,
        str(plan_case.reference_domain or ""),
        str(plan_case.expected_transition or ""),
    ]
    accumulator_family = infer_grouped_valid_accumulator_family(
        contract,
        additional_texts=additional_texts,
    )
    serial_family = infer_serial_to_parallel_family(contract, additional_texts=additional_texts)
    packed_family = infer_packed_stream_conversion_family(contract, additional_texts=additional_texts)
    fifo_family = infer_fifo_readback_family(contract, additional_texts=additional_texts)
    multiply_family = infer_pipelined_multiply_family(contract, additional_texts=additional_texts)
    fixed_point_family = infer_fixed_point_add_family(contract, additional_texts=additional_texts)
    divide_family = infer_divide_relation_family(contract, additional_texts=additional_texts)
    sequence_family = infer_sequence_detect_family(contract, additional_texts=additional_texts)
    ring_family = infer_ring_progression_family(contract, additional_texts=additional_texts)
    traffic_family = infer_traffic_light_phase_family(contract, additional_texts=additional_texts)

    accumulator_check = _build_grouped_valid_accumulation_check(
        contract=contract,
        plan_case=plan_case,
        accumulator_family=accumulator_family,
    )
    if accumulator_check is not None:
        checks.append(accumulator_check)

    if serial_family is not None and plan_case.category in {"basic", "back_to_back"}:
        checks.append(
            _make_check(
                case_id=plan_case.case_id,
                check_type=OracleCheckType.FUNCTIONAL,
                ordinal=900,
                description="Collect eight valid serial bits and verify the reconstructed parallel byte when dout_valid pulses.",
                observed_signals=_deduped(
                    [serial_family["parallel_output_signal"], serial_family["output_gate_signal"]]
                ),
                trigger_condition="When the rendered stimulus drives a legal eight-bit serial transfer.",
                pass_condition="After one complete legal serial transfer, the output-valid signal must pulse exactly once and the parallel output must equal the captured byte in the documented or ambiguity-preserving bit order.",
                temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="operation_applied"),
                strictness=OracleStrictness.CONSERVATIVE,
                confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.03),
                notes=["Structured serial-history relation check is derived from role-level stream metadata, not exact canonical names."],
                semantic_tags=["operation_specific", "serial_history"],
                relation_kind="serial_to_parallel_byte",
                comparison_operands=[
                    serial_family["serial_input_signal"],
                    serial_family["input_gate_signal"],
                    serial_family["parallel_output_signal"],
                    serial_family["output_gate_signal"],
                ],
                reference_domain=str(serial_family["bit_order"]),
                expected_transition=f'{serial_family["bit_count"]}_valid_bits_then_single_output_event',
                oracle_pattern=json.dumps(
                    {
                        "bit_count": int(serial_family["bit_count"]),
                        "bit_order": str(serial_family["bit_order"]),
                    },
                    sort_keys=True,
                ),
            )
        )

    if packed_family is not None:
        checks.append(
            _make_check(
                case_id=plan_case.case_id,
                check_type=OracleCheckType.FUNCTIONAL,
                ordinal=901,
                description="Capture one complete packed input group and verify the aggregated output when output-valid asserts.",
                observed_signals=_deduped(
                    [packed_family["output_data_signal"], packed_family["output_gate_signal"]]
                ),
                trigger_condition="When the rendered stimulus presents one finite legal group of valid input elements.",
                pass_condition="After one complete valid input group, the output-valid signal must assert and the packed output must reflect the finite input group in the documented or ambiguity-preserving element order.",
                temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="operation_applied"),
                strictness=OracleStrictness.CONSERVATIVE,
                confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.03),
                notes=["Structured packing relation avoids hidden exact-cycle assumptions while still checking externally visible grouped value semantics."],
                semantic_tags=["operation_specific", "data_packing"],
                relation_kind="byte_pack_pair",
                comparison_operands=[
                    packed_family["input_data_signal"],
                    packed_family["input_gate_signal"],
                    packed_family["output_data_signal"],
                    packed_family["output_gate_signal"],
                ],
                reference_domain=str(packed_family["pack_order"]),
                expected_transition=f'{packed_family["element_count"]}_valid_elements_then_output_valid',
                oracle_pattern=json.dumps(
                    {
                        "element_count": int(packed_family["element_count"]),
                        "element_width": int(packed_family["input_width"]),
                        "pack_order": str(packed_family["pack_order"]),
                    },
                    sort_keys=True,
                ),
            )
        )

    if fifo_family is not None:
        checks.append(
            _make_check(
                case_id=plan_case.case_id,
                check_type=OracleCheckType.FUNCTIONAL,
                ordinal=902,
                description="Write one FIFO entry, then read it back while checking empty/full consistency.",
                observed_signals=_deduped(
                    [
                        signal
                        for signal in [
                            fifo_family["read_data_signal"],
                            fifo_family["empty_signal"],
                            fifo_family["full_signal"],
                        ]
                        if signal
                    ]
                ),
                trigger_condition="When the rendered stimulus performs a legal write phase followed by a legal read phase.",
                pass_condition="A value written into the FIFO must later become observable on rdata during a legal read sequence, and rempty/wfull must remain externally consistent.",
                temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="operation_applied"),
                strictness=OracleStrictness.CONSERVATIVE,
                confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.02),
                notes=["Structured FIFO relation check uses only externally visible write/read behavior and role-level interface inference."],
                semantic_tags=["operation_specific", "fifo_relation"],
                relation_kind="fifo_write_readback",
                comparison_operands=[
                    fifo_family["write_data_signal"],
                    fifo_family["write_enable_signal"],
                    fifo_family["read_enable_signal"],
                    fifo_family["read_data_signal"],
                    fifo_family["empty_signal"],
                    fifo_family["full_signal"],
                ],
                reference_domain="single_write_single_read",
                expected_transition="write_then_readback",
            )
        )

    if multiply_family is not None:
        multiply_domain = str(multiply_family.get("arithmetic_domain") or "unknown")
        operands = [
            multiply_family["left_operand_signal"],
            multiply_family["right_operand_signal"],
            multiply_family["product_signal"],
        ]
        if multiply_family["input_gate_signal"]:
            operands.append(multiply_family["input_gate_signal"])
        if multiply_family["output_gate_signal"]:
            operands.append(multiply_family["output_gate_signal"])
        if multiply_domain == "unsigned" and str(plan_case.category) == "basic":
            checks.append(
                _make_check(
                    case_id=plan_case.case_id,
                    check_type=OracleCheckType.FUNCTIONAL,
                    ordinal=903,
                    description="Verify that a legal enabled multiply operation eventually produces the exact unsigned product.",
                    observed_signals=_deduped(
                        [
                            signal
                            for signal in [
                                multiply_family["product_signal"],
                                multiply_family["output_gate_signal"],
                            ]
                            if signal
                        ]
                    ),
                    trigger_condition="When the rendered stimulus drives one concrete legal multiplicand/multiplier pair.",
                    pass_condition="The observable product must equal mul_a * mul_b once the output becomes valid.",
                    temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="operation_applied"),
                    strictness=OracleStrictness.CONSERVATIVE,
                    confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.03),
                    notes=[
                        "Structured pipeline-product relation is limited to one finite unsigned operation.",
                        "Back-to-back or signed/Booth-style multiply cases stay on weaker progress/property checks unless the contract is more explicit.",
                    ],
                    semantic_tags=["operation_specific", "arithmetic_relation"],
                    relation_kind="pipelined_unsigned_product",
                    comparison_operands=operands,
                    reference_domain="unsigned",
                    expected_transition="enabled_operation_then_exact_product",
                )
            )

    if fixed_point_family is not None:
        checks.append(
            _make_check(
                case_id=plan_case.case_id,
                check_type=OracleCheckType.FUNCTIONAL,
                ordinal=904,
                description="Verify the sign-magnitude fixed-point addition relation on non-overflowing operands.",
                observed_signals=[fixed_point_family["result_signal"]],
                trigger_condition="When the rendered stimulus applies legal fixed-point operands whose magnitude relation is unambiguous.",
                pass_condition="Output c must equal the sign-magnitude addition/subtraction result of a and b for the observed operands.",
                temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="input_stable"),
                strictness=OracleStrictness.CONSERVATIVE,
                confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.02),
                notes=["Structured fixed-point relation only fires on non-overflowing sign-magnitude operands."],
                semantic_tags=["operation_specific", "arithmetic_relation"],
                relation_kind="fixed_point_sign_magnitude_add",
                comparison_operands=[
                    fixed_point_family["left_operand_signal"],
                    fixed_point_family["right_operand_signal"],
                    fixed_point_family["result_signal"],
                ],
                reference_domain="sign_magnitude",
                expected_transition="exact_combinational_result",
            )
        )

    if divide_family is not None:
        checks.append(
            _make_check(
                case_id=plan_case.case_id,
                check_type=OracleCheckType.FUNCTIONAL,
                ordinal=905,
                description="Verify the quotient/remainder relation for the observed dividend and divisor.",
                observed_signals=_deduped(
                    [divide_family["quotient_signal"], divide_family["remainder_signal"]]
                ),
                trigger_condition="When the rendered stimulus applies a non-zero divisor.",
                pass_condition="result must equal A divided by B and odd must carry the zero-extended remainder for the observed inputs.",
                temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="input_stable"),
                strictness=OracleStrictness.CONSERVATIVE,
                confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.02),
                notes=["Structured divide relation stays combinational and avoids any benchmark-only reference model."],
                semantic_tags=["operation_specific", "arithmetic_relation"],
                relation_kind="unsigned_divide_16_by_8",
                comparison_operands=[
                    divide_family["dividend_signal"],
                    divide_family["divisor_signal"],
                    divide_family["quotient_signal"],
                    divide_family["remainder_signal"],
                ],
                reference_domain="zero_extend_remainder",
                expected_transition="exact_combinational_result",
            )
        )

    if sequence_family is not None:
        pattern = str(sequence_family["bit_pattern"])
        checks.append(
            _make_check(
                case_id=plan_case.case_id,
                check_type=OracleCheckType.FUNCTIONAL,
                ordinal=906,
                description="Verify that the documented input bit pattern leads to an observable detect pulse.",
                observed_signals=[sequence_family["output_signal"]],
                trigger_condition="When the rendered stimulus drives the documented detection pattern on the resolved scalar input stream.",
                pass_condition=f"After the documented input pattern {pattern}, the detect output must become high within a conservative observation window.",
                temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="operation_applied"),
                strictness=OracleStrictness.CONSERVATIVE,
                confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.02),
                notes=["Structured pattern-detect relation uses only driven input history and observed detect output."],
                semantic_tags=["operation_specific", "serial_history"],
                relation_kind="sequence_pattern_detect",
                comparison_operands=[sequence_family["input_signal"], sequence_family["output_signal"]],
                reference_domain="bit_pattern",
                expected_transition=pattern,
                oracle_pattern=json.dumps({"bit_pattern": pattern}, sort_keys=True),
            )
        )

    ring_check = _build_ring_counter_progression_check(
        contract=contract,
        plan_case=plan_case,
        ring_family=ring_family,
    )
    if ring_check is not None:
        checks.append(ring_check)

    traffic_light_check = _build_traffic_light_progression_check(
        contract=contract,
        plan_case=plan_case,
        traffic_family=traffic_family,
    )
    if traffic_light_check is not None:
        checks.append(traffic_light_check)

    return checks


def _build_grouped_valid_accumulation_check(
    *,
    contract: DUTContract,
    plan_case: TestCasePlan,
    accumulator_family: dict[str, object] | None,
) -> OracleCheck | None:
    if accumulator_family is None:
        return None

    group_size = int(accumulator_family["group_size"])
    pattern = _grouped_valid_pattern(plan_case=plan_case, group_size=group_size, accumulator_family=accumulator_family)
    if pattern is None:
        return None
    return _make_check(
        case_id=plan_case.case_id,
        check_type=OracleCheckType.FUNCTIONAL,
        ordinal=899,
        description=pattern["description"],
        observed_signals=_deduped(
            [
                str(accumulator_family["output_gate_signal"]),
                str(accumulator_family["output_data_signal"]),
            ]
        ),
        trigger_condition=pattern["trigger_condition"],
        pass_condition=pattern["pass_condition"],
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="operation_applied"),
        strictness=OracleStrictness.CONSERVATIVE,
        confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.04),
        notes=[pattern["note"]],
        semantic_tags=["operation_specific", "stream_grouping", "accumulation_relation"],
        relation_kind="grouped_valid_accumulation",
        comparison_operands=[
            str(accumulator_family["input_data_signal"]),
            str(accumulator_family["input_gate_signal"]),
            str(accumulator_family["output_data_signal"]),
            str(accumulator_family["output_gate_signal"]),
        ],
        reference_domain=pattern["reference_domain"],
        expected_transition=pattern["expected_transition"],
        oracle_pattern=json.dumps(pattern["oracle_pattern"], sort_keys=True),
    )


def _grouped_valid_pattern(
    *,
    plan_case: TestCasePlan,
    group_size: int,
    accumulator_family: dict[str, object],
) -> dict[str, object] | None:
    category = str(plan_case.category)
    scenario_kind = str(plan_case.scenario_kind or "")
    transition = str(plan_case.expected_transition or "").lower()
    reset_name = str(accumulator_family.get("reset_name") or "")
    reset_active_level = accumulator_family.get("reset_active_level")
    pattern: dict[str, object] = {
        "group_size": group_size,
        "allow_gaps": False,
        "expected_groups": 1,
        "require_no_output_before_group": False,
    }
    if reset_name:
        pattern["reset_signal"] = reset_name
        pattern["reset_active_level"] = int(reset_active_level or 0)

    if scenario_kind == "reset_mid_progress" or "reset_clears_partial" in transition:
        pattern["respect_reset_clear"] = True
        pattern["expected_groups"] = 1
        return {
            "description": "Clear partial accumulation on reset and require the later full group to produce the only output event.",
            "trigger_condition": "When a partial valid stream is interrupted by reset and a later full valid group is driven.",
            "pass_condition": f"Before {group_size} accepted post-reset valid samples, valid_out remains low; after the later full post-reset group, one output event occurs and data_out equals the accumulated sum of that post-reset group.",
            "note": "Structured grouped-valid relation uses reset only as a finite state-clear event.",
            "reference_domain": f"group_size={group_size};allow_gaps=0;expected_groups=1;respect_reset_clear=1",
            "expected_transition": "reset_clears_partial_group",
            "oracle_pattern": pattern,
        }
    if scenario_kind == "multi_group_stream" or "multi_group" in transition:
        pattern["expected_groups"] = 2
        return {
            "description": "Observe two grouped accumulation closures in one finite valid stream.",
            "trigger_condition": "When two complete valid groups are driven in one deterministic stream.",
            "pass_condition": f"Before each completed group of {group_size} accepted valid samples, valid_out remains low; after each completed group, one output event occurs and data_out matches that group's accumulated sum.",
            "note": "Repeated-group relation remains event-based and avoids exact inter-group latency assumptions.",
            "reference_domain": f"group_size={group_size};allow_gaps=0;expected_groups=2",
            "expected_transition": "multi_group_sum",
            "oracle_pattern": pattern,
        }
    if scenario_kind == "gapped_valid_group" or "gapped" in transition:
        pattern["allow_gaps"] = True
        return {
            "description": "Count only valid-high samples toward grouped accumulation even when gaps occur between them.",
            "trigger_condition": "When the deterministic stimulus applies valid-high samples separated by valid-low gaps.",
            "pass_condition": f"Only valid-high samples count toward the {group_size}-sample accumulation group; after the full accepted group, valid_out asserts once and data_out equals the accumulated sum of the accepted samples.",
            "note": "Gap cycles are explicitly treated as non-accepting points in the grouped relation.",
            "reference_domain": f"group_size={group_size};allow_gaps=1;expected_groups=1",
            "expected_transition": "gapped_group_sum",
            "oracle_pattern": pattern,
        }
    if category == "negative":
        pattern["expected_groups"] = 0
        return {
            "description": "Keep the grouped accumulator quiet while valid-like gating remains deasserted.",
            "trigger_condition": "When the deterministic stimulus toggles data while valid_in stays low.",
            "pass_condition": f"Without {group_size} accepted valid samples, valid_out must remain low and no grouped accumulation output is justified.",
            "note": "Negative grouped-valid case remains functional but does not invent undocumented error signaling.",
            "reference_domain": f"group_size={group_size};allow_gaps=0;expected_groups=0",
            "expected_transition": "preclosure_quiet",
            "oracle_pattern": pattern,
        }
    if category == "basic" and scenario_kind in {"single_operation", ""}:
        pattern["expected_groups"] = 0
        pattern["require_no_output_before_group"] = True
        return {
            "description": "Reject premature grouped output before a full valid group has been accepted.",
            "trigger_condition": "When fewer than one full grouped-valid accumulation window is driven.",
            "pass_condition": f"Before {group_size} accepted valid samples have been observed, valid_out must remain low and no grouped output value is claimed.",
            "note": "Pre-closure quiet check is concrete because the deterministic stimulus drives only a finite prefix of one group.",
            "reference_domain": f"group_size={group_size};allow_gaps=0;expected_groups=0",
            "expected_transition": "preclosure_quiet",
            "oracle_pattern": pattern,
        }
    return {
        "description": "Observe one grouped accumulation closure and verify the concrete accumulated value relation.",
        "trigger_condition": "When the deterministic stimulus drives one complete grouped valid stream.",
        "pass_condition": f"Before {group_size} accepted valid samples, valid_out remains low; after the completed group, one output event occurs and data_out equals the accumulated sum.",
        "note": "Structured grouped-valid relation is derived from stable valid/data and output-valid/data naming plus finite plan stimulus.",
        "reference_domain": f"group_size={group_size};allow_gaps=0;expected_groups=1",
        "expected_transition": "single_group_sum",
        "oracle_pattern": pattern,
    }


def _build_ring_counter_progression_check(
    *,
    contract: DUTContract,
    plan_case: TestCasePlan,
    ring_family: dict[str, object] | None,
) -> OracleCheck | None:
    if ring_family is None:
        return None
    output_name = str(ring_family["state_output_signal"])
    if plan_case.category != "basic":
        return None
    return _make_check(
        case_id=plan_case.case_id,
        check_type=OracleCheckType.FUNCTIONAL,
        ordinal=907,
        description="Observe one-hot ring rotation across successive clocked states.",
        observed_signals=[output_name],
        trigger_condition="When reset is released and conservative clock-driven observation begins.",
        pass_condition="The ring counter output remains one-hot and successive observed states rotate by one bit across the conservative observation window.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="operation_applied"),
        strictness=OracleStrictness.CONSERVATIVE,
        confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.02),
        notes=["Autonomous ring progression check uses only externally visible output history."],
        semantic_tags=["operation_specific", "autonomous_progression"],
        relation_kind="one_hot_rotation_progression",
        comparison_operands=[output_name],
        reference_domain="one_hot_ring",
        expected_transition="rotation_by_one",
        oracle_pattern=json.dumps({"sample_count": 6}, sort_keys=True),
    )


def _build_traffic_light_progression_check(
    *,
    contract: DUTContract,
    plan_case: TestCasePlan,
    traffic_family: dict[str, object] | None,
) -> OracleCheck | None:
    if traffic_family is None:
        return None
    if plan_case.category != "protocol":
        return None
    request_signal = str(traffic_family.get("request_signal") or "")
    observed_signals = [
        str(traffic_family["red_signal"]),
        str(traffic_family["yellow_signal"]),
        str(traffic_family["green_signal"]),
    ]
    operands = [request_signal, *observed_signals]
    return _make_check(
        case_id=plan_case.case_id,
        check_type=OracleCheckType.FUNCTIONAL,
        ordinal=908,
        description="Observe mutually exclusive traffic-light phases and a bounded request-driven phase progression.",
        observed_signals=observed_signals,
        trigger_condition="When pass_request is pulsed during a conservative legal observation window.",
        pass_condition="Exactly one traffic-light phase is active at a time; a request-driven observation window eventually includes yellow and later red after green has been observed.",
        temporal_window=TemporalWindow(mode=TemporalWindowMode.EVENT_BASED, anchor="operation_applied"),
        strictness=OracleStrictness.CONSERVATIVE,
        confidence=_oracle_case_confidence(contract=contract, plan_case=plan_case, bonus=0.02),
        notes=["Traffic-light progression check remains event-based and does not assume exact phase dwell counts."],
        semantic_tags=["operation_specific", "fsm_progression"],
        relation_kind="traffic_light_phase_progression",
        comparison_operands=operands,
        reference_domain="mutually_exclusive_phases",
        expected_transition="green_then_yellow_then_red",
        oracle_pattern=json.dumps({"sample_count": 20}, sort_keys=True),
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
    semantic_tags: list[str] | None = None,
    relation_kind: str = "",
    expected_transition: str = "",
    comparison_operands: list[str] | None = None,
    reference_domain: str = "",
    oracle_pattern: str = "",
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
        oracle_pattern=oracle_pattern,
        relation_kind=relation_kind,
        expected_transition=expected_transition,
        comparison_operands=list(comparison_operands or []),
        reference_domain=reference_domain,
        semantic_tags=list(semantic_tags or []),
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


def _append_unique(existing: list[str], additions: list[str]) -> list[str]:
    return _deduped(list(existing) + list(additions))


def _oracle_case_list(
    *,
    protocol_cases: list[OracleCase],
    functional_cases: list[OracleCase],
    property_cases: list[OracleCase],
    oracle_class: str,
) -> list[OracleCase]:
    if oracle_class == "protocol":
        return protocol_cases
    if oracle_class == "functional":
        return functional_cases
    return property_cases


def _find_oracle_case(
    *,
    protocol_cases: list[OracleCase],
    functional_cases: list[OracleCase],
    property_cases: list[OracleCase],
    oracle_class: str,
    linked_plan_case_id: str,
) -> OracleCase | None:
    for oracle_case in _oracle_case_list(
        protocol_cases=protocol_cases,
        functional_cases=functional_cases,
        property_cases=property_cases,
        oracle_class=oracle_class,
    ):
        if oracle_case.linked_plan_case_id == linked_plan_case_id:
            return oracle_case
    return None


def _make_hybrid_oracle_case(*, oracle_class: str, linked_plan_case_id: str, category: str) -> OracleCase:
    return OracleCase(
        case_id=f"{oracle_class}_{linked_plan_case_id}_llm_001",
        linked_plan_case_id=linked_plan_case_id,
        category=category,
        checks=[],
        assumptions=[],
        unresolved_items=[],
        confidence=0.05,
        source="hybrid_llm_generated",
        notes=[],
    )


def _make_hybrid_check(
    *,
    case_id: str,
    ordinal: int,
    proposed_check,
    confidence: float,
) -> OracleCheck:
    return OracleCheck(
        check_id=f"{case_id}_{proposed_check.check_type}_{ordinal:03d}",
        check_type=proposed_check.check_type,
        description=proposed_check.description,
        observed_signals=_deduped(list(proposed_check.observed_signals)),
        trigger_condition=proposed_check.trigger_condition,
        pass_condition=proposed_check.pass_condition,
        temporal_window=TemporalWindow(
            mode=proposed_check.temporal_window.mode,
            min_cycles=proposed_check.temporal_window.min_cycles,
            max_cycles=proposed_check.temporal_window.max_cycles,
            anchor=proposed_check.temporal_window.anchor,
        ),
        strictness=proposed_check.strictness,
        oracle_pattern=str(getattr(proposed_check, "oracle_pattern", "") or ""),
        relation_kind=str(getattr(proposed_check, "relation_kind", "") or ""),
        expected_transition=str(getattr(proposed_check, "expected_transition", "") or ""),
        comparison_operands=_deduped(list(getattr(proposed_check, "comparison_operands", []) or [])),
        reference_domain=str(getattr(proposed_check, "reference_domain", "") or ""),
        semantic_tags=_deduped(list(getattr(proposed_check, "semantic_tags", []) or [])),
        confidence=max(0.05, min(confidence, 0.95)),
        source="hybrid_llm_generated",
        notes=_deduped(list(getattr(proposed_check, "notes", []) or [])),
    )


def _attach_signal_policies(*, oracle: OracleSpec, contract: DUTContract, plan: TestPlan) -> None:
    plan_cases = {case.case_id: case for case in plan.cases}
    weak_contract = _is_weak_contract(contract, plan)
    semantic_hints = _explicit_output_semantic_hints(contract)
    for oracle_case in [*oracle.protocol_oracles, *oracle.functional_oracles, *oracle.property_oracles]:
        plan_case = plan_cases.get(oracle_case.linked_plan_case_id)
        for check in oracle_case.checks:
            check.signal_policies = _build_signal_policies(
                contract=contract,
                plan_case=plan_case,
                check=check,
                weak_contract=weak_contract,
                semantic_hints=semantic_hints,
            )


def _build_signal_policies(
    *,
    contract: DUTContract,
    plan_case: TestCasePlan | None,
    check: OracleCheck,
    weak_contract: bool,
    semantic_hints: dict[str, SignalAssertionPolicy],
) -> dict[str, SignalAssertionPolicy]:
    policies: dict[str, SignalAssertionPolicy] = {}
    handshake_signals = set(contract.handshake_signals)
    allowed_unknowns = set(contract.allowed_unknowns)
    ambiguity_preserving = bool(plan_case and "ambiguity_preserving" in set(plan_case.semantic_tags))
    control_heavy_case = bool(plan_case and any(signal in _control_like_input_names(contract) for signal in plan_case.stimulus_signals))
    property_check = check.check_type == OracleCheckType.PROPERTY
    negative_like = bool(
        plan_case
        and (
            plan_case.category == "negative"
            or "invalid_illegal_input" in set(plan_case.semantic_tags)
        )
    )
    for signal in check.observed_signals:
        if signal in allowed_unknowns:
            policy = SignalAssertionPolicy(
                strength=AssertionStrength.GUARDED,
                allow_unknown=True,
                allow_high_impedance=True,
                rationale="contract_allowed_unknown",
            )
            policies[signal] = _finalize_signal_policy(
                policy=policy,
                contract=contract,
                plan_case=plan_case,
                check=check,
                signal=signal,
                control_heavy_case=control_heavy_case,
            )
            continue
        if signal in handshake_signals:
            policy = SignalAssertionPolicy(
                strength=AssertionStrength.GUARDED,
                allow_unknown=False,
                allow_high_impedance=False,
                rationale="protocol_visible_signal",
            )
            policies[signal] = _finalize_signal_policy(
                policy=policy,
                contract=contract,
                plan_case=plan_case,
                check=check,
                signal=signal,
                control_heavy_case=control_heavy_case,
            )
            continue
        if property_check and signal in _primary_data_outputs(contract):
            policy = SignalAssertionPolicy(
                strength=AssertionStrength.UNRESOLVED,
                allow_unknown=True,
                allow_high_impedance=True,
                rationale="property_guardrail_preserves_value_ambiguity",
            )
            policies[signal] = _finalize_signal_policy(
                policy=policy,
                contract=contract,
                plan_case=plan_case,
                check=check,
                signal=signal,
                control_heavy_case=control_heavy_case,
            )
            continue
        if property_check and signal in _scalar_status_outputs(contract) and _should_preserve_protocol_status_output_ambiguity(
            contract=contract,
            plan_case=plan_case,
        ):
            policy = SignalAssertionPolicy(
                strength=AssertionStrength.UNRESOLVED,
                allow_unknown=True,
                allow_high_impedance=True,
                rationale="property_guardrail_preserves_status_ambiguity",
            )
            policies[signal] = _finalize_signal_policy(
                policy=policy,
                contract=contract,
                plan_case=plan_case,
                check=check,
                signal=signal,
                control_heavy_case=control_heavy_case,
            )
            continue
        if negative_like:
            policy = SignalAssertionPolicy(
                strength=AssertionStrength.UNRESOLVED,
                allow_unknown=True,
                allow_high_impedance=True,
                rationale="negative_or_illegal_case_preserves_ambiguity",
            )
            policies[signal] = _finalize_signal_policy(
                policy=policy,
                contract=contract,
                plan_case=plan_case,
                check=check,
                signal=signal,
                control_heavy_case=control_heavy_case,
            )
            continue

        hinted_policy = semantic_hints.get(signal)
        if hinted_policy is not None:
            policy = hinted_policy.model_copy(deep=True)
            if weak_contract and policy.strength == AssertionStrength.EXACT and signal not in _primary_data_outputs(contract):
                policy = policy.model_copy(
                    update={
                        "strength": AssertionStrength.GUARDED,
                        "rationale": f"{policy.rationale}_downgraded_for_weak_contract",
                    }
                )
            if _should_preserve_primary_output_ambiguity(
                contract=contract,
                plan_case=plan_case,
                signal=signal,
                control_heavy_case=control_heavy_case,
            ):
                policy = policy.model_copy(
                    update={
                        "strength": AssertionStrength.UNRESOLVED,
                        "allow_unknown": True,
                        "allow_high_impedance": True,
                        "rationale": f"{policy.rationale}_downgraded_for_case_ambiguity",
                    }
                )
            if _should_preserve_scalar_status_output_ambiguity(
                contract=contract,
                plan_case=plan_case,
                signal=signal,
                control_heavy_case=control_heavy_case,
            ):
                policy = policy.model_copy(
                    update={
                        "strength": AssertionStrength.UNRESOLVED,
                        "allow_unknown": True,
                        "allow_high_impedance": True,
                        "rationale": f"{policy.rationale}_downgraded_for_status_edge_ambiguity",
                    }
                )
            policies[signal] = _finalize_signal_policy(
                policy=policy,
                contract=contract,
                plan_case=plan_case,
                check=check,
                signal=signal,
                control_heavy_case=control_heavy_case,
            )
            continue

        if signal in _primary_data_outputs(contract) and not ambiguity_preserving:
            if _should_preserve_primary_output_ambiguity(
                contract=contract,
                plan_case=plan_case,
                signal=signal,
                control_heavy_case=control_heavy_case,
            ):
                policy = SignalAssertionPolicy(
                    strength=AssertionStrength.UNRESOLVED,
                    allow_unknown=True,
                    allow_high_impedance=True,
                    rationale="primary_data_output_case_ambiguity",
                )
                policies[signal] = _finalize_signal_policy(
                    policy=policy,
                    contract=contract,
                    plan_case=plan_case,
                    check=check,
                    signal=signal,
                    control_heavy_case=control_heavy_case,
                )
                continue
            policy = SignalAssertionPolicy(
                strength=AssertionStrength.GUARDED,
                allow_unknown=False,
                allow_high_impedance=False,
                rationale="primary_data_output_guarded_definedness",
            )
            policies[signal] = _finalize_signal_policy(
                policy=policy,
                contract=contract,
                plan_case=plan_case,
                check=check,
                signal=signal,
                control_heavy_case=control_heavy_case,
            )
            continue

        policy = SignalAssertionPolicy(
            strength=AssertionStrength.UNRESOLVED,
            allow_unknown=True,
            allow_high_impedance=True,
            rationale="insufficient_structured_evidence",
        )
        policies[signal] = _finalize_signal_policy(
            policy=policy,
            contract=contract,
            plan_case=plan_case,
            check=check,
            signal=signal,
            control_heavy_case=control_heavy_case,
        )
    return policies


def _finalize_signal_policy(
    *,
    policy: SignalAssertionPolicy,
    contract: DUTContract,
    plan_case: TestCasePlan | None,
    check: OracleCheck,
    signal: str,
    control_heavy_case: bool,
) -> SignalAssertionPolicy:
    return policy.model_copy(
        update={
            "definedness_mode": _select_definedness_mode(
                policy=policy,
                contract=contract,
                plan_case=plan_case,
                check=check,
                signal=signal,
                control_heavy_case=control_heavy_case,
            ),
        }
    )


def _select_definedness_mode(
    *,
    policy: SignalAssertionPolicy,
    contract: DUTContract,
    plan_case: TestCasePlan | None,
    check: OracleCheck,
    signal: str,
    control_heavy_case: bool,
) -> DefinednessMode:
    if policy.strength == AssertionStrength.UNRESOLVED:
        return DefinednessMode.NOT_REQUIRED
    if policy.allow_unknown or policy.allow_high_impedance:
        return DefinednessMode.NOT_REQUIRED
    if check.check_type == OracleCheckType.PROPERTY:
        return DefinednessMode.NOT_REQUIRED
    if plan_case is None:
        return DefinednessMode.NOT_REQUIRED

    category = str(plan_case.category)
    if category in {"protocol", "back_to_back", "negative", "metamorphic", "regression"}:
        return DefinednessMode.NOT_REQUIRED

    if signal in set(contract.handshake_signals):
        return DefinednessMode.NOT_REQUIRED

    if signal in _scalar_status_outputs(contract):
        if _should_require_status_definedness(
            contract=contract,
            plan_case=plan_case,
            check=check,
            signal=signal,
        ):
            return DefinednessMode.AT_OBSERVATION
        return DefinednessMode.NOT_REQUIRED

    if signal in _primary_data_outputs(contract):
        if _should_require_primary_data_definedness(
            contract=contract,
            plan_case=plan_case,
            check=check,
            signal=signal,
            control_heavy_case=control_heavy_case,
        ):
            return DefinednessMode.AT_OBSERVATION
        return DefinednessMode.NOT_REQUIRED

    return DefinednessMode.NOT_REQUIRED


def _should_require_primary_data_definedness(
    *,
    contract: DUTContract,
    plan_case: TestCasePlan,
    check: OracleCheck,
    signal: str,
    control_heavy_case: bool,
) -> bool:
    if signal not in _primary_data_outputs(contract):
        return False
    if check.check_type != OracleCheckType.FUNCTIONAL:
        return False
    if str(plan_case.category) == "reset":
        return False
    if contract.timing.sequential_kind == SequentialKind.SEQ:
        if contract.timing.latency_model != LatencyModel.FIXED:
            return False
        semantic_tags = set(plan_case.semantic_tags)
        return bool(
            str(plan_case.category) == "basic"
            and not control_heavy_case
            and "operation_specific" in semantic_tags
            and _case_covers_all_business_inputs(contract=contract, plan_case=plan_case)
        )
    if str(plan_case.category) == "basic":
        return _case_covers_all_business_inputs(contract=contract, plan_case=plan_case)
    if str(plan_case.category) == "edge":
        return _case_covers_all_business_inputs(contract=contract, plan_case=plan_case) and "operation_specific" in set(
            plan_case.semantic_tags
        )
    return False


def _should_require_status_definedness(
    *,
    contract: DUTContract,
    plan_case: TestCasePlan,
    check: OracleCheck,
    signal: str,
) -> bool:
    if signal not in _scalar_status_outputs(contract):
        return False
    if check.check_type != OracleCheckType.FUNCTIONAL:
        return False
    if str(plan_case.category) == "reset":
        if _is_scalar_data_like_output_signal(contract=contract, signal=signal):
            return False
        return _signal_has_explicit_reset_behavior(contract=contract, signal=signal)
    if contract.timing.sequential_kind == SequentialKind.SEQ:
        return False
    return str(plan_case.category) == "basic" and _case_covers_all_business_inputs(contract=contract, plan_case=plan_case)


def _is_scalar_data_like_output_signal(*, contract: DUTContract, signal: str) -> bool:
    signal_width = None
    for port in contract.ports:
        if port.name == signal and port.direction in {PortDirection.OUTPUT, PortDirection.INOUT}:
            signal_width = port.width if isinstance(port.width, int) else None
            break
    if signal_width != 1:
        return False
    lowered = signal.lower()
    data_like_tokens = {"data", "dout", "stream", "serial", "value", "payload", "out"}
    status_like_tokens = {"valid", "ready", "empty", "full", "done", "busy", "flag", "err", "error", "zero", "overflow", "carry", "negative"}
    tokens = {token for token in re.split(r"[^a-z0-9]+", lowered) if token}
    if any(token in status_like_tokens for token in tokens):
        return False
    if lowered in {"dout", "data_out", "q", "o"}:
        return True
    return any(token in data_like_tokens for token in tokens)


def _case_covers_all_business_inputs(*, contract: DUTContract, plan_case: TestCasePlan) -> bool:
    business_inputs = {
        port.name
        for port in contract.ports
        if port.direction == PortDirection.INPUT
        and port.name not in {clock.name for clock in contract.clocks}
        and port.name not in {reset.name for reset in contract.resets}
    }
    if not business_inputs:
        return False
    return business_inputs.issubset(set(plan_case.stimulus_signals))


def _explicit_output_semantic_hints(contract: DUTContract) -> dict[str, SignalAssertionPolicy]:
    hints: dict[str, SignalAssertionPolicy] = {}
    for signal in _output_signal_names(contract):
        matching_lines = _assumption_lines_for_signal(contract, signal)
        if not matching_lines:
            continue
        behavior_lines = [line for line in matching_lines if _line_explicitly_targets_signal_behavior(line=line, signal=signal)]
        has_explicit_behavior = bool(behavior_lines)
        has_high_impedance = any("high-impedance" in line or "'z'" in line or " 1'bz" in line for line in behavior_lines)
        if has_explicit_behavior and has_high_impedance:
            hints[signal] = SignalAssertionPolicy(
                strength=AssertionStrength.GUARDED,
                allow_unknown=True,
                allow_high_impedance=True,
                rationale="explicit_conditional_high_impedance_behavior",
            )
        elif has_explicit_behavior:
            hints[signal] = SignalAssertionPolicy(
                strength=AssertionStrength.EXACT,
                allow_unknown=False,
                allow_high_impedance=False,
                rationale="explicit_output_behavior",
            )
    return hints


def _line_explicitly_targets_signal_behavior(*, line: str, signal: str) -> bool:
    normalized = re.sub(r"\s+", " ", str(line or "").strip().lower())
    normalized = normalized.replace("(", " ").replace(")", " ")
    signal_lower = signal.lower()
    target_patterns = (
        rf"\b{re.escape(signal_lower)}\b(?:\s+(?:output|flag|register|reg|signal))?\s+(?:is|are)\s+(?:set|assigned|determined|updated)\b",
        rf"\b{re.escape(signal_lower)}\b\s*(?:<=|=)\s*",
        rf"\b(?:assigned|assigns|driven|drives|set|sets|updated|updates|written)\b.+\bto\b.+\b{re.escape(signal_lower)}\b",
    )
    return any(re.search(pattern, normalized) for pattern in target_patterns)


def _signal_has_explicit_reset_behavior(*, contract: DUTContract, signal: str) -> bool:
    for line in _assumption_lines_for_signal(contract, signal):
        normalized = str(line or "").lower()
        if "reset" not in normalized and "rst" not in normalized:
            continue
        if _line_explicitly_targets_signal_behavior(line=normalized, signal=signal):
            return True
    return False


def _assumption_lines_for_signal(contract: DUTContract, signal: str) -> list[str]:
    pattern = re.compile(rf"\b{re.escape(signal.lower())}\b")
    return [line.lower() for line in contract.assumptions if pattern.search(str(line or "").lower())]


def _output_signal_names(contract: DUTContract) -> list[str]:
    return [
        port.name
        for port in contract.ports
        if port.direction in {PortDirection.OUTPUT, PortDirection.INOUT} and port.name
    ]


def _primary_data_outputs(contract: DUTContract) -> set[str]:
    return {
        port.name
        for port in contract.ports
        if port.direction == PortDirection.OUTPUT
        and isinstance(port.width, int)
        and port.width > 1
        and port.name in set(contract.observable_outputs)
    }


def _control_like_input_names(contract: DUTContract) -> set[str]:
    control_tokens = {
        "opcode",
        "op",
        "func",
        "aluc",
        "sel",
        "mode",
        "cmd",
        "ctrl",
        "control",
        "rw",
        "en",
        "enable",
        "valid",
        "ready",
        "start",
        "req",
        "ack",
        "done",
        "load",
        "write",
        "read",
    }
    names: set[str] = set()
    for port in contract.ports:
        if port.direction != PortDirection.INPUT:
            continue
        lower = port.name.lower()
        tokens = [token for token in re.split(r"[^a-z0-9]+", lower) if token]
        if lower in control_tokens or any(token in control_tokens for token in tokens):
            names.add(port.name)
    return names


def _should_preserve_primary_output_ambiguity(
    *,
    contract: DUTContract,
    plan_case: TestCasePlan | None,
    signal: str,
    control_heavy_case: bool,
) -> bool:
    if plan_case is None or signal not in _primary_data_outputs(contract):
        return False
    if plan_case.category in {"edge", "back_to_back"} and control_heavy_case:
        return True
    if contract.timing.sequential_kind == SequentialKind.SEQ and control_heavy_case:
        return True
    return False


def _scalar_status_outputs(contract: DUTContract) -> set[str]:
    handshake_signals = set(contract.handshake_signals)
    return {
        port.name
        for port in contract.ports
        if port.direction == PortDirection.OUTPUT
        and isinstance(port.width, int)
        and port.width == 1
        and port.name in set(contract.observable_outputs)
        and port.name not in handshake_signals
    }


def _should_preserve_scalar_status_output_ambiguity(
    *,
    contract: DUTContract,
    plan_case: TestCasePlan | None,
    signal: str,
    control_heavy_case: bool,
) -> bool:
    if plan_case is None or signal not in _scalar_status_outputs(contract):
        return False
    if contract.timing.sequential_kind != SequentialKind.SEQ:
        return False
    if plan_case.category not in {"edge", "back_to_back"}:
        return False
    semantic_tags = set(plan_case.semantic_tags)
    if "operation_specific" in semantic_tags:
        return False
    return "width_sensitive" in semantic_tags or control_heavy_case


def _should_preserve_protocol_status_output_ambiguity(
    *,
    contract: DUTContract,
    plan_case: TestCasePlan | None,
) -> bool:
    if plan_case is None or plan_case.category != "protocol":
        return False
    if contract.timing.sequential_kind != SequentialKind.SEQ:
        return False
    semantic_tags = set(plan_case.semantic_tags)
    coverage_tags = set(plan_case.coverage_tags)
    if "operation_specific" in semantic_tags:
        return False
    return bool(
        "ambiguity_preserving" in semantic_tags
        or {"sequence", "push_pop", "persistence", "stability", "reset_protocol"} & coverage_tags
    )


def _is_duplicate_oracle_check(candidate: OracleCheck, existing_checks: list[OracleCheck]) -> bool:
    candidate_signature = (
        candidate.check_type,
        _single_line(candidate.description).lower(),
        tuple(candidate.observed_signals),
        _single_line(candidate.trigger_condition).lower(),
        _single_line(candidate.pass_condition).lower(),
    )
    for existing in existing_checks:
        existing_signature = (
            existing.check_type,
            _single_line(existing.description).lower(),
            tuple(existing.observed_signals),
            _single_line(existing.trigger_condition).lower(),
            _single_line(existing.pass_condition).lower(),
        )
        if candidate_signature == existing_signature:
            return True
    return False


def _is_conflicting_oracle_check(candidate: OracleCheck, existing_checks: list[OracleCheck]) -> bool:
    for existing in existing_checks:
        if existing.check_type != candidate.check_type:
            continue
        if set(existing.observed_signals) != set(candidate.observed_signals):
            continue
        same_trigger = _single_line(existing.trigger_condition).lower() == _single_line(candidate.trigger_condition).lower()
        same_description = _single_line(existing.description).lower() == _single_line(candidate.description).lower()
        different_pass = _single_line(existing.pass_condition).lower() != _single_line(candidate.pass_condition).lower()
        if different_pass and (same_trigger or same_description):
            return True
    return False


def _single_line(text: str) -> str:
    return " ".join(str(text or "").split())
