"""Interface helpers for `verified_traffic_light`.

This file is rendered from contract artifacts. It keeps interface handling
conservative and records unresolved items instead of inventing missing semantics.

Interface notes:
# - Spec/reset hint could not be mapped to a known reset port: The second always block handles the counting logic of the internal counter (cnt). The counter is decremented by 1 on every positive edge of the clock or negative edge of the reset signal. The counter values are adjusted based on various conditions:
# - Spec/reset hint could not be mapped to a known reset port: The final always block handles the output signals. It assigns the previous values (p_red, p_yellow, p_green) to the output signals (red, yellow, green) on the positive edge of the clock or negative edge of the reset signal.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

MODULE_NAME = 'verified_traffic_light'
CLOCK_SIGNALS = ['clk']
RESET_SIGNALS = ['rst_n']
PROTOCOL_SIGNAL_NAMES = []
BUSINESS_INPUTS = ['pass_request']
BUSINESS_OUTPUTS = ['clock', 'red', 'yellow', 'green']
UNKNOWN_DIRECTION_SIGNALS = []
OPTIONAL_SIGNALS = []
HANDSHAKE_GROUPS = json.loads('[]')
UNRESOLVED_ITEMS = ['Spec/reset hint could not be mapped to a known reset port: The second always '
 'block handles the counting logic of the internal counter (cnt). The counter '
 'is decremented by 1 on every positive edge of the clock or negative edge of '
 'the reset signal. The counter values are adjusted based on various '
 'conditions:',
 'Spec/reset hint could not be mapped to a known reset port: The final always '
 'block handles the output signals. It assigns the previous values (p_red, '
 'p_yellow, p_green) to the output signals (red, yellow, green) on the '
 'positive edge of the clock or negative edge of the reset signal.']


@dataclass
class VerifiedTrafficLightInterface:
    """Thin interface binding helper rendered from the contract artifact."""

    dut: Any
    signal_cache: dict[str, Any] = field(default_factory=dict)

    def bind_signals(self) -> None:
        """Bind all known interface and protocol signals that actually exist on the DUT."""
        signal_names = sorted({
            *CLOCK_SIGNALS,
            *RESET_SIGNALS,
            *PROTOCOL_SIGNAL_NAMES,
            *BUSINESS_INPUTS,
            *BUSINESS_OUTPUTS,
            *OPTIONAL_SIGNALS,
        })
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

    def clock_names(self) -> list[str]:
        """Return all inferred clock signal names in deterministic order."""
        return list(CLOCK_SIGNALS)

    def reset_name(self) -> str | None:
        """Return the preferred reset signal name if one was inferred."""
        return RESET_SIGNALS[0] if RESET_SIGNALS else None

    def reset_names(self) -> list[str]:
        """Return all inferred reset signal names in deterministic order."""
        return list(RESET_SIGNALS)

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
            return dict(group.get("signals", {}))
        return None
