"""Helpers for rendering cocotb environment modules."""

from __future__ import annotations

from pprint import pformat

from cocoverify2.cocotbgen.template_loader import render_template
from cocoverify2.cocotbgen.todo_blocks import build_todo_block
from cocoverify2.core.models import DUTContract, TestPlan
from cocoverify2.core.types import PortDirection
from cocoverify2.utils.numeric_literals import normalize_deterministic_literal
from cocoverify2.utils.semantic_families import infer_grouped_valid_accumulator_family

_ENV_TEMPLATE = "env_module.py.tmpl"


def render_env_module(
    contract: DUTContract,
    plan: TestPlan,
    *,
    temporal_modes_used: list[str],
    interface_module: str,
    coverage_module: str,
    runtime_module: str,
) -> tuple[str, dict[str, object]]:
    """Render the `<dut>_env.py` module content and summary."""
    class_name = f"{_camel(contract.module_name)}Env"
    interface_class = f"{_camel(contract.module_name)}Interface"
    coverage_class = f"{_camel(contract.module_name)}Coverage"
    plan_cases = {
        case.case_id: {
            "goal": case.goal,
            "category": case.category,
            "scenario_kind": getattr(case, "scenario_kind", ""),
            "stimulus_intent": case.stimulus_intent,
            "stimulus_signals": case.stimulus_signals,
            "stimulus_program": getattr(case, "stimulus_program", []),
            "execution_policy": case.execution_policy,
            "defer_reason": case.defer_reason,
            "timing_assumptions": case.timing_assumptions,
            "dependencies": case.dependencies,
            "notes": case.notes,
            "coverage_tags": case.coverage_tags,
            "semantic_tags": case.semantic_tags,
            "deterministic_stimulus_steps": _build_deterministic_stimulus_steps(contract=contract, case=case),
        }
        for case in plan.cases
    }
    unresolved_items = _deduped(contract.ambiguities + plan.unresolved_items)
    helper_comment = "\n".join(f"# - {item}" for item in unresolved_items[:8]) or "# - none"
    wait_methods = ["wait_event_based", "wait_bounded_safe", "wait_unbounded_safe"]
    exact_cycle_block = ""
    exact_cycle_dispatch = ""
    if "exact_cycle" in temporal_modes_used:
        wait_methods.insert(0, "wait_exact_cycle")
        exact_cycle_block = '''
    async def wait_exact_cycle(self, cycles: int, label: str = "exact_cycle") -> None:
        """Wait an exact number of cycles only when the oracle explicitly permits it."""
        clock_name = self.interface.clock_name()
        if clock_name and self.interface.signal_exists(clock_name):
            clock_signal = self.interface.get_signal(clock_name)
            for _ in range(max(1, cycles)):
                await RisingEdge(clock_signal)
        else:
            await Timer(max(1, cycles), unit="ns")
        await ReadOnly()
'''
        exact_cycle_dispatch = (
            '        if mode == "exact_cycle":\n'
            '            await self.wait_exact_cycle(\n'
            '                int(temporal_window.get("max_cycles") or temporal_window.get("min_cycles") or 1),\n'
            '                label=label,\n'
            '            )\n'
            '            return\n'
        )

    business_inputs = _business_inputs(contract)
    business_outputs = _business_outputs(contract)
    signal_widths = {
        port.name: port.width if isinstance(port.width, int) else None
        for port in contract.ports
    }
    clock_specs = [
        {
            "name": clock.name,
            "confidence": clock.confidence,
            "period_ns_guess": float(clock.period_ns_guess) if clock.period_ns_guess else None,
        }
        for clock in contract.clocks
    ]
    stimulus_dispatch_lines: list[str] = []
    stimulus_helper_blocks: list[str] = []
    llm_todo_blocks: list[dict[str, object]] = []
    for case in plan.cases:
        method_name = f"_todo_stimulus_{_sanitize_identifier(case.case_id)}"
        stimulus_dispatch_lines.extend(
            [
                f"        if case_id == {case.case_id!r}:",
                f"            await self.{method_name}()",
                "            return",
            ]
        )
        todo_block, todo_metadata = build_todo_block(
            fill_kind="stimulus",
            block_id=f"stimulus_{case.case_id}",
            template_name=_ENV_TEMPLATE,
            comment_lines=_stimulus_comment_lines(case=case, business_inputs=business_inputs),
            instructions=[
                "Drive concrete legal values onto business inputs for this plan case.",
                "Keep edits inside this TODO block so regeneration stays stable.",
                "Preserve conservative timing assumptions when exact behavior is unclear.",
            ],
            context={
                "business_inputs": list(business_inputs),
                "business_outputs": list(business_outputs),
                "case_id": case.case_id,
                "category": case.category,
                "goal": case.goal,
                "stimulus_intent": list(case.stimulus_intent),
                "stimulus_signals": list(case.stimulus_signals),
                "timing_assumptions": list(case.timing_assumptions),
                "semantic_tags": list(case.semantic_tags),
                "signal_widths": dict(signal_widths),
            },
            indent="        ",
            case_id=case.case_id,
        )
        llm_todo_blocks.append(todo_metadata)
        deterministic_call_lines = [f"        await self._apply_deterministic_case({case.case_id!r})"]
        stimulus_helper_blocks.append(
            "\n".join(
                [
                    f"    async def {method_name}(self) -> None:",
                    f'        """LLM-fill stimulus hook for plan case `{case.case_id}`."""',
                    todo_block,
                    f"        if self.get_case_inputs({case.case_id!r}) or self._last_driven_inputs:",
                    "            return",
                    *deterministic_call_lines,
                ]
            )
        )

    if not stimulus_dispatch_lines:
        stimulus_dispatch_lines.append("        return")

    content = render_template(
        _ENV_TEMPLATE,
        module_name=contract.module_name,
        helper_comment=helper_comment,
        coverage_module=coverage_module,
        coverage_class=coverage_class,
        interface_module=interface_module,
        interface_class=interface_class,
        runtime_module=runtime_module,
        plan_cases_literal=pformat(plan_cases, sort_dicts=True),
        unresolved_items_literal=pformat(unresolved_items),
        signal_widths_literal=pformat(signal_widths, sort_dicts=True),
        clock_specs_literal=pformat(clock_specs, sort_dicts=True),
        business_outputs_literal=pformat(business_outputs),
        class_name=class_name,
        exact_cycle_block=exact_cycle_block,
        exact_cycle_dispatch=exact_cycle_dispatch,
        stimulus_dispatch_block="\n".join(stimulus_dispatch_lines),
        stimulus_helper_blocks=("\n\n".join(stimulus_helper_blocks) + "\n\n") if stimulus_helper_blocks else "",
    )
    summary = {
        "class_name": class_name,
        "wait_helpers": wait_methods,
        "has_reset_helper": bool(contract.resets),
        "case_count": len(plan.cases),
        "unresolved_items": unresolved_items,
        "template_name": _ENV_TEMPLATE,
        "llm_todo_blocks": llm_todo_blocks,
    }
    return content, summary


def _business_inputs(contract: DUTContract) -> list[str]:
    control_signals = set(contract.handshake_signals) | {clock.name for clock in contract.clocks} | {reset.name for reset in contract.resets}
    return [
        port.name
        for port in contract.ports
        if port.direction == PortDirection.INPUT and port.name not in control_signals
    ]


def _business_outputs(contract: DUTContract) -> list[str]:
    control_signals = set(contract.handshake_signals) | {clock.name for clock in contract.clocks} | {reset.name for reset in contract.resets}
    return [
        port.name
        for port in contract.ports
        if port.direction in {PortDirection.OUTPUT, PortDirection.INOUT} and port.name not in control_signals
    ]


def _stimulus_comment_lines(*, case, business_inputs: list[str]) -> list[str]:
    return [
        f"Inputs: {', '.join(business_inputs) if business_inputs else 'none'}",
        f"Stimulus signals: {', '.join(case.stimulus_signals) if getattr(case, 'stimulus_signals', None) else 'none'}",
        f"Goal: {case.goal}",
        "Guidance: Drive concrete legal values onto business inputs here.",
    ]


def _build_deterministic_stimulus_steps(*, contract: DUTContract, case) -> list[dict[str, object]]:
    if getattr(case, "execution_policy", "deterministic") != "deterministic":
        return []

    widths = {
        port.name: port.width if isinstance(port.width, int) else None
        for port in contract.ports
    }
    case_category = str(case.category)
    signal_names = list(getattr(case, "stimulus_signals", []) or [])
    clock_names = {clock.name for clock in contract.clocks}
    reset_names = {reset.name for reset in contract.resets}
    available_step_names = [
        port.name
        for port in contract.ports
        if port.direction == PortDirection.INPUT
        and port.name not in clock_names
    ]
    available_input_names = [name for name in available_step_names if name not in reset_names]

    structured_program = _validate_stimulus_program(
        getattr(case, "stimulus_program", []) or [],
        available_input_names=set(available_step_names),
    )
    steps: list[dict[str, object]] = []
    if _structured_program_is_actionable(
        contract=contract,
        case=case,
        available_input_names=available_input_names,
        steps=structured_program,
    ):
        steps = _ensure_recorded_inputs(structured_program)
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=steps)

    if case_category == "reset":
        return [{"action": "record_inputs", "signals": {"__reset_only__": True}}]

    accumulator_steps = _accumulator_style_steps(contract=contract, case=case, signal_names=available_input_names, widths=widths)
    if accumulator_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=accumulator_steps)

    fifo_steps = _fifo_style_steps(signal_names=available_input_names, widths=widths, case_category=case_category)
    if fifo_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=fifo_steps)

    packing_steps = _packing_pair_steps(signal_names=available_input_names, widths=widths, case_category=case_category)
    if packing_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=packing_steps)

    sequence_steps = _sequence_pattern_steps(contract=contract, signal_names=available_input_names, case_category=case_category)
    if sequence_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=sequence_steps)

    pulse_steps = _pulse_detect_steps(contract=contract, signal_names=available_input_names, case_category=case_category)
    if pulse_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=pulse_steps)

    multiply_steps = _multiply_style_steps(contract=contract, signal_names=available_input_names, widths=widths, case_category=case_category)
    if multiply_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=multiply_steps)

    divide_steps = _divide_style_steps(contract=contract, signal_names=available_input_names, widths=widths, case_category=case_category)
    if divide_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=divide_steps)

    fixed_point_steps = _fixed_point_adder_steps(contract=contract, signal_names=available_input_names, widths=widths, case_category=case_category)
    if fixed_point_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=fixed_point_steps)

    traffic_steps = _traffic_light_steps(contract=contract, signal_names=available_input_names, case_category=case_category)
    if traffic_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=traffic_steps)

    stack_steps = _stack_buffer_steps(signal_names=available_input_names, widths=widths, case_category=case_category)
    if stack_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=stack_steps)

    serial_steps = _serial_parallel_steps(signal_names=available_input_names, case_category=case_category)
    if serial_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=serial_steps)

    memory_steps = _memory_style_steps(signal_names=signal_names, widths=widths)
    if memory_steps:
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=memory_steps)

    if case_category == "protocol":
        protocol_steps = _protocol_style_steps(signal_names=signal_names, widths=widths, case=case)
        if protocol_steps:
            return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=protocol_steps)

    if case_category == "back_to_back" and signal_names:
        first = _deterministic_drive_pattern(signal_names=signal_names, widths=widths, profile="basic")
        second = _deterministic_drive_pattern(signal_names=signal_names, widths=widths, profile="edge")
        steps = [
            {"action": "drive", "signals": first},
            {"action": "wait_cycles", "cycles": 1},
            {"action": "drive", "signals": second},
            {"action": "wait_cycles", "cycles": 1},
        ]
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=steps)

    if signal_names:
        profile = "edge" if case_category == "edge" else "basic"
        steps = _ensure_recorded_inputs([
            {"action": "drive", "signals": _deterministic_drive_pattern(signal_names=signal_names, widths=widths, profile=profile)},
            {"action": "wait_cycles" if contract.timing.sequential_kind == "seq" and contract.clocks else "wait_for_settle"},
        ])
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=steps)

    if contract.timing.sequential_kind == "seq" and contract.clocks:
        steps = [
            {
                "action": "record_note",
                "text": "Deterministic mainline case relies on clock-driven observation because no non-control inputs were resolved.",
            },
            {"action": "wait_cycles", "cycles": 2},
            {"action": "record_inputs", "signals": {"__clock_progress__": 2}},
        ]
        return _finalize_deterministic_stimulus_steps(contract=contract, case=case, steps=steps)

    return []


def _validate_stimulus_program(
    steps: list[dict[str, object]],
    *,
    available_input_names: set[str],
) -> list[dict[str, object]]:
    if not isinstance(steps, list):
        return []
    normalized: list[dict[str, object]] = []
    for step in steps:
        if not isinstance(step, dict):
            continue
        action = str(step.get("action") or "").strip()
        if action == "drive":
            raw_signals = step.get("signals")
            if not isinstance(raw_signals, dict):
                continue
            filtered_signals: dict[str, object] = {}
            for signal_name, signal_value in raw_signals.items():
                normalized_name = str(signal_name or "").strip()
                if normalized_name not in available_input_names:
                    continue
                try:
                    filtered_signals[normalized_name] = normalize_deterministic_literal(signal_value)
                except ValueError:
                    continue
            if not filtered_signals:
                continue
            normalized.append({"action": "drive", "signals": filtered_signals})
            continue
        if action == "wait_for_settle":
            normalized.append({"action": "wait_for_settle"})
            continue
        if action == "wait_cycles":
            try:
                cycles = int(step.get("cycles") or 1)
            except (TypeError, ValueError):
                cycles = 1
            normalized.append({"action": "wait_cycles", "cycles": max(1, cycles)})
            continue
        if action == "record_inputs":
            raw_signals = step.get("signals")
            if isinstance(raw_signals, dict) and raw_signals:
                filtered_signals: dict[str, object] = {}
                for signal_name, signal_value in raw_signals.items():
                    normalized_name = str(signal_name or "").strip()
                    if normalized_name not in available_input_names:
                        continue
                    try:
                        filtered_signals[normalized_name] = normalize_deterministic_literal(signal_value)
                    except ValueError:
                        continue
                if filtered_signals:
                    normalized.append({"action": "record_inputs", "signals": filtered_signals})
            continue
        if action == "record_note":
            text = str(step.get("text") or "").strip()
            if text:
                normalized.append({"action": "record_note", "text": text})
            continue
    return normalized


def _has_executable_drive_step(steps: list[dict[str, object]]) -> bool:
    return any(
        step.get("action") in {"drive", "record_inputs"}
        and isinstance(step.get("signals"), dict)
        and bool(step.get("signals"))
        for step in steps
    )


def _structured_program_is_actionable(
    *,
    contract: DUTContract,
    case,
    available_input_names: list[str],
    steps: list[dict[str, object]],
) -> bool:
    if not _has_executable_drive_step(steps):
        return False

    lowered = {name.lower(): name for name in available_input_names}
    drive_steps = [step for step in steps if step.get("action") == "drive" and isinstance(step.get("signals"), dict)]

    if {"din_serial", "din_valid"}.issubset(lowered):
        valid_name = lowered["din_valid"]
        serial_name = lowered["din_serial"]
        valid_drives = [
            step for step in drive_steps
            if int(bool(step["signals"].get(valid_name, 0))) == 1 and serial_name in step["signals"]
        ]
        return len(valid_drives) >= 8

    if {"data_in", "valid_in"}.issubset(lowered):
        valid_name = lowered["valid_in"]
        data_name = lowered["data_in"]
        valid_drives = [
            step for step in drive_steps
            if int(bool(step["signals"].get(valid_name, 0))) == 1 and data_name in step["signals"]
        ]
        accumulator_family = infer_grouped_valid_accumulator_family(
            contract,
            additional_texts=_case_semantic_texts(case),
        )
        if accumulator_family is not None:
            group_size = int(accumulator_family["group_size"])
            transition = str(getattr(case, "expected_transition", "") or "").lower()
            minimum_valids = 1
            if "multi_group" in transition:
                minimum_valids = group_size * 2
            elif "single_group" in transition or str(getattr(case, "scenario_kind", "") or "") in {
                "grouped_valid_closure",
                "gapped_valid_group",
                "reset_mid_progress",
            }:
                minimum_valids = group_size
            elif str(case.category) in {"edge", "back_to_back", "protocol", "regression"}:
                minimum_valids = group_size
            if len(valid_drives) < minimum_valids:
                return False
            return _has_explicit_tail_cleanup(drive_steps, valid_name)
        return len(valid_drives) >= 2 and _has_explicit_tail_cleanup(drive_steps, valid_name)

    if {"winc", "rinc", "wdata"}.issubset(lowered):
        write_name = lowered["winc"]
        read_name = lowered["rinc"]
        saw_write = any(int(bool(step["signals"].get(write_name, 0))) == 1 for step in drive_steps)
        saw_read = any(int(bool(step["signals"].get(read_name, 0))) == 1 for step in drive_steps)
        return saw_write and saw_read

    if _looks_like_sequence_detector(contract) and "data_in" in lowered:
        data_name = lowered["data_in"]
        return sum(1 for step in drive_steps if data_name in step["signals"]) >= 4

    if _looks_like_pulse_detector(contract) and "data_in" in lowered:
        data_name = lowered["data_in"]
        return sum(1 for step in drive_steps if data_name in step["signals"]) >= 3

    return True


def _ensure_recorded_inputs(steps: list[dict[str, object]]) -> list[dict[str, object]]:
    has_record_inputs = any(step.get("action") == "record_inputs" for step in steps)
    if has_record_inputs:
        return steps
    last_drive_signals: dict[str, object] = {}
    for step in steps:
        if step.get("action") == "drive":
            raw_signals = step.get("signals")
            if isinstance(raw_signals, dict):
                last_drive_signals = dict(raw_signals)
    if last_drive_signals:
        return [*steps, {"action": "record_inputs", "signals": last_drive_signals}]
    return steps


def _finalize_deterministic_stimulus_steps(
    *,
    contract: DUTContract,
    case,
    steps: list[dict[str, object]],
) -> list[dict[str, object]]:
    finalized = _append_end_of_case_quiesce(contract=contract, case=case, steps=list(steps))
    return _ensure_recorded_inputs(finalized)


def _append_end_of_case_quiesce(
    *,
    contract: DUTContract,
    case,
    steps: list[dict[str, object]],
) -> list[dict[str, object]]:
    if not steps:
        return steps
    last_drive = _last_drive_signals(steps)
    if not last_drive:
        return steps
    quiesce: dict[str, object] = {}
    for signal_name in _quiesce_signal_names(contract=contract, case=case, driven_signals=last_drive):
        if int(bool(last_drive.get(signal_name, 0))) == 1:
            quiesce[signal_name] = 0
    if not quiesce:
        return steps
    finalized = list(steps)
    finalized.append({"action": "drive", "signals": quiesce})
    finalized.append({"action": "wait_cycles", "cycles": 1})
    return finalized


def _last_drive_signals(steps: list[dict[str, object]]) -> dict[str, object]:
    last_drive: dict[str, object] = {}
    for step in steps:
        if step.get("action") != "drive":
            continue
        signals = step.get("signals")
        if isinstance(signals, dict):
            last_drive = dict(signals)
    return last_drive


def _quiesce_signal_names(*, contract: DUTContract, case, driven_signals: dict[str, object]) -> list[str]:
    lowered = {name.lower(): name for name in driven_signals}
    case_text = " ".join(str(item) for item in _case_semantic_texts(case)).lower()
    result: list[str] = []
    for lower_name, original_name in lowered.items():
        if lower_name in {"valid", "valid_in", "din_valid", "winc", "rinc", "start", "opn_valid", "pass_request"}:
            result.append(original_name)
            continue
        if any(token in lower_name for token in ("valid", "enable", "_en", "start", "req", "inc", "load")):
            result.append(original_name)
    if infer_grouped_valid_accumulator_family(contract, additional_texts=[case_text]) is not None and "valid_in" in lowered:
        result.append(lowered["valid_in"])
    return sorted(set(result))


def _case_semantic_texts(case) -> list[str]:
    return [
        getattr(case, "goal", ""),
        str(getattr(case, "scenario_kind", "") or ""),
        *list(getattr(case, "stimulus_intent", []) or []),
        *list(getattr(case, "expected_properties", []) or []),
        *list(getattr(case, "assumptions", []) or []),
        *list(getattr(case, "notes", []) or []),
        str(getattr(case, "reference_domain", "") or ""),
        str(getattr(case, "expected_transition", "") or ""),
    ]


def _has_explicit_tail_cleanup(drive_steps: list[dict[str, object]], signal_name: str) -> bool:
    for step in reversed(drive_steps):
        signals = step.get("signals", {})
        if signal_name in signals:
            return int(bool(signals.get(signal_name, 0))) == 0
    return True


def _accumulator_style_steps(
    *,
    contract: DUTContract,
    case,
    signal_names: list[str],
    widths: dict[str, int | None],
) -> list[dict[str, object]]:
    family = infer_grouped_valid_accumulator_family(
        contract,
        additional_texts=_case_semantic_texts(case),
    )
    if family is None:
        return []
    lowered = {name.lower(): name for name in signal_names}
    if not {"data_in", "valid_in"}.issubset(lowered):
        return []
    data_in = lowered["data_in"]
    valid_in = lowered["valid_in"]
    group_size = int(family["group_size"])
    data_mask = _mask_from_width(widths.get(data_in))
    case_category = str(case.category)
    transition = str(getattr(case, "expected_transition", "") or "").lower()
    scenario_kind = str(getattr(case, "scenario_kind", "") or "")

    if "multi_group" in transition or scenario_kind == "multi_group_stream":
        values = [index & data_mask for index in range(1, group_size + 1)] + [index & data_mask for index in range(10, 10 + group_size)]
        return _accumulator_group_program(valid_in=valid_in, data_in=data_in, values=values)
    if "gapped" in transition or scenario_kind == "gapped_valid_group" or case_category == "protocol":
        values = [index & data_mask for index in range(1, group_size + 1)]
        return _accumulator_gapped_program(valid_in=valid_in, data_in=data_in, values=values)
    if case_category == "edge":
        return _accumulator_group_program(valid_in=valid_in, data_in=data_in, values=[data_mask] * group_size)
    if case_category == "back_to_back":
        values = [index & data_mask for index in range(1, group_size + 1)] + [index & data_mask for index in range(group_size + 1, 2 * group_size + 1)]
        return _accumulator_group_program(valid_in=valid_in, data_in=data_in, values=values)
    if case_category == "negative":
        return [
            {"action": "drive", "signals": {valid_in: 0, data_in: (0xAA & data_mask)}},
            {"action": "wait_cycles", "cycles": 2},
            {"action": "drive", "signals": {valid_in: 0, data_in: (0x55 & data_mask)}},
            {"action": "wait_cycles", "cycles": 1},
        ]
    return [
        {"action": "drive", "signals": {valid_in: 1, data_in: 1 & data_mask}},
        {"action": "wait_cycles", "cycles": 1},
        {"action": "drive", "signals": {valid_in: 0, data_in: 1 & data_mask}},
        {"action": "wait_cycles", "cycles": 1},
    ]


def _fifo_style_steps(
    *,
    signal_names: list[str],
    widths: dict[str, int | None],
    case_category: str,
) -> list[dict[str, object]]:
    lowered = {name.lower(): name for name in signal_names}
    required = {"winc", "rinc", "wdata"}
    if not required.issubset(lowered):
        return []
    winc = lowered["winc"]
    rinc = lowered["rinc"]
    wdata = lowered["wdata"]
    data_basic = 0xA5 & _mask_from_width(widths.get(wdata))
    data_edge = _mask_from_width(widths.get(wdata))
    write_value = data_edge if case_category == "edge" else data_basic
    return [
        {"action": "drive", "signals": {winc: 1, rinc: 0, wdata: write_value}},
        {"action": "wait_cycles", "cycles": 2},
        {"action": "drive", "signals": {winc: 0, rinc: 0, wdata: write_value}},
        {"action": "wait_cycles", "cycles": 1},
        {"action": "drive", "signals": {winc: 0, rinc: 1, wdata: write_value}},
        {"action": "wait_cycles", "cycles": 2},
    ]


def _memory_style_steps(*, signal_names: list[str], widths: dict[str, int | None]) -> list[dict[str, object]]:
    lowered = {name.lower(): name for name in signal_names}
    required = {"write_en", "read_en", "write_addr", "write_data", "read_addr"}
    if not required.issubset(lowered):
        return []
    write_en = lowered["write_en"]
    read_en = lowered["read_en"]
    write_addr = lowered["write_addr"]
    write_data = lowered["write_data"]
    read_addr = lowered["read_addr"]
    return [
        {
            "action": "drive",
            "signals": {
                write_en: 1,
                read_en: 0,
                write_addr: 3 & _mask_from_width(widths.get(write_addr)),
                write_data: 0x15 & _mask_from_width(widths.get(write_data)),
                read_addr: 3 & _mask_from_width(widths.get(read_addr)),
            },
        },
        {"action": "wait_cycles", "cycles": 1},
        {
            "action": "drive",
            "signals": {
                write_en: 0,
                read_en: 1,
                write_addr: 3 & _mask_from_width(widths.get(write_addr)),
                write_data: 0x15 & _mask_from_width(widths.get(write_data)),
                read_addr: 3 & _mask_from_width(widths.get(read_addr)),
            },
        },
        {"action": "wait_cycles", "cycles": 1},
    ]


def _accumulator_group_program(*, valid_in: str, data_in: str, values: list[int]) -> list[dict[str, object]]:
    steps: list[dict[str, object]] = []
    for value in values:
        steps.append({"action": "drive", "signals": {valid_in: 1, data_in: int(value)}})
        steps.append({"action": "wait_cycles", "cycles": 1})
    final_value = int(values[-1]) if values else 0
    steps.append({"action": "drive", "signals": {valid_in: 0, data_in: final_value}})
    steps.append({"action": "wait_cycles", "cycles": 1})
    return steps


def _accumulator_gapped_program(*, valid_in: str, data_in: str, values: list[int]) -> list[dict[str, object]]:
    steps: list[dict[str, object]] = []
    for index, value in enumerate(values):
        steps.append({"action": "drive", "signals": {valid_in: 1, data_in: int(value)}})
        steps.append({"action": "wait_cycles", "cycles": 1})
        if index < len(values) - 1:
            steps.append({"action": "drive", "signals": {valid_in: 0, data_in: int(value)}})
            steps.append({"action": "wait_cycles", "cycles": 1})
    final_value = int(values[-1]) if values else 0
    steps.append({"action": "drive", "signals": {valid_in: 0, data_in: final_value}})
    steps.append({"action": "wait_cycles", "cycles": 1})
    return steps


def _packing_pair_steps(
    *,
    signal_names: list[str],
    widths: dict[str, int | None],
    case_category: str,
) -> list[dict[str, object]]:
    lowered = {name.lower(): name for name in signal_names}
    required = {"valid_in", "data_in"}
    if not required.issubset(lowered):
        return []
    valid_in = lowered["valid_in"]
    data_in = lowered["data_in"]
    first = 0x12 & _mask_from_width(widths.get(data_in))
    second = 0x34 & _mask_from_width(widths.get(data_in))
    if case_category == "edge":
        first = _mask_from_width(widths.get(data_in))
        second = 0
    return [
        {"action": "drive", "signals": {valid_in: 1, data_in: first}},
        {"action": "wait_cycles", "cycles": 1},
        {"action": "drive", "signals": {valid_in: 1, data_in: second}},
        {"action": "wait_cycles", "cycles": 1},
        {"action": "drive", "signals": {valid_in: 0, data_in: second}},
        {"action": "wait_cycles", "cycles": 1},
    ]


def _stack_buffer_steps(
    *,
    signal_names: list[str],
    widths: dict[str, int | None],
    case_category: str,
) -> list[dict[str, object]]:
    lowered = {name.lower(): name for name in signal_names}
    required = {"datain", "rw", "en"}
    if not required.issubset(lowered):
        return []
    data_in = lowered["datain"]
    read_write = lowered["rw"]
    enable = lowered["en"]
    basic_value = 0x1 & _mask_from_width(widths.get(data_in))
    edge_value = _mask_from_width(widths.get(data_in))

    if case_category == "back_to_back":
        return [
            {"action": "drive", "signals": {enable: 1, read_write: 0, data_in: basic_value}},
            {"action": "wait_cycles", "cycles": 1},
            {"action": "drive", "signals": {enable: 1, read_write: 0, data_in: edge_value}},
            {"action": "wait_cycles", "cycles": 1},
            {"action": "drive", "signals": {enable: 1, read_write: 1, data_in: edge_value}},
            {"action": "wait_cycles", "cycles": 1},
        ]

    drive_value = edge_value if case_category == "edge" else basic_value
    return [
        {"action": "drive", "signals": {enable: 1, read_write: 0, data_in: drive_value}},
        {"action": "wait_cycles", "cycles": 1},
        {"action": "drive", "signals": {enable: 1, read_write: 1, data_in: drive_value}},
        {"action": "wait_cycles", "cycles": 1},
    ]


def _serial_parallel_steps(*, signal_names: list[str], case_category: str) -> list[dict[str, object]]:
    lowered = {name.lower(): name for name in signal_names}
    required = {"din_serial", "din_valid"}
    if not required.issubset(lowered):
        return []
    din_serial = lowered["din_serial"]
    din_valid = lowered["din_valid"]
    pattern = [1, 0, 1, 0, 1, 0, 1, 0]
    if case_category == "edge":
        pattern = [1] * 8
    steps: list[dict[str, object]] = []
    for bit in pattern:
        steps.append({"action": "drive", "signals": {din_serial: bit, din_valid: 1}})
        steps.append({"action": "wait_cycles", "cycles": 1})
    steps.append({"action": "drive", "signals": {din_serial: pattern[-1], din_valid: 0}})
    steps.append({"action": "wait_cycles", "cycles": 1})
    return steps


def _sequence_pattern_steps(*, contract: DUTContract, signal_names: list[str], case_category: str) -> list[dict[str, object]]:
    lowered = {name.lower(): name for name in signal_names}
    if "data_in" not in lowered or not _looks_like_sequence_detector(contract):
        return []
    data_in = lowered["data_in"]
    pattern = [1, 0, 0, 1]
    if case_category == "edge":
        pattern = [1, 0, 0, 1, 0]
    steps: list[dict[str, object]] = []
    for bit in pattern:
        steps.append({"action": "drive", "signals": {data_in: bit}})
        steps.append({"action": "wait_cycles", "cycles": 1})
    return steps


def _pulse_detect_steps(*, contract: DUTContract, signal_names: list[str], case_category: str) -> list[dict[str, object]]:
    lowered = {name.lower(): name for name in signal_names}
    if "data_in" not in lowered or not _looks_like_pulse_detector(contract):
        return []
    data_in = lowered["data_in"]
    pattern = [0, 1, 0]
    if case_category == "edge":
        pattern = [0, 1, 0, 0]
    steps: list[dict[str, object]] = []
    for bit in pattern:
        steps.append({"action": "drive", "signals": {data_in: bit}})
        steps.append({"action": "wait_cycles", "cycles": 1})
    return steps


def _multiply_style_steps(
    *,
    contract: DUTContract,
    signal_names: list[str],
    widths: dict[str, int | None],
    case_category: str,
) -> list[dict[str, object]]:
    lowered = {name.lower(): name for name in signal_names}
    required = {"mul_a", "mul_b"}
    if not required.issubset(lowered):
        return []
    mul_a = lowered["mul_a"]
    mul_b = lowered["mul_b"]
    enable_name = lowered.get("mul_en_in")
    first = 13 & _mask_from_width(widths.get(mul_a))
    second = 11 & _mask_from_width(widths.get(mul_b))
    if case_category == "edge":
        first = _mask_from_width(widths.get(mul_a)) >> 1
        second = 3 & _mask_from_width(widths.get(mul_b))
    drive = {mul_a: first, mul_b: second}
    if enable_name:
        drive[enable_name] = 1
    settle = {mul_a: first, mul_b: second}
    if enable_name:
        settle[enable_name] = 0
    return [
        {"action": "drive", "signals": drive},
        {"action": "wait_cycles", "cycles": 4 if contract.timing.sequential_kind == "seq" else 1},
        {"action": "drive", "signals": settle},
        {"action": "wait_cycles", "cycles": 1},
    ]


def _divide_style_steps(
    *,
    contract: DUTContract,
    signal_names: list[str],
    widths: dict[str, int | None],
    case_category: str,
) -> list[dict[str, object]]:
    lowered = {name.lower(): name for name in signal_names}
    required = {"a", "b"}
    if not required.issubset(lowered):
        return []
    if contract.module_name.lower() != "div_16bit":
        return []
    dividend = lowered["a"]
    divisor = lowered["b"]
    a_value = 0x00C8 & _mask_from_width(widths.get(dividend))
    b_value = 0x0A & _mask_from_width(widths.get(divisor))
    if case_category == "edge":
        a_value = 0x1234 & _mask_from_width(widths.get(dividend))
        b_value = 0x13 & _mask_from_width(widths.get(divisor))
    return _ensure_recorded_inputs(
        [
            {"action": "drive", "signals": {dividend: a_value, divisor: b_value}},
            {"action": "wait_for_settle"},
        ]
    )


def _fixed_point_adder_steps(
    *,
    contract: DUTContract,
    signal_names: list[str],
    widths: dict[str, int | None],
    case_category: str,
) -> list[dict[str, object]]:
    lowered = {name.lower(): name for name in signal_names}
    required = {"a", "b"}
    if not required.issubset(lowered):
        return []
    if contract.module_name.lower() != "fixed_point_adder":
        return []
    a_name = lowered["a"]
    b_name = lowered["b"]
    width = max(2, int(widths.get(a_name) or widths.get(b_name) or 16))
    magnitude_mask = (1 << (width - 1)) - 1
    pos_three = 3 & magnitude_mask
    neg_one = (1 << (width - 1)) | (1 & magnitude_mask)
    pos_two = 2 & magnitude_mask
    neg_two = (1 << (width - 1)) | (2 & magnitude_mask)
    if case_category == "edge":
        drive = {a_name: pos_two, b_name: neg_two}
    else:
        drive = {a_name: pos_three, b_name: neg_one}
    return _ensure_recorded_inputs([{"action": "drive", "signals": drive}, {"action": "wait_for_settle"}])


def _traffic_light_steps(*, contract: DUTContract, signal_names: list[str], case_category: str) -> list[dict[str, object]]:
    lowered = {name.lower(): name for name in signal_names}
    if "pass_request" not in lowered:
        return []
    if not {"red", "yellow", "green"}.issubset({name.lower() for name in contract.observable_outputs}):
        return []
    pass_request = lowered["pass_request"]
    wait_before = 3 if case_category == "edge" else 6
    return [
        {"action": "drive", "signals": {pass_request: 0}},
        {"action": "wait_cycles", "cycles": wait_before},
        {"action": "drive", "signals": {pass_request: 1}},
        {"action": "wait_cycles", "cycles": 4},
        {"action": "drive", "signals": {pass_request: 0}},
        {"action": "wait_cycles", "cycles": 2},
    ]


def _protocol_style_steps(*, signal_names: list[str], widths: dict[str, int | None], case) -> list[dict[str, object]]:
    signals = {name.lower(): name for name in signal_names}
    if not signals:
        return []
    drive = _deterministic_drive_pattern(signal_names=signal_names, widths=widths, profile="basic")
    coverage_tags = {str(tag).lower() for tag in getattr(case, "coverage_tags", [])}
    if "backpressure" in coverage_tags:
        for lower_name, original_name in signals.items():
            if "ready" in lower_name:
                drive[original_name] = 0
            elif any(token in lower_name for token in ("valid", "start", "req")):
                drive[original_name] = 1
        return [{"action": "drive", "signals": drive}, {"action": "wait_cycles", "cycles": 1}]
    if "persistence" in coverage_tags:
        initial = dict(drive)
        follow_up = dict(drive)
        for lower_name, original_name in signals.items():
            if "ready" in lower_name:
                initial[original_name] = 0
                follow_up[original_name] = 1
            elif any(token in lower_name for token in ("valid", "start", "req")):
                initial[original_name] = 1
                follow_up[original_name] = 1
        return [
            {"action": "drive", "signals": initial},
            {"action": "wait_cycles", "cycles": 1},
            {"action": "drive", "signals": follow_up},
            {"action": "wait_cycles", "cycles": 1},
        ]
    for lower_name, original_name in signals.items():
        if any(token in lower_name for token in ("valid", "ready", "start", "req", "ack", "done")):
            drive[original_name] = 1
    return [{"action": "drive", "signals": drive}, {"action": "wait_cycles", "cycles": 1}]


def _deterministic_drive_pattern(*, signal_names: list[str], widths: dict[str, int | None], profile: str) -> dict[str, int]:
    values: dict[str, int] = {}
    for index, signal_name in enumerate(signal_names):
        width = widths.get(signal_name)
        mask = _mask_from_width(width)
        lower = signal_name.lower()
        if any(token in lower for token in ("enable", "_en", "valid", "ready", "start", "write", "read", "req", "ack", "load")) or lower in {"en", "ce", "we", "re"}:
            value = 1
        elif _is_control_like_signal_name(lower):
            value = 0
        elif profile == "edge":
            value = mask
        elif width is not None and width > 1:
            value = (index + 1) & mask
        else:
            value = index % 2
        values[signal_name] = value & mask
    return values


def _mask_from_width(width: int | None) -> int:
    width_int = max(1, int(width or 1))
    return (1 << width_int) - 1


def _is_control_like_signal_name(lower_name: str) -> bool:
    normalized = lower_name.replace("[", "_").replace("]", "_")
    tokens = [token for token in normalized.replace("__", "_").split("_") if token]
    if lower_name in {"aluc", "opcode", "op", "sel", "mode", "cmd", "ctrl", "control"}:
        return True
    return any(token in {"opcode", "op", "func", "sel", "mode", "cmd", "ctrl", "control"} for token in tokens)


def _looks_like_sequence_detector(contract: DUTContract) -> bool:
    module_name = contract.module_name.lower()
    outputs = {name.lower() for name in contract.observable_outputs}
    return "sequence" in module_name or "sequence_detected" in outputs


def _looks_like_pulse_detector(contract: DUTContract) -> bool:
    module_name = contract.module_name.lower()
    return "pulse_detect" in module_name or module_name.endswith("pulse")


def _camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_")) or "Rendered"


def _deduped(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items


def _sanitize_identifier(name: str) -> str:
    sanitized = "".join(char if char.isalnum() or char == "_" else "_" for char in name)
    if sanitized and sanitized[0].isdigit():
        return f"case_{sanitized}"
    return sanitized or "rendered_case"
