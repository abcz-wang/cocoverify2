"""Helpers for rendering DUT interface modules."""

from __future__ import annotations

from pprint import pformat

from cocoverify2.core.models import DUTContract
from cocoverify2.core.types import PortDirection


def render_interface_module(contract: DUTContract) -> tuple[str, dict[str, object]]:
    """Render the `<dut>_interface.py` module content and summary."""
    class_name = f"{_camel(contract.module_name)}Interface"
    clock_names = [clock.name for clock in contract.clocks]
    reset_names = [reset.name for reset in contract.resets]
    protocol_signal_names = list(contract.handshake_signals)
    control_signals = set(clock_names) | set(reset_names) | set(protocol_signal_names)
    business_inputs = [
        port.name
        for port in contract.ports
        if port.direction == PortDirection.INPUT and port.name not in control_signals
    ]
    business_outputs = [
        port.name
        for port in contract.ports
        if port.direction in {PortDirection.OUTPUT, PortDirection.INOUT} and port.name not in control_signals
    ]
    unknown_direction_signals = [port.name for port in contract.ports if port.direction == PortDirection.UNKNOWN]
    unresolved_items = _deduped(contract.ambiguities + contract.extraction_warnings)
    optional_signals = sorted(
        {
            *unknown_direction_signals,
            *[port.name for port in contract.ports if port.direction == PortDirection.INOUT],
        }
    )
    helper_comment = "\n".join(f"# - {item}" for item in unresolved_items[:8]) or "# - none"
    content = f'''"""Interface helpers for `{contract.module_name}`.

This file is rendered from contract artifacts. It keeps interface handling
conservative and records unresolved items instead of inventing missing semantics.

Interface notes:
{helper_comment}
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

MODULE_NAME = {contract.module_name!r}
CLOCK_SIGNALS = {pformat(clock_names)}
RESET_SIGNALS = {pformat(reset_names)}
PROTOCOL_SIGNAL_NAMES = {pformat(protocol_signal_names)}
BUSINESS_INPUTS = {pformat(business_inputs)}
BUSINESS_OUTPUTS = {pformat(business_outputs)}
UNKNOWN_DIRECTION_SIGNALS = {pformat(unknown_direction_signals)}
OPTIONAL_SIGNALS = {pformat(optional_signals)}
HANDSHAKE_GROUPS = json.loads({pformat(_json_dump(contract.handshake_groups))})
UNRESOLVED_ITEMS = {pformat(unresolved_items)}


@dataclass
class {class_name}:
    """Thin interface binding helper rendered from the contract artifact."""

    dut: Any
    signal_cache: dict[str, Any] = field(default_factory=dict)

    def bind_signals(self) -> None:
        """Bind all known interface and protocol signals that actually exist on the DUT."""
        signal_names = sorted({{
            *CLOCK_SIGNALS,
            *RESET_SIGNALS,
            *PROTOCOL_SIGNAL_NAMES,
            *BUSINESS_INPUTS,
            *BUSINESS_OUTPUTS,
            *OPTIONAL_SIGNALS,
        }})
        for signal_name in signal_names:
            if hasattr(self.dut, signal_name):
                self.signal_cache[signal_name] = getattr(self.dut, signal_name)

    def signal_exists(self, signal_name: str) -> bool:
        """Return whether the DUT exposes the requested signal."""
        return signal_name in self.signal_cache or hasattr(self.dut, signal_name)

    def get_signal(self, signal_name: str) -> Any | None:
        """Get a signal handle if present, otherwise return ``None``."""
        if signal_name in self.signal_cache:
            return self.signal_cache[signal_name]
        if hasattr(self.dut, signal_name):
            signal = getattr(self.dut, signal_name)
            self.signal_cache[signal_name] = signal
            return signal
        return None

    def business_input_names(self) -> list[str]:
        """Return business-input signals, excluding clock/reset/control signals."""
        return list(BUSINESS_INPUTS)

    def business_output_names(self) -> list[str]:
        """Return business-output signals, excluding clock/reset/control signals."""
        return list(BUSINESS_OUTPUTS)

    def clock_name(self) -> str | None:
        """Return the preferred clock signal name if one was inferred."""
        return CLOCK_SIGNALS[0] if CLOCK_SIGNALS else None

    def reset_name(self) -> str | None:
        """Return the preferred reset signal name if one was inferred."""
        return RESET_SIGNALS[0] if RESET_SIGNALS else None

    def protocol_signal_names(self) -> list[str]:
        """Return control/protocol signals derived from handshake hints."""
        return list(PROTOCOL_SIGNAL_NAMES)

    def protocol_group(self, pattern: str, group_name: str | None = None) -> dict[str, str] | None:
        """Look up a rendered handshake group by pattern and optional name."""
        for group in HANDSHAKE_GROUPS:
            if group.get("pattern") != pattern:
                continue
            if group_name is not None and group.get("group_name") != group_name:
                continue
            return dict(group.get("signals", {{}}))
        return None
'''
    summary = {
        "class_name": class_name,
        "business_inputs": business_inputs,
        "business_outputs": business_outputs,
        "clock_signals": clock_names,
        "reset_signals": reset_names,
        "protocol_signal_names": protocol_signal_names,
        "unknown_direction_signals": unknown_direction_signals,
        "optional_signals": optional_signals,
        "unresolved_items": unresolved_items,
    }
    return content, summary


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


def _json_dump(value: object) -> str:
    import json

    if isinstance(value, list):
        payload = [item.model_dump(mode="json") if hasattr(item, "model_dump") else item for item in value]
    elif hasattr(value, "model_dump"):
        payload = value.model_dump(mode="json")
    else:
        payload = value
    return json.dumps(payload, indent=2, sort_keys=True)
