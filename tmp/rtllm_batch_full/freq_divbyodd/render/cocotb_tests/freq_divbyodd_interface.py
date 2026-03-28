"""Interface helpers for `freq_divbyodd`.

This file is rendered from contract artifacts. It keeps interface handling
conservative and records unresolved items instead of inventing missing semantics.

Interface notes:
# - All parsed ports have unknown directions; the module may use a non-ANSI header.
# - No observable outputs were identified from the parsed RTL header.
# - Reset polarity for 'clk' is unresolved.
# - Port segment is missing a direction keyword: clk
# - Port segment is missing a direction keyword: rst_n
# - Port segment is missing a direction keyword: clk_div
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

MODULE_NAME = 'freq_divbyodd'
CLOCK_SIGNALS = ['clk', 'clk_div', 'rst_n']
RESET_SIGNALS = ['clk', 'rst_n']
PROTOCOL_SIGNAL_NAMES = []
BUSINESS_INPUTS = []
BUSINESS_OUTPUTS = []
UNKNOWN_DIRECTION_SIGNALS = ['clk', 'rst_n', 'clk_div']
OPTIONAL_SIGNALS = ['clk', 'clk_div', 'rst_n']
HANDSHAKE_GROUPS = json.loads('[]')
UNRESOLVED_ITEMS = ['All parsed ports have unknown directions; the module may use a non-ANSI '
 'header.',
 'No observable outputs were identified from the parsed RTL header.',
 "Reset polarity for 'clk' is unresolved.",
 'Port segment is missing a direction keyword: clk',
 'Port segment is missing a direction keyword: rst_n',
 'Port segment is missing a direction keyword: clk_div']


@dataclass
class FreqDivbyoddInterface:
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
            return dict(group.get("signals", {}))
        return None
