"""Interface helpers for `verified_parallel2serial`.

This file is rendered from contract artifacts. It keeps interface handling
conservative and records unresolved items instead of inventing missing semantics.

Interface notes:
# - Detected valid_ready-like signal(s) ['valid_out'] without matching role(s) ['ready'] in group 'out'.
# - Spec/reset hint could not be mapped to a known reset port: The most significant bit of the parallel input is assigned to the serial output (dout). On each clock cycle, if the counter (cnt) is 3, indicating the last bit of the parallel input, the module updates the data register (data) with the parallel input (d), resets the counter (cnt) to 0, and sets the valid signal (valid) to 1.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

MODULE_NAME = 'verified_parallel2serial'
CLOCK_SIGNALS = ['clk']
RESET_SIGNALS = ['rst_n']
PROTOCOL_SIGNAL_NAMES = []
BUSINESS_INPUTS = ['d']
BUSINESS_OUTPUTS = ['valid_out', 'dout']
UNKNOWN_DIRECTION_SIGNALS = []
OPTIONAL_SIGNALS = []
HANDSHAKE_GROUPS = json.loads('[]')
UNRESOLVED_ITEMS = ["Detected valid_ready-like signal(s) ['valid_out'] without matching role(s) "
 "['ready'] in group 'out'.",
 'Spec/reset hint could not be mapped to a known reset port: The most '
 'significant bit of the parallel input is assigned to the serial output '
 '(dout). On each clock cycle, if the counter (cnt) is 3, indicating the last '
 'bit of the parallel input, the module updates the data register (data) with '
 'the parallel input (d), resets the counter (cnt) to 0, and sets the valid '
 'signal (valid) to 1.']


@dataclass
class VerifiedParallel2serialInterface:
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
