"""Helpers for recognizing small, reusable semantic verification families."""

from __future__ import annotations

import re
from typing import Any, Iterable

from cocoverify2.core.models import DUTContract, PortSpec
from cocoverify2.core.types import PortDirection, SequentialKind

_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
}
_GROUP_PATTERNS = (
    re.compile(
        r"\b(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\b"
        r"(?:\s+\w+){0,4}\s+\b(?:valid|accepted|received|input|inputs|sample|samples|word|words)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bafter\b(?:\s+\w+){0,3}\s+\b(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\bevery\b(?:\s+\w+){0,2}\s+\b(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\b"
        r"(?:\s+\w+){0,5}\s+\b(?:accepted|received|valid|input|sample|samples)\b"
        r"(?:\s+\w+){0,3}\s+\b(?:accumulation|group|groups|closure|output)\b",
        re.IGNORECASE,
    ),
)
_ACCUM_HINT_RE = re.compile(r"\b(accu|accumulator|accumulation|sum|summing|accumulate)\b", re.IGNORECASE)
_SERIAL_HINT_RE = re.compile(r"\b(serial|seriali[sz](?:e|er)|deseriali[sz](?:e|er)|bitstream|bit stream|bit-serial|shift)\b", re.IGNORECASE)
_PARALLEL_HINT_RE = re.compile(r"\b(parallel|byte|word|packed|pack|deseriali[sz](?:e|er)|conversion)\b", re.IGNORECASE)
_FIFO_HINT_RE = re.compile(r"\b(fifo|queue|buffer|stream buffer|asynchronous fifo|async fifo|readback)\b", re.IGNORECASE)
_RING_HINT_RE = re.compile(r"\b(ring|rotate|rotation|one[- ]hot|circulat)\b", re.IGNORECASE)
_TRAFFIC_HINT_RE = re.compile(r"\b(traffic|light|phase|pedestrian|request)\b", re.IGNORECASE)
_MULTIPLY_HINT_RE = re.compile(r"\b(mult|multiply|product|multiplier)\b", re.IGNORECASE)
_SIGNED_MULTIPLY_HINT_RE = re.compile(r"\b(signed|sign[- ]extend(?:ed)?|two'?s complement|booth|radix[- ]?4)\b", re.IGNORECASE)
_FIXED_POINT_HINT_RE = re.compile(r"\b(fixed[_ ]point|q\d+|fractional)\b", re.IGNORECASE)
_DIVIDE_HINT_RE = re.compile(r"\b(div|divide|division|divisor|quotient|remainder)\b", re.IGNORECASE)
_SEQUENCE_HINT_RE = re.compile(r"\b(sequence|pattern|detect|detector|pulse)\b", re.IGNORECASE)
_BIT_PATTERN_RE = re.compile(r"\b[01]{2,16}\b")

_VALID_INPUT_TOKENS = {
    "accept",
    "accepted",
    "ce",
    "enable",
    "enabled",
    "en",
    "gate",
    "go",
    "load",
    "push",
    "req",
    "sample",
    "start",
    "strobe",
    "vld",
    "valid",
    "write",
}
_COMPLETION_OUTPUT_TOKENS = {
    "ack",
    "complete",
    "completion",
    "done",
    "match",
    "pulse",
    "ready",
    "rdy",
    "valid",
    "vld",
}
_READ_TOKENS = {"pop", "read", "rd", "recv", "receive", "rinc"}
_WRITE_TOKENS = {"push", "send", "transmit", "winc", "write", "wr"}
_DATA_TOKENS = {"byte", "count", "data", "din", "dout", "input", "out", "output", "payload", "result", "sample", "sum", "value", "word"}
_SERIAL_TOKENS = {"bit", "din", "serial", "shift"}
_PARALLEL_TOKENS = {"byte", "dout", "out", "parallel", "word"}
_CLOCK_LIKE_TOKENS = {"clk", "clock"}
_RESET_LIKE_TOKENS = {"reset", "rst", "rstn", "rst_n", "resetn"}


def infer_grouped_valid_accumulator_family(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    """Return grouped-valid accumulator metadata when the contract strongly hints it."""
    if contract.timing.sequential_kind != SequentialKind.SEQ:
        return None

    evidence = _semantic_evidence_text(
        contract,
        task_description=task_description,
        spec_text=spec_text,
        additional_texts=additional_texts,
    )
    if not evidence or not _ACCUM_HINT_RE.search(evidence):
        return None
    if _MULTIPLY_HINT_RE.search(evidence) or _DIVIDE_HINT_RE.search(evidence):
        return None

    group_size = infer_group_size(evidence)
    if group_size is None or group_size < 2:
        return None

    gate_input = _select_stream_gate_input(contract, evidence_text=evidence)
    completion_output = _select_completion_output(contract, evidence_text=evidence)
    if gate_input is None or completion_output is None:
        return None

    candidate_data_inputs = [
        port
        for port in _non_control_input_ports(contract)
        if port.name != gate_input.name and (_port_width_int(port) or 0) > 1
    ]
    if len(candidate_data_inputs) != 1:
        return None

    data_input = _select_primary_data_input(contract, exclude_names={gate_input.name}, evidence_text=evidence)
    data_output = _select_primary_data_output(
        contract,
        exclude_names={completion_output.name},
        min_width=_port_width_int(data_input),
        evidence_text=evidence,
    )
    if data_input is None or data_output is None:
        return None

    data_in_width = _port_width_int(data_input)
    data_out_width = _port_width_int(data_output)
    if data_in_width is not None and data_out_width is not None and data_out_width < data_in_width:
        return None

    reset_name = contract.resets[0].name if contract.resets else ""
    reset_active_level = contract.resets[0].active_level if contract.resets else None
    return {
        "input_data_signal": data_input.name,
        "input_gate_signal": gate_input.name,
        "output_data_signal": data_output.name,
        "output_gate_signal": completion_output.name,
        "data_in": data_input.name,
        "valid_in": gate_input.name,
        "data_out": data_output.name,
        "valid_out": completion_output.name,
        "group_size": group_size,
        "data_width": data_in_width,
        "output_width": data_out_width,
        "reset_name": reset_name,
        "reset_active_level": reset_active_level,
        "evidence_text": evidence,
    }


def infer_serial_to_parallel_family(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    """Infer a serial-input to parallel-output stream conversion family."""
    if contract.timing.sequential_kind != SequentialKind.SEQ:
        return None
    evidence = _semantic_evidence_text(
        contract,
        task_description=task_description,
        spec_text=spec_text,
        additional_texts=additional_texts,
    )
    lowered = evidence.lower()
    if not (_SERIAL_HINT_RE.search(evidence) and _PARALLEL_HINT_RE.search(evidence)):
        return None

    gate_input = _select_stream_gate_input(contract, evidence_text=evidence)
    if gate_input is None:
        return None
    serial_input = _select_serial_input(contract, exclude_names={gate_input.name}, evidence_text=evidence)
    parallel_output = _select_primary_data_output(contract, exclude_names=set(), min_width=2, evidence_text=evidence, prefer_parallel=True)
    completion_output = _select_completion_output(contract, evidence_text=evidence)
    if serial_input is None or parallel_output is None or completion_output is None:
        return None

    bit_count = _port_width_int(parallel_output)
    if bit_count is None or bit_count < 2:
        return None
    bit_order = "either"
    if "msb" in lowered or "high bit first" in lowered:
        bit_order = "msb_to_lsb"
    elif "lsb" in lowered or "low bit first" in lowered:
        bit_order = "lsb_to_msb"

    return {
        "serial_input_signal": serial_input.name,
        "input_gate_signal": gate_input.name,
        "parallel_output_signal": parallel_output.name,
        "output_gate_signal": completion_output.name,
        "bit_count": bit_count,
        "bit_order": bit_order,
        "evidence_text": evidence,
    }


def infer_packed_stream_conversion_family(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    """Infer a gated stream-to-packed-output conversion family."""
    if contract.timing.sequential_kind != SequentialKind.SEQ:
        return None
    evidence = _semantic_evidence_text(
        contract,
        task_description=task_description,
        spec_text=spec_text,
        additional_texts=additional_texts,
    )
    lowered = evidence.lower()
    if not _PARALLEL_HINT_RE.search(evidence):
        return None

    gate_input = _select_stream_gate_input(contract, evidence_text=evidence)
    completion_output = _select_completion_output(contract, evidence_text=evidence)
    if gate_input is None or completion_output is None:
        return None

    data_input = _select_primary_data_input(contract, exclude_names={gate_input.name}, evidence_text=evidence)
    data_output = _select_primary_data_output(
        contract,
        exclude_names={completion_output.name},
        min_width=max(2, (_port_width_int(data_input) or 0) + 1) if data_input is not None else 2,
        evidence_text=evidence,
        prefer_parallel=True,
    )
    if data_input is None or data_output is None:
        return None

    input_width = _port_width_int(data_input)
    output_width = _port_width_int(data_output)
    if input_width is None or output_width is None or output_width <= input_width:
        return None
    ratio = output_width / input_width
    if ratio < 2 or int(ratio) != ratio:
        return None

    pack_order = "either"
    if "high byte first" in lowered or "first byte in the high bits" in lowered or "msb first" in lowered:
        pack_order = "high_to_low"
    elif "low byte first" in lowered or "first byte in the low bits" in lowered or "lsb first" in lowered:
        pack_order = "low_to_high"

    return {
        "input_data_signal": data_input.name,
        "input_gate_signal": gate_input.name,
        "output_data_signal": data_output.name,
        "output_gate_signal": completion_output.name,
        "element_count": int(ratio),
        "input_width": input_width,
        "output_width": output_width,
        "pack_order": pack_order,
        "evidence_text": evidence,
    }


def infer_fifo_readback_family(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    """Infer a simple externally visible FIFO write/readback family."""
    evidence = _semantic_evidence_text(
        contract,
        task_description=task_description,
        spec_text=spec_text,
        additional_texts=additional_texts,
    )
    if not _FIFO_HINT_RE.search(evidence):
        return None

    write_enable = _select_read_write_control(contract, write=True, evidence_text=evidence)
    read_enable = _select_read_write_control(contract, write=False, evidence_text=evidence)
    if write_enable is None or read_enable is None or write_enable.name == read_enable.name:
        return None

    write_data = _select_directional_data_port(
        contract,
        direction=PortDirection.INPUT,
        exclude_names={write_enable.name, read_enable.name},
        role_hint="write",
        evidence_text=evidence,
    )
    read_data = _select_directional_data_port(
        contract,
        direction=PortDirection.OUTPUT,
        exclude_names=set(),
        role_hint="read",
        evidence_text=evidence,
        min_width=_port_width_int(write_data),
    )
    if write_data is None or read_data is None:
        return None

    empty_output = _select_named_scalar_output(contract, evidence_text=evidence, preferred_tokens={"empty"})
    full_output = _select_named_scalar_output(contract, evidence_text=evidence, preferred_tokens={"full"})
    if empty_output is None:
        return None

    return {
        "write_enable_signal": write_enable.name,
        "read_enable_signal": read_enable.name,
        "write_data_signal": write_data.name,
        "read_data_signal": read_data.name,
        "empty_signal": empty_output.name,
        "full_signal": full_output.name if full_output is not None else "",
        "evidence_text": evidence,
    }


def infer_ring_progression_family(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    """Infer a one-hot ring or rotational progression family."""
    evidence = _semantic_evidence_text(
        contract,
        task_description=task_description,
        spec_text=spec_text,
        additional_texts=additional_texts,
    )
    if not _RING_HINT_RE.search(evidence):
        return None
    output_port = _select_primary_data_output(contract, exclude_names=set(), min_width=2, evidence_text=evidence)
    if output_port is None:
        return None
    output_width = _port_width_int(output_port)
    if output_width is None or output_width < 2:
        return None
    return {
        "state_output_signal": output_port.name,
        "output_width": output_width,
        "evidence_text": evidence,
    }


def infer_traffic_light_phase_family(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    """Infer a traffic-light style mutually exclusive phase-output family."""
    evidence = _semantic_evidence_text(
        contract,
        task_description=task_description,
        spec_text=spec_text,
        additional_texts=additional_texts,
    )
    if not _TRAFFIC_HINT_RE.search(evidence):
        return None

    outputs = {
        token: _select_named_scalar_output(contract, evidence_text=evidence, preferred_tokens={token})
        for token in ("red", "yellow", "green")
    }
    if not all(outputs.values()):
        return None

    request_signal = _select_stream_gate_input(
        contract,
        evidence_text=evidence,
        preferred_tokens={"pass", "pedestrian", "request", "req", "button"},
    )
    return {
        "request_signal": request_signal.name if request_signal is not None else "",
        "red_signal": outputs["red"].name,
        "yellow_signal": outputs["yellow"].name,
        "green_signal": outputs["green"].name,
        "evidence_text": evidence,
    }


def infer_pipelined_multiply_family(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    """Infer a pipelined or enabled unsigned multiply family."""
    evidence = _semantic_evidence_text(
        contract,
        task_description=task_description,
        spec_text=spec_text,
        additional_texts=additional_texts,
    )
    if not _MULTIPLY_HINT_RE.search(evidence):
        return None

    input_ports = [port for port in _non_control_input_ports(contract) if (_port_width_int(port) or 0) > 1]
    if len(input_ports) < 2:
        return None
    ranked_inputs = sorted(
        input_ports,
        key=lambda port: (
            _data_name_score(port.name, preferred_tokens={"mul", "product", "factor", "operand", "a", "b"}),
            _port_width_int(port) or 0,
            port.name,
        ),
        reverse=True,
    )
    left = ranked_inputs[0]
    right = next((port for port in ranked_inputs[1:] if port.name != left.name), None)
    if right is None:
        return None
    output_port = _select_primary_data_output(
        contract,
        exclude_names=set(),
        min_width=max(_port_width_int(left) or 0, _port_width_int(right) or 0) + 1,
        evidence_text=evidence,
    )
    if output_port is None:
        return None

    input_gate = _select_stream_gate_input(contract, evidence_text=evidence, preferred_tokens={"mul", "start", "valid", "enable"})
    output_gate = _select_completion_output(contract, evidence_text=evidence, preferred_tokens={"mul", "done", "valid"})
    lowered = evidence.lower()
    signed_hint = bool(_SIGNED_MULTIPLY_HINT_RE.search(evidence))
    if "unsigned" in lowered and not signed_hint:
        arithmetic_domain = "unsigned"
    elif signed_hint:
        arithmetic_domain = "signed_or_ambiguous"
    else:
        arithmetic_domain = "unknown"
    return {
        "left_operand_signal": left.name,
        "right_operand_signal": right.name,
        "product_signal": output_port.name,
        "input_gate_signal": input_gate.name if input_gate is not None else "",
        "output_gate_signal": output_gate.name if output_gate is not None else "",
        "arithmetic_domain": arithmetic_domain,
        "evidence_text": evidence,
    }


def infer_fixed_point_add_family(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    """Infer a combinational fixed-point add/sub family."""
    evidence = _semantic_evidence_text(
        contract,
        task_description=task_description,
        spec_text=spec_text,
        additional_texts=additional_texts,
    )
    if contract.timing.sequential_kind != SequentialKind.COMB or not _FIXED_POINT_HINT_RE.search(evidence):
        return None
    input_ports = [port for port in _non_control_input_ports(contract) if (_port_width_int(port) or 0) > 1]
    output_port = _select_primary_data_output(contract, exclude_names=set(), min_width=2, evidence_text=evidence)
    if len(input_ports) < 2 or output_port is None:
        return None
    ranked_inputs = sorted(
        input_ports,
        key=lambda port: (_data_name_score(port.name, preferred_tokens={"a", "b", "lhs", "rhs", "in"}), _port_width_int(port) or 0, port.name),
        reverse=True,
    )
    return {
        "left_operand_signal": ranked_inputs[0].name,
        "right_operand_signal": ranked_inputs[1].name,
        "result_signal": output_port.name,
        "evidence_text": evidence,
    }


def infer_divide_relation_family(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    """Infer a simple dividend/divisor to quotient/remainder family."""
    evidence = _semantic_evidence_text(
        contract,
        task_description=task_description,
        spec_text=spec_text,
        additional_texts=additional_texts,
    )
    if not _DIVIDE_HINT_RE.search(evidence):
        return None

    dividend = _select_directional_data_port(contract, direction=PortDirection.INPUT, exclude_names=set(), role_hint="dividend", evidence_text=evidence)
    divisor = _select_directional_data_port(
        contract,
        direction=PortDirection.INPUT,
        exclude_names={dividend.name} if dividend is not None else set(),
        role_hint="divisor",
        evidence_text=evidence,
    )
    quotient = _select_directional_data_port(contract, direction=PortDirection.OUTPUT, exclude_names=set(), role_hint="quotient", evidence_text=evidence)
    remainder = _select_directional_data_port(
        contract,
        direction=PortDirection.OUTPUT,
        exclude_names={quotient.name} if quotient is not None else set(),
        role_hint="remainder",
        evidence_text=evidence,
    )
    if dividend is None or divisor is None or quotient is None or remainder is None:
        return None
    return {
        "dividend_signal": dividend.name,
        "divisor_signal": divisor.name,
        "quotient_signal": quotient.name,
        "remainder_signal": remainder.name,
        "evidence_text": evidence,
    }


def infer_sequence_detect_family(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> dict[str, Any] | None:
    """Infer a simple scalar sequence/pulse detect family from task evidence."""
    evidence = _semantic_evidence_text(
        contract,
        task_description=task_description,
        spec_text=spec_text,
        additional_texts=additional_texts,
    )
    if not _SEQUENCE_HINT_RE.search(evidence):
        return None
    pattern = _infer_bit_pattern(evidence)
    if not pattern:
        return None
    input_port = _select_serial_input(contract, exclude_names=set(), evidence_text=evidence)
    output_port = _select_completion_output(
        contract,
        evidence_text=evidence,
        preferred_tokens={"detect", "match", "pulse", "found", "hit"},
    )
    if input_port is None or output_port is None:
        return None
    return {
        "input_signal": input_port.name,
        "output_signal": output_port.name,
        "bit_pattern": pattern,
        "evidence_text": evidence,
    }


def infer_group_size(text: str | None) -> int | None:
    """Infer a small grouped-transaction size from descriptive text."""
    content = str(text or "").strip()
    if not content:
        return None
    pattern_candidates: list[int] = []
    for pattern in _GROUP_PATTERNS:
        for match in pattern.finditer(content):
            parsed = _parse_small_number(match.group("count"))
            if parsed is not None and parsed >= 2:
                pattern_candidates.append(parsed)
    if pattern_candidates:
        return max(pattern_candidates)

    fallback_candidates: list[int] = []
    for match in re.finditer(
        r"\b(?P<count>\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen)\b",
        content,
        re.IGNORECASE,
    ):
        parsed = _parse_small_number(match.group("count"))
        if parsed is None or parsed < 2:
            continue
        window = content[max(0, match.start() - 48) : min(len(content), match.end() + 96)]
        lower_window = window.lower()
        if any(token in lower_window for token in ("accum", "valid", "sample", "group", "closure", "received")):
            fallback_candidates.append(parsed)
    if fallback_candidates:
        return max(fallback_candidates)
    return None


def _semantic_evidence_text(
    contract: DUTContract,
    *,
    task_description: str | None = None,
    spec_text: str | None = None,
    additional_texts: list[str] | None = None,
) -> str:
    return " ".join(
        text
        for text in [
            contract.module_name,
            " ".join(_name_tokens(contract.module_name)),
            task_description or "",
            spec_text or "",
            *contract.assumptions,
            *(additional_texts or []),
        ]
        if text
    ).strip()


def _parse_small_number(raw: str | None) -> int | None:
    token = str(raw or "").strip().lower()
    if not token:
        return None
    if token.isdigit():
        return int(token)
    return _NUMBER_WORDS.get(token)


def _infer_bit_pattern(text: str) -> str:
    matches = [match.group(0) for match in _BIT_PATTERN_RE.finditer(text or "")]
    if not matches:
        return ""
    matches.sort(key=len, reverse=True)
    return matches[0]


def _non_control_input_ports(contract: DUTContract) -> list[PortSpec]:
    control_names = {clock.name.lower() for clock in contract.clocks} | {reset.name.lower() for reset in contract.resets}
    return [
        port
        for port in contract.ports
        if port.direction == PortDirection.INPUT and port.name.lower() not in control_names
    ]


def _observable_output_ports(contract: DUTContract) -> list[PortSpec]:
    observable = {name.lower() for name in contract.observable_outputs}
    candidates = [
        port
        for port in contract.ports
        if port.direction in {PortDirection.OUTPUT, PortDirection.INOUT}
        and (not observable or port.name.lower() in observable)
    ]
    if candidates:
        return candidates
    return [
        port
        for port in contract.ports
        if port.direction in {PortDirection.OUTPUT, PortDirection.INOUT}
    ]


def _port_width_int(port: PortSpec | None) -> int | None:
    if port is None or not isinstance(port.width, int):
        return None
    return int(port.width)


def _name_tokens(name: str) -> tuple[str, ...]:
    if not name:
        return ()
    expanded = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    expanded = re.sub(r"([A-Za-z])([0-9])", r"\1_\2", expanded)
    expanded = re.sub(r"([0-9])([A-Za-z])", r"\1_\2", expanded)
    lowered = expanded.lower().replace("[", "_").replace("]", "_")
    tokens = tuple(token for token in re.split(r"[^a-z0-9]+", lowered) if token)
    if not tokens and lowered:
        return (lowered,)
    return tokens


def _handshake_role_bonus(contract: DUTContract, port_name: str, expected_tokens: set[str]) -> int:
    lowered_name = port_name.lower()
    bonus = 0
    for group in contract.handshake_groups:
        for role, signal_name in group.signals.items():
            if str(signal_name).strip().lower() != lowered_name:
                continue
            role_tokens = set(_name_tokens(str(role)))
            if role_tokens & expected_tokens:
                bonus += 2
            elif any(token in str(role).lower() for token in expected_tokens):
                bonus += 1
    return bonus


def _scalarish(port: PortSpec) -> bool:
    width = _port_width_int(port)
    return width in (None, 1)


def _is_clock_or_reset_like(name: str) -> bool:
    tokens = set(_name_tokens(name))
    return bool(tokens & _CLOCK_LIKE_TOKENS) or bool(tokens & _RESET_LIKE_TOKENS)


def _data_name_score(name: str, *, preferred_tokens: set[str] | None = None) -> int:
    tokens = set(_name_tokens(name))
    score = 0
    if tokens & _DATA_TOKENS:
        score += 2
    if preferred_tokens and tokens & preferred_tokens:
        score += 3
    lowered = name.lower()
    if any(token in lowered for token in preferred_tokens or set()):
        score += 1
    return score


def _select_best_port(
    candidates: Iterable[PortSpec],
    *,
    score_fn,
    min_score: int = 1,
) -> PortSpec | None:
    ranked: list[tuple[int, int, str, PortSpec]] = []
    for port in candidates:
        score = int(score_fn(port))
        ranked.append((score, _port_width_int(port) or 0, port.name, port))
    if not ranked:
        return None
    ranked.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
    best_score = ranked[0][0]
    if best_score < min_score:
        return None
    top = [item for item in ranked if item[0] == best_score]
    if len(top) > 1:
        top.sort(key=lambda item: (item[1], item[2]), reverse=True)
    return top[0][3]


def _select_stream_gate_input(
    contract: DUTContract,
    *,
    evidence_text: str,
    preferred_tokens: set[str] | None = None,
) -> PortSpec | None:
    candidates = [
        port
        for port in _non_control_input_ports(contract)
        if _scalarish(port) and not _is_clock_or_reset_like(port.name)
    ]
    preferred = preferred_tokens or _VALID_INPUT_TOKENS

    def score(port: PortSpec) -> int:
        tokens = set(_name_tokens(port.name))
        value = 0
        if tokens & preferred:
            value += 4
        if tokens & _VALID_INPUT_TOKENS:
            value += 2
        if port.name.lower().endswith("_en") or port.name.lower().endswith("valid"):
            value += 1
        value += _handshake_role_bonus(contract, port.name, preferred | _VALID_INPUT_TOKENS)
        if "valid" in evidence_text.lower() and tokens & {"sample", "accept"}:
            value += 1
        return value

    fallback_min_score = 1 if "valid" in evidence_text.lower() else 2
    return _select_best_port(candidates, score_fn=score, min_score=fallback_min_score)


def _select_completion_output(
    contract: DUTContract,
    *,
    evidence_text: str,
    preferred_tokens: set[str] | None = None,
) -> PortSpec | None:
    candidates = [port for port in _observable_output_ports(contract) if _scalarish(port)]
    preferred = preferred_tokens or _COMPLETION_OUTPUT_TOKENS

    def score(port: PortSpec) -> int:
        tokens = set(_name_tokens(port.name))
        value = 0
        if tokens & preferred:
            value += 4
        if tokens & _COMPLETION_OUTPUT_TOKENS:
            value += 2
        if port.name.lower().endswith("_valid") or port.name.lower().endswith("_done"):
            value += 1
        if "output event" in evidence_text.lower() and tokens & {"event", "pulse"}:
            value += 1
        return value

    return _select_best_port(candidates, score_fn=score, min_score=2)


def _select_primary_data_input(
    contract: DUTContract,
    *,
    exclude_names: set[str],
    evidence_text: str,
) -> PortSpec | None:
    candidates = [
        port
        for port in _non_control_input_ports(contract)
        if port.name not in exclude_names and (_port_width_int(port) or 0) > 1
    ]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    def score(port: PortSpec) -> int:
        value = _data_name_score(port.name, preferred_tokens={"data", "din", "sample", "payload", "sum", "input", "word", "byte"})
        width = _port_width_int(port)
        if width is not None and width > 1:
            value += 1
        if "accum" in evidence_text.lower() and set(_name_tokens(port.name)) & {"data", "sample", "sum"}:
            value += 2
        return value

    return _select_best_port(candidates, score_fn=score, min_score=1)


def _select_primary_data_output(
    contract: DUTContract,
    *,
    exclude_names: set[str],
    min_width: int | None,
    evidence_text: str,
    prefer_parallel: bool = False,
) -> PortSpec | None:
    candidates = [
        port
        for port in _observable_output_ports(contract)
        if port.name not in exclude_names and (_port_width_int(port) or 0) > 1
    ]
    if min_width is not None:
        candidates = [port for port in candidates if (_port_width_int(port) or 0) >= min_width]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    preferred = {"data", "dout", "sum", "result", "out", "value"}
    if prefer_parallel:
        preferred |= {"parallel", "byte", "word", "pack"}

    def score(port: PortSpec) -> int:
        value = _data_name_score(port.name, preferred_tokens=preferred)
        width = _port_width_int(port)
        if width is not None and min_width is not None and width >= min_width:
            value += 1
        if "sum" in evidence_text.lower() and set(_name_tokens(port.name)) & {"sum", "result"}:
            value += 2
        return value

    return _select_best_port(candidates, score_fn=score, min_score=1)


def _select_serial_input(
    contract: DUTContract,
    *,
    exclude_names: set[str],
    evidence_text: str,
) -> PortSpec | None:
    candidates = [
        port
        for port in _non_control_input_ports(contract)
        if port.name not in exclude_names and _scalarish(port)
    ]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0]

    def score(port: PortSpec) -> int:
        tokens = set(_name_tokens(port.name))
        value = 0
        if tokens & _SERIAL_TOKENS:
            value += 4
        if tokens & {"data", "in"}:
            value += 1
        if "sequence" in evidence_text.lower() and tokens & {"data", "bit"}:
            value += 1
        return value

    return _select_best_port(candidates, score_fn=score, min_score=1)


def _select_read_write_control(
    contract: DUTContract,
    *,
    write: bool,
    evidence_text: str,
) -> PortSpec | None:
    candidates = [
        port
        for port in _non_control_input_ports(contract)
        if _scalarish(port) and not _is_clock_or_reset_like(port.name)
    ]
    role_tokens = _WRITE_TOKENS if write else _READ_TOKENS

    def score(port: PortSpec) -> int:
        tokens = set(_name_tokens(port.name))
        value = 0
        if tokens & role_tokens:
            value += 4
        if tokens & {"enable", "en", "valid", "inc"}:
            value += 1
        value += _handshake_role_bonus(contract, port.name, role_tokens)
        if write and "write" in evidence_text.lower() and tokens & {"valid", "enable"}:
            value += 1
        if not write and "read" in evidence_text.lower() and tokens & {"valid", "enable"}:
            value += 1
        return value

    return _select_best_port(candidates, score_fn=score, min_score=2)


def _select_directional_data_port(
    contract: DUTContract,
    *,
    direction: PortDirection,
    exclude_names: set[str],
    role_hint: str,
    evidence_text: str,
    min_width: int | None = None,
) -> PortSpec | None:
    if direction == PortDirection.INPUT:
        ports = _non_control_input_ports(contract)
    else:
        ports = _observable_output_ports(contract)
    candidates = [
        port
        for port in ports
        if port.name not in exclude_names and (_port_width_int(port) or 0) > 1
    ]
    if min_width is not None:
        candidates = [port for port in candidates if (_port_width_int(port) or 0) >= min_width]
    if not candidates:
        return None

    preferred_tokens = {"data", role_hint}
    if role_hint == "write":
        preferred_tokens |= {"din", "payload", "w"}
    elif role_hint == "read":
        preferred_tokens |= {"dout", "r"}
    elif role_hint == "dividend":
        preferred_tokens |= {"a", "lhs", "numerator"}
    elif role_hint == "divisor":
        preferred_tokens |= {"b", "rhs", "denominator"}
    elif role_hint == "quotient":
        preferred_tokens |= {"result", "quotient", "q"}
    elif role_hint == "remainder":
        preferred_tokens |= {"odd", "remain", "remainder", "r"}

    def score(port: PortSpec) -> int:
        value = _data_name_score(port.name, preferred_tokens=preferred_tokens)
        if role_hint in evidence_text.lower() and set(_name_tokens(port.name)) & preferred_tokens:
            value += 1
        return value

    if len(candidates) == 1:
        return candidates[0]
    return _select_best_port(candidates, score_fn=score, min_score=1)


def _select_named_scalar_output(
    contract: DUTContract,
    *,
    evidence_text: str,
    preferred_tokens: set[str],
) -> PortSpec | None:
    candidates = [port for port in _observable_output_ports(contract) if _scalarish(port)]

    def score(port: PortSpec) -> int:
        tokens = set(_name_tokens(port.name))
        value = 0
        if tokens & preferred_tokens:
            value += 4
        if any(token in port.name.lower() for token in preferred_tokens):
            value += 1
        if tokens & {"phase", "state", "light"} and preferred_tokens & {"red", "yellow", "green"}:
            value += 1
        if preferred_tokens & {"empty", "full"} and "fifo" in evidence_text.lower():
            value += 1
        return value

    return _select_best_port(candidates, score_fn=score, min_score=2)
