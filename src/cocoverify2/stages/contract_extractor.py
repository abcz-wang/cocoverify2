"""Rule-based contract extraction for Phase 1."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from cocoverify2.core.errors import ConfigurationError, ParserError, StageExecutionError
from cocoverify2.core.models import ClockSpec, DUTContract, HandshakeGroup, ResetSpec, TimingSpec
from cocoverify2.core.types import LatencyModel, PortDirection, SequentialKind, StageName
from cocoverify2.parsers.golden_interface_parser import GoldenInterfaceHints, parse_golden_interface_text
from cocoverify2.parsers.rtl_parser import ParsedRTLModule, parse_rtl_file
from cocoverify2.utils.files import ensure_dir, read_text, write_json, write_yaml
from cocoverify2.utils.logging import get_logger

_CLOCK_EXACT_NAMES = {"clk", "clock", "i_clk", "aclk", "core_clk", "sys_clk"}
_RESET_EXACT_NAMES = {"rst", "rst_n", "reset", "resetn", "reset_n", "aresetn", "areset"}
_HANDSHAKE_KEYWORDS = ("valid", "ready", "req", "ack", "start", "done")


class ContractExtractor:
    """Extract a conservative structural contract from RTL and optional hints."""

    def __init__(self) -> None:
        """Initialize the extractor with a stage-scoped logger."""
        self.logger = get_logger(__name__)

    def run(
        self,
        *,
        rtl_paths: list[Path],
        task_description: str | None,
        spec_text: str | None,
        golden_interface_text: str | None,
        out_dir: Path,
    ) -> DUTContract:
        """Extract a ``DUTContract`` and persist contract artifacts to disk."""
        if not rtl_paths:
            raise ConfigurationError("Contract extraction requires at least one RTL path.")

        parsed_modules: list[ParsedRTLModule] = []
        parse_errors: list[ParserError] = []
        for rtl_path in rtl_paths:
            try:
                module = parse_rtl_file(rtl_path)
                parsed_modules.append(module)
                self.logger.debug("Parsed RTL module '%s' from %s", module.module_name, rtl_path)
            except ParserError as exc:
                parse_errors.append(exc)

        if not parsed_modules:
            raise StageExecutionError(
                stage=StageName.CONTRACT,
                message="Contract extraction could not parse any RTL modules.",
                evidence={"parser_errors": [self._serialize_parser_error(error) for error in parse_errors]},
            )

        primary = parsed_modules[0]
        warnings = list(primary.warnings)
        ambiguities: list[str] = []
        assumptions: list[str] = []
        source_map: dict[str, list[str]] = defaultdict(list)

        if len(parsed_modules) > 1:
            module_names = [module.module_name for module in parsed_modules]
            ambiguities.append(
                f"Multiple RTL modules were provided ({module_names}); using '{primary.module_name}' from '{primary.source_path.name}' as the primary contract source."
            )
            warnings.append("Additional RTL modules were ignored for the initial contract extraction.")

        for parser_error in parse_errors:
            warnings.append(str(parser_error))

        for field_name in ("module_name",):
            _append_source(source_map, field_name, f"rtl:{primary.source_path.name}")
        for name in primary.parameters:
            _append_source(source_map, f"parameters.{name}", f"rtl:{primary.source_path.name}")
        for port in primary.ports:
            _append_source(source_map, f"ports.{port.name}", f"rtl:{primary.source_path.name}")

        clocks = self._detect_clocks(primary)
        resets = self._detect_resets(primary)
        handshake_groups, handshake_signals, handshake_ambiguities = self._detect_handshake_groups(primary)
        ambiguities.extend(handshake_ambiguities)
        timing, timing_ambiguities = self._infer_timing(
            primary,
            clocks=clocks,
            resets=resets,
            handshake_groups=handshake_groups,
            task_description=task_description,
            spec_text=spec_text,
        )
        ambiguities.extend(timing_ambiguities)

        for clock in clocks:
            _append_source(source_map, f"clocks.{clock.name}", clock.source)
        for reset in resets:
            _append_source(source_map, f"resets.{reset.name}", reset.source)
        for group in handshake_groups:
            group_key = group.group_name if group.group_name else "default"
            _append_source(source_map, f"handshake_groups.{group.pattern}.{group_key}", group.source)
        for signal_name in handshake_signals:
            _append_source(source_map, f"handshake_signals.{signal_name}", "flattened_from_handshake_groups")
        _append_source(source_map, "timing", timing.source)

        golden_hints = parse_golden_interface_text(golden_interface_text)
        self._merge_golden_interface_hints(
            primary=primary,
            hints=golden_hints,
            clocks=clocks,
            resets=resets,
            assumptions=assumptions,
            ambiguities=ambiguities,
            source_map=source_map,
        )
        warnings.extend(golden_hints.warnings)
        assumptions.extend(golden_hints.assumptions)
        ambiguities.extend(golden_hints.ambiguities)

        illegal_constraints, spec_assumptions, spec_ambiguities = self._extract_text_hints(
            ports=primary.ports,
            task_description=task_description,
            spec_text=spec_text,
            clocks=clocks,
            resets=resets,
            source_map=source_map,
        )
        assumptions.extend(spec_assumptions)
        ambiguities.extend(spec_ambiguities)

        if not primary.ports:
            ambiguities.append("No ports were parsed from the module header.")
        elif all(port.direction == PortDirection.UNKNOWN for port in primary.ports):
            ambiguities.append("All parsed ports have unknown directions; the module may use a non-ANSI header.")

        if handshake_groups:
            assumptions.append("handshake_signals is a flattened compatibility view derived from handshake_groups.")

        observable_outputs = [port.name for port in primary.ports if port.direction in {PortDirection.OUTPUT, PortDirection.INOUT}]
        if not observable_outputs:
            ambiguities.append("No observable outputs were identified from the parsed RTL header.")

        self._add_reset_polarity_ambiguities(resets, ambiguities)
        self._dedupe_in_place(warnings)
        self._dedupe_in_place(ambiguities)
        self._dedupe_in_place(assumptions)
        self._dedupe_in_place(illegal_constraints)

        contract = DUTContract(
            module_name=primary.module_name,
            rtl_sources=rtl_paths,
            parameters=primary.parameters,
            ports=primary.ports,
            clocks=clocks,
            resets=resets,
            handshake_groups=handshake_groups,
            handshake_signals=handshake_signals,
            timing=timing,
            observable_outputs=observable_outputs,
            illegal_input_constraints=illegal_constraints,
            assumptions=assumptions,
            ambiguities=ambiguities,
            source_map=dict(source_map),
            extraction_warnings=warnings,
            contract_confidence=self._estimate_contract_confidence(
                module=primary,
                clocks=clocks,
                resets=resets,
                timing=timing,
                observable_outputs=observable_outputs,
                ambiguities=ambiguities,
                warnings=warnings,
            ),
        )
        self._dump_contract_artifacts(contract, out_dir)
        return contract

    def _detect_clocks(self, module: ParsedRTLModule) -> list[ClockSpec]:
        clocks: dict[str, ClockSpec] = {}
        edge_signals = re.findall(r"(posedge|negedge)\s+([A-Za-z_][A-Za-z0-9_$]*)", module.body_text)
        posedge_names = {name for edge, name in edge_signals if edge == "posedge"}
        for port in module.ports:
            clock_confidence = _clock_name_confidence(port.name)
            reset_confidence = _reset_name_confidence(port.name)
            if clock_confidence > reset_confidence and _is_scalar_input_like_port(port):
                clocks[port.name] = ClockSpec(name=port.name, source="rtl_heuristic", confidence=clock_confidence)
            elif port.name in posedge_names and reset_confidence == 0.0 and _is_scalar_input_like_port(port):
                clocks[port.name] = ClockSpec(name=port.name, source="rtl_heuristic", confidence=0.8)
        for signal_name in posedge_names:
            if (
                signal_name not in clocks
                and _reset_name_confidence(signal_name) == 0.0
                and any(port.name == signal_name and _is_scalar_input_like_port(port) for port in module.ports)
            ):
                clocks[signal_name] = ClockSpec(name=signal_name, source="rtl_heuristic", confidence=0.8)
        return list(clocks.values())

    def _detect_resets(self, module: ParsedRTLModule) -> list[ResetSpec]:
        resets: dict[str, ResetSpec] = {}
        edge_signals = re.findall(r"(posedge|negedge)\s+([A-Za-z_][A-Za-z0-9_$]*)", module.body_text)
        sensitivity = [name for _, name in edge_signals]
        negative_edge_names = {name for edge, name in edge_signals if edge == "negedge"}
        for port in module.ports:
            reset_confidence = _reset_name_confidence(port.name)
            clock_confidence = _clock_name_confidence(port.name)
            if (
                (reset_confidence <= clock_confidence and port.name not in negative_edge_names)
                or not _is_scalar_input_like_port(port)
            ):
                continue
            active_level, level_confidence = _guess_reset_polarity(port.name)
            resets[port.name] = ResetSpec(
                name=port.name,
                active_level=active_level,
                source="rtl_heuristic",
                confidence=max(reset_confidence, level_confidence),
            )
        for signal_name in sensitivity:
            if signal_name in resets:
                continue
            if signal_name in negative_edge_names and any(port.name == signal_name and _is_scalar_input_like_port(port) for port in module.ports):
                active_level, level_confidence = _guess_reset_polarity(signal_name)
                resets[signal_name] = ResetSpec(
                    name=signal_name,
                    active_level=active_level,
                    source="rtl_heuristic",
                    confidence=max(0.45, level_confidence),
                )
        return list(resets.values())

    def _detect_handshake_groups(self, module: ParsedRTLModule) -> tuple[list[HandshakeGroup], list[str], list[str]]:
        groups: list[HandshakeGroup] = []
        ambiguities: list[str] = []
        for pattern_name, roles in (
            ("valid_ready", ("valid", "ready")),
            ("req_ack", ("req", "ack")),
            ("start_done", ("start", "done")),
        ):
            pattern_groups, pattern_ambiguities = _build_handshake_groups(module.ports, pattern=pattern_name, roles=roles)
            groups.extend(pattern_groups)
            ambiguities.extend(pattern_ambiguities)

        flattened_signals: list[str] = []
        for group in groups:
            for signal_name in group.signals.values():
                if signal_name not in flattened_signals:
                    flattened_signals.append(signal_name)
        return groups, flattened_signals, ambiguities

    def _infer_timing(
        self,
        module: ParsedRTLModule,
        *,
        clocks: list[ClockSpec],
        resets: list[ResetSpec],
        handshake_groups: list[HandshakeGroup],
        task_description: str | None,
        spec_text: str | None,
    ) -> tuple[TimingSpec, list[str]]:
        body_lower = module.body_text.lower()
        ambiguities: list[str] = []
        has_control_interface = bool(clocks or resets)
        has_structured_handshake = bool(handshake_groups)
        has_sequential_evidence = re.search(r"\balways_ff\b", body_lower) or re.search(
            r"always\s*@\s*\([^)]*(posedge|negedge)",
            body_lower,
        )
        has_comb_evidence = re.search(r"\balways_comb\b", body_lower) or "assign" in body_lower

        if has_sequential_evidence:
            return TimingSpec(
                sequential_kind=SequentialKind.SEQ,
                latency_model=LatencyModel.UNKNOWN,
                source="rtl_heuristic",
                confidence=0.9,
            ), ambiguities

        if has_comb_evidence and not has_control_interface and not has_structured_handshake:
            return TimingSpec(
                sequential_kind=SequentialKind.COMB,
                latency_model=LatencyModel.UNKNOWN,
                source="rtl_heuristic",
                confidence=0.65,
            ), ambiguities

        if has_comb_evidence and (has_control_interface or has_structured_handshake):
            ambiguities.append(
                "Combinational body constructs were found, but detected clock/reset or handshake structure makes the timing model ambiguous."
            )
            return TimingSpec(
                sequential_kind=SequentialKind.UNKNOWN,
                latency_model=LatencyModel.UNKNOWN,
                source="rtl_heuristic",
                confidence=0.2,
            ), ambiguities

        combined = "\n".join(part for part in (task_description or "", spec_text or "") if part).lower()
        if "combinational" in combined and not has_control_interface and not has_structured_handshake:
            return TimingSpec(
                sequential_kind=SequentialKind.COMB,
                latency_model=LatencyModel.UNKNOWN,
                source="spec_hint",
                confidence=0.4,
            ), ambiguities
        if any(token in combined for token in ("sequential", "clocked", "registered")):
            return TimingSpec(
                sequential_kind=SequentialKind.SEQ,
                latency_model=LatencyModel.UNKNOWN,
                source="spec_hint",
                confidence=0.4,
            ), ambiguities
        if has_control_interface and has_structured_handshake:
            ambiguities.append(
                "Clock/reset candidates and a structured handshake interface were detected, but there is not enough behavioral evidence to classify timing as comb or seq."
            )
            return TimingSpec(
                sequential_kind=SequentialKind.UNKNOWN,
                latency_model=LatencyModel.UNKNOWN,
                source="rtl_heuristic",
                confidence=0.25,
            ), ambiguities
        if has_control_interface:
            ambiguities.append("Clock/reset candidates were detected, but there is not enough behavioral evidence to classify timing.")
            return TimingSpec(
                sequential_kind=SequentialKind.UNKNOWN,
                latency_model=LatencyModel.UNKNOWN,
                source="rtl_heuristic",
                confidence=0.15,
            ), ambiguities
        return TimingSpec(source="unknown", confidence=0.0), ambiguities

    def _merge_golden_interface_hints(
        self,
        *,
        primary: ParsedRTLModule,
        hints: GoldenInterfaceHints,
        clocks: list[ClockSpec],
        resets: list[ResetSpec],
        assumptions: list[str],
        ambiguities: list[str],
        source_map: dict[str, list[str]],
    ) -> None:
        port_lookup = {port.name: port for port in primary.ports}
        for port_name in hints.port_names:
            if port_name in port_lookup:
                _append_source(source_map, f"ports.{port_name}", "golden_interface")
            else:
                ambiguities.append(f"Golden interface mentioned port '{port_name}', but it was not found in the RTL header.")

        for clock_hint in hints.clocks:
            existing = _find_by_name(clocks, clock_hint.name)
            if existing is None:
                hinted_port = port_lookup.get(clock_hint.name)
                if hinted_port and _is_scalar_input_like_port(hinted_port):
                    clocks.append(clock_hint)
                    _append_source(source_map, f"clocks.{clock_hint.name}", "golden_interface")
                elif hinted_port is None:
                    ambiguities.append(
                        f"Golden interface described clock '{clock_hint.name}', but the signal was not found in the RTL ports."
                    )
                else:
                    ambiguities.append(
                        f"Golden interface described clock '{clock_hint.name}', but the RTL port is not a scalar input-like signal."
                    )
                continue
            existing.confidence = max(existing.confidence, clock_hint.confidence)
            existing.source = "golden_interface"
            _append_source(source_map, f"clocks.{clock_hint.name}", "golden_interface")

        for reset_hint in hints.resets:
            existing_reset = _find_by_name(resets, reset_hint.name)
            if existing_reset is None:
                hinted_port = port_lookup.get(reset_hint.name)
                if hinted_port and _is_scalar_input_like_port(hinted_port):
                    resets.append(reset_hint)
                    _append_source(source_map, f"resets.{reset_hint.name}", "golden_interface")
                elif hinted_port is None:
                    ambiguities.append(
                        f"Golden interface described reset '{reset_hint.name}', but the signal was not found in the RTL ports."
                    )
                else:
                    ambiguities.append(
                        f"Golden interface described reset '{reset_hint.name}', but the RTL port is not a scalar input-like signal."
                    )
                continue
            if reset_hint.active_level is not None:
                existing_reset.active_level = reset_hint.active_level
            existing_reset.confidence = max(existing_reset.confidence, reset_hint.confidence)
            existing_reset.source = "golden_interface"
            _append_source(source_map, f"resets.{reset_hint.name}", "golden_interface")

        assumptions.extend(hints.assumptions)

    def _extract_text_hints(
        self,
        *,
        ports: list[PortSpec],
        task_description: str | None,
        spec_text: str | None,
        clocks: list[ClockSpec],
        resets: list[ResetSpec],
        source_map: dict[str, list[str]],
    ) -> tuple[list[str], list[str], list[str]]:
        illegal_constraints: list[str] = []
        assumptions: list[str] = []
        ambiguities: list[str] = []
        combined_lines: list[str] = []
        if task_description:
            combined_lines.extend(task_description.splitlines())
        if spec_text:
            combined_lines.extend(spec_text.splitlines())

        port_lookup = {port.name.lower(): port.name for port in ports}
        control_hint_candidates = {port.name for port in ports if _is_scalar_input_like_port(port)}
        output_hint_candidates = {
            port.name
            for port in ports
            if port.direction in {PortDirection.OUTPUT, PortDirection.INOUT}
        }
        for raw_line in combined_lines:
            line = raw_line.strip()
            if not line:
                continue
            line_lower = line.lower()
            if any(token in line_lower for token in ("illegal", "invalid", "must not", "undefined")):
                illegal_constraints.append(line)
                _append_source(source_map, "illegal_input_constraints", "spec_hint")
            if "clock" in line_lower:
                for matched_name in _collect_port_names_in_text(line_lower, port_lookup):
                    if matched_name not in control_hint_candidates:
                        continue
                    if not _supports_clock_hint(line_lower, matched_name, port_lookup):
                        continue
                    if _has_strong_role(resets, matched_name):
                        ambiguities.append(
                            f"Spec/clock hint mentioned '{matched_name}', but the signal is already strongly classified as a reset; preserving the existing role."
                        )
                        continue
                    existing_clock = _find_by_name(clocks, matched_name)
                    if existing_clock is None:
                        clocks.append(ClockSpec(name=matched_name, source="spec_hint", confidence=0.6))
                    else:
                        existing_clock.confidence = max(existing_clock.confidence, 0.6)
                        existing_clock.source = "spec_hint"
                    _append_source(source_map, f"clocks.{matched_name}", "spec_hint")
            if "reset" in line_lower:
                matched_reset_names = [
                    name
                    for name in _collect_port_names_in_text(line_lower, port_lookup)
                    if name in control_hint_candidates
                    if _supports_reset_hint(line_lower, name, port_lookup)
                ]
                if matched_reset_names:
                    active_level: int | None = None
                    if "active low" in line_lower or "active-low" in line_lower:
                        active_level = 0
                    elif "active high" in line_lower or "active-high" in line_lower:
                        active_level = 1
                    for matched_name in matched_reset_names:
                        if _has_strong_role(clocks, matched_name):
                            ambiguities.append(
                                f"Spec/reset hint mentioned '{matched_name}', but the signal is already strongly classified as a clock; preserving the existing role."
                            )
                            continue
                        existing_reset = _find_by_name(resets, matched_name)
                        if existing_reset is None:
                            resets.append(
                                ResetSpec(
                                    name=matched_name,
                                    active_level=active_level,
                                    source="spec_hint",
                                    confidence=0.65,
                                )
                            )
                        else:
                            if active_level is not None:
                                existing_reset.active_level = active_level
                            existing_reset.confidence = max(existing_reset.confidence, 0.65)
                            existing_reset.source = "spec_hint"
                        _append_source(source_map, f"resets.{matched_name}", "spec_hint")
                else:
                    ambiguities.append(f"Spec/reset hint could not be mapped to a known reset port: {line}")
            if any(token in line_lower for token in ("fixed latency", "variable latency", "latency")):
                assumptions.append(line)
            if _looks_like_output_behavior_hint(line_lower, output_hint_candidates, port_lookup):
                assumptions.append(line)
        return illegal_constraints, assumptions, ambiguities

    def _add_reset_polarity_ambiguities(self, resets: Iterable[ResetSpec], ambiguities: list[str]) -> None:
        for reset in resets:
            if reset.active_level is None:
                ambiguities.append(f"Reset polarity for '{reset.name}' is unresolved.")
            elif reset.source == "rtl_heuristic":
                ambiguities.append(f"Reset polarity for '{reset.name}' is inferred heuristically from the signal name or sensitivity list.")

    def _dedupe_in_place(self, items: list[str]) -> None:
        """Deduplicate a list while preserving insertion order."""
        seen: set[str] = set()
        unique_items: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            unique_items.append(item)
        items[:] = unique_items

    def _estimate_contract_confidence(
        self,
        *,
        module: ParsedRTLModule,
        clocks: list[ClockSpec],
        resets: list[ResetSpec],
        timing: TimingSpec,
        observable_outputs: list[str],
        ambiguities: list[str],
        warnings: list[str],
    ) -> float:
        total_ports = len(module.ports)
        known_direction_ports = sum(1 for port in module.ports if port.direction != PortDirection.UNKNOWN)
        known_direction_ratio = (known_direction_ports / total_ports) if total_ports else 0.0

        score = 0.1 if module.module_name else 0.0
        if total_ports:
            score += 0.2
        score += 0.25 * known_direction_ratio
        if observable_outputs:
            score += 0.1
        if clocks:
            score += 0.05
        if resets:
            score += 0.05
        score += 0.15 * timing.confidence

        penalty = min(0.25, 0.05 * len(warnings))
        penalty += min(0.25, 0.05 * len(ambiguities))
        if known_direction_ratio < 0.5:
            penalty += 0.15
        if not observable_outputs:
            penalty += 0.1
        if timing.sequential_kind == SequentialKind.UNKNOWN:
            penalty += 0.1

        return max(0.05, min(score - penalty, 0.95))

    def _dump_contract_artifacts(self, contract: DUTContract, out_dir: Path) -> None:
        contract_dir = ensure_dir(out_dir / "contract")
        contract_json_path = contract_dir / "contract.json"
        summary_yaml_path = contract_dir / "contract_summary.yaml"
        write_json(contract_json_path, contract.model_dump(mode="json"))
        write_yaml(summary_yaml_path, _build_contract_summary(contract))
        self.logger.info("Wrote contract artifacts to %s", contract_dir)

    def _serialize_parser_error(self, error: ParserError) -> dict[str, str | None]:
        return {
            "parser_name": error.parser_name,
            "message": error.message,
            "path": str(error.path) if error.path is not None else None,
            "snippet": error.snippet,
        }


def _build_contract_summary(contract: DUTContract) -> dict[str, object]:
    return {
        "module_name": contract.module_name,
        "rtl_sources": [str(path) for path in contract.rtl_sources],
        "parameters": contract.parameters,
        "port_count": len(contract.ports),
        "ports": [port.model_dump(mode="json") for port in contract.ports],
        "clock_names": [clock.name for clock in contract.clocks],
        "reset_names": [reset.name for reset in contract.resets],
        "handshake_groups": [group.model_dump(mode="json") for group in contract.handshake_groups],
        "handshake_signals": contract.handshake_signals,
        "timing": contract.timing.model_dump(mode="json"),
        "observable_outputs": contract.observable_outputs,
        "ambiguities": contract.ambiguities,
        "extraction_warnings": contract.extraction_warnings,
        "contract_confidence": contract.contract_confidence,
    }


def _append_source(source_map: dict[str, list[str]], key: str, source: str) -> None:
    if source and source not in source_map[key]:
        source_map[key].append(source)


def _find_by_name(items: Iterable[ClockSpec | ResetSpec], name: str) -> ClockSpec | ResetSpec | None:
    for item in items:
        if item.name == name:
            return item
    return None


def _is_scalar_input_like_port(port: PortSpec) -> bool:
    if port.direction not in {PortDirection.INPUT, PortDirection.UNKNOWN}:
        return False
    width = port.width
    if isinstance(width, int):
        return width == 1
    if isinstance(width, str):
        return False
    return port.raw_range is None


def _looks_like_output_behavior_hint(
    line_lower: str,
    output_hint_candidates: set[str],
    port_lookup: dict[str, str],
) -> bool:
    if not output_hint_candidates:
        return False
    behavior_tokens = (
        " is set ",
        " are set ",
        " is assigned ",
        " are assigned ",
        " assigned to ",
        " is determined ",
        " are determined ",
        " indicating whether ",
        " means if ",
        " concatenated ",
        " formed ",
        " lower ",
        " upper ",
        " high-impedance",
        "'z'",
    )
    if not any(token in line_lower for token in behavior_tokens):
        return False
    return any(name in output_hint_candidates for name in _collect_port_names_in_text(line_lower, port_lookup))


def _clock_name_confidence(name: str) -> float:
    lower = name.lower()
    if lower in _CLOCK_EXACT_NAMES:
        return 0.95
    if lower.endswith("_clk") or lower.startswith("clk_") or lower.endswith("clk") or "clock" in lower:
        return 0.7
    return 0.0


def _reset_name_confidence(name: str) -> float:
    lower = name.lower()
    if lower in _RESET_EXACT_NAMES:
        return 0.9
    if lower.endswith("_rst") or lower.startswith("rst_") or "reset" in lower:
        return 0.65
    return 0.0


def _guess_reset_polarity(name: str) -> tuple[int | None, float]:
    lower = name.lower()
    if lower.endswith("_n") or lower.endswith("n") or lower in {"rst_n", "resetn", "aresetn", "reset_n"}:
        return 0, 0.75
    if lower in {"rst", "reset", "areset"}:
        return 1, 0.45
    return None, 0.2


def _handshake_keyword(name: str) -> str | None:
    lower = name.lower()
    tokens = re.split(r"[^a-z0-9]+", lower)
    for keyword in _HANDSHAKE_KEYWORDS:
        if keyword in tokens or lower.endswith(keyword) or lower.startswith(f"{keyword}_"):
            return keyword
    return None


def _build_handshake_groups(
    ports: list,
    *,
    pattern: str,
    roles: tuple[str, str],
) -> tuple[list[HandshakeGroup], list[str]]:
    buckets: dict[str, dict[str, list[str]]] = defaultdict(lambda: {role: [] for role in roles})
    ambiguities: list[str] = []

    for port in ports:
        for role in roles:
            base = _extract_handshake_base(port.name, role)
            if base is None:
                continue
            buckets[base][role].append(port.name)
            break

    groups: list[HandshakeGroup] = []
    for base, role_map in buckets.items():
        present_roles = [role for role, signal_names in role_map.items() if signal_names]
        if len(present_roles) == len(roles):
            if any(len(role_map[role]) > 1 for role in roles):
                ambiguities.append(
                    f"Multiple candidate signals matched the {pattern} pattern for group '{base}'. Using the first signal per role."
                )
            signals = {role: role_map[role][0] for role in roles}
            groups.append(
                HandshakeGroup(
                    pattern=pattern,
                    group_name=base,
                    signals=signals,
                    source="rtl_heuristic",
                    confidence=0.9 if pattern in {"valid_ready", "req_ack"} else 0.8,
                )
            )
            continue
        if present_roles:
            missing_roles = [role for role in roles if role not in present_roles]
            present_signals = [signal for role in present_roles for signal in role_map[role]]
            ambiguities.append(
                f"Detected {pattern}-like signal(s) {present_signals} without matching role(s) {missing_roles} in group '{base}'."
            )
    return groups, ambiguities


def _extract_handshake_base(name: str, role: str) -> str | None:
    lower = name.lower()
    if lower == role:
        return "default"
    if lower.endswith(f"_{role}"):
        base = lower[: -(len(role) + 1)]
        return base or "default"
    if lower.startswith(f"{role}_"):
        base = lower[len(role) + 1 :]
        return base or "default"
    return None


def _collect_port_names_in_text(line_lower: str, port_lookup: dict[str, str]) -> list[str]:
    matches: list[str] = []
    for lower_name, original_name in port_lookup.items():
        if re.search(rf"(?<![A-Za-z0-9_$]){re.escape(lower_name)}(?![A-Za-z0-9_$])", line_lower):
            matches.append(original_name)
    return matches


def _supports_clock_hint(line_lower: str, port_name: str, port_lookup: dict[str, str]) -> bool:
    clock_confidence = _clock_name_confidence(port_name)
    reset_confidence = _reset_name_confidence(port_name)
    if clock_confidence > reset_confidence:
        return True
    if not _line_explicitly_targets_named_role(line_lower=line_lower, port_name=port_name, role="clock"):
        return False
    mentioned_names = _collect_port_names_in_text(line_lower, port_lookup)
    return len(mentioned_names) == 1 and reset_confidence == 0.0


def _supports_reset_hint(line_lower: str, port_name: str, port_lookup: dict[str, str]) -> bool:
    reset_confidence = _reset_name_confidence(port_name)
    clock_confidence = _clock_name_confidence(port_name)
    if reset_confidence > clock_confidence:
        return True
    if not _line_explicitly_targets_named_role(line_lower=line_lower, port_name=port_name, role="reset"):
        return False
    mentioned_names = _collect_port_names_in_text(line_lower, port_lookup)
    return len(mentioned_names) == 1 and clock_confidence == 0.0


def _line_explicitly_targets_named_role(*, line_lower: str, port_name: str, role: str) -> bool:
    normalized = re.sub(r"\s+", " ", str(line_lower or "").strip().lower())
    signal_lower = port_name.lower()
    role_tokens = {
        "clock": r"(?:clock|clock signal|clk)",
        "reset": r"(?:reset|reset signal|rst)",
    }
    role_pattern = role_tokens.get(role, re.escape(role))
    explicit_patterns = (
        rf"^\s*[-*]?\s*{re.escape(signal_lower)}\s*:\s*.*\b{role_pattern}\b",
        rf"\b{re.escape(signal_lower)}\b\s+(?:is|acts as|serves as|provides)\s+(?:an?\s+)?\b{role_pattern}\b",
    )
    return any(re.search(pattern, normalized) for pattern in explicit_patterns)


def _has_strong_role(items: Iterable[ClockSpec | ResetSpec], name: str, threshold: float = 0.75) -> bool:
    item = _find_by_name(items, name)
    return bool(item and item.confidence >= threshold)


def load_optional_text(path: Path | None) -> str | None:
    """Load an optional text file, returning ``None`` when the path is absent."""
    if path is None:
        return None
    return read_text(path)
