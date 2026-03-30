"""Interface helpers for `verified_calendar`.

This file is rendered from contract artifacts. It keeps interface handling
conservative and records unresolved items instead of inventing missing semantics.

Interface notes:
# - Spec/reset hint could not be mapped to a known reset port: The calendar module uses three always blocks to update the values of seconds, minutes, and hours based on the clock signal and reset signal.
# - Spec/reset hint could not be mapped to a known reset port: The second always block also triggers on the positive edge of the clock signal or the positive edge of the reset signal. It handles the minutes value (Mins). If the reset signal is active, it sets the minutes value to 0. If both the minutes and seconds values are 59, it wraps around and sets the minutes value to 0. If the seconds value is 59, it increments the minutes value by 1. Otherwise, it keeps the minutes value unchanged.
# - Spec/reset hint could not be mapped to a known reset port: The third always block triggers on the positive edge of the clock signal or the positive edge of the reset signal. It handles the hours value (Hours). If the reset signal is active, it sets the hours value to 0. If the hours, minutes, and seconds values are all at their maximum (23, 59, and 59 respectively), it wraps around and sets the hours value to 0. If the minutes and seconds values are both 59, it increments the hours value by 1. Otherwise, it keeps the hours value unchanged.
# - Port segment is missing a direction keyword: CLK
# - Port segment is missing a direction keyword: RST
# - Port segment is missing a direction keyword: Hours
# - Port segment is missing a direction keyword: Mins
# - Port segment is missing a direction keyword: Secs
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

MODULE_NAME = 'verified_calendar'
CLOCK_SIGNALS = ['CLK']
RESET_SIGNALS = ['RST']
PROTOCOL_SIGNAL_NAMES = []
BUSINESS_INPUTS = []
BUSINESS_OUTPUTS = ['Hours', 'Mins', 'Secs']
UNKNOWN_DIRECTION_SIGNALS = []
OPTIONAL_SIGNALS = []
HANDSHAKE_GROUPS = json.loads('[]')
UNRESOLVED_ITEMS = ['Spec/reset hint could not be mapped to a known reset port: The calendar '
 'module uses three always blocks to update the values of seconds, minutes, '
 'and hours based on the clock signal and reset signal.',
 'Spec/reset hint could not be mapped to a known reset port: The second always '
 'block also triggers on the positive edge of the clock signal or the positive '
 'edge of the reset signal. It handles the minutes value (Mins). If the reset '
 'signal is active, it sets the minutes value to 0. If both the minutes and '
 'seconds values are 59, it wraps around and sets the minutes value to 0. If '
 'the seconds value is 59, it increments the minutes value by 1. Otherwise, it '
 'keeps the minutes value unchanged.',
 'Spec/reset hint could not be mapped to a known reset port: The third always '
 'block triggers on the positive edge of the clock signal or the positive edge '
 'of the reset signal. It handles the hours value (Hours). If the reset signal '
 'is active, it sets the hours value to 0. If the hours, minutes, and seconds '
 'values are all at their maximum (23, 59, and 59 respectively), it wraps '
 'around and sets the hours value to 0. If the minutes and seconds values are '
 'both 59, it increments the hours value by 1. Otherwise, it keeps the hours '
 'value unchanged.',
 'Port segment is missing a direction keyword: CLK',
 'Port segment is missing a direction keyword: RST',
 'Port segment is missing a direction keyword: Hours',
 'Port segment is missing a direction keyword: Mins',
 'Port segment is missing a direction keyword: Secs']


@dataclass
class VerifiedCalendarInterface:
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
