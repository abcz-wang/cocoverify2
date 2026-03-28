"""Interface helpers for `dual_port_RAM`.

This file is rendered from contract artifacts. It keeps interface handling
conservative and records unresolved items instead of inventing missing semantics.

Interface notes:
# - Golden interface mentioned port 'wrstn', but it was not found in the RTL header.
# - Golden interface mentioned port 'rrstn', but it was not found in the RTL header.
# - Golden interface mentioned port 'winc', but it was not found in the RTL header.
# - Golden interface mentioned port 'rinc', but it was not found in the RTL header.
# - Golden interface mentioned port 'wfull', but it was not found in the RTL header.
# - Golden interface mentioned port 'rempty', but it was not found in the RTL header.
# - Golden interface described reset 'wrstn', but the signal was not found in the RTL ports.
# - Golden interface described reset 'rrstn', but the signal was not found in the RTL ports.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

MODULE_NAME = 'dual_port_RAM'
CLOCK_SIGNALS = ['wclk', 'rclk']
RESET_SIGNALS = []
PROTOCOL_SIGNAL_NAMES = []
BUSINESS_INPUTS = ['wenc', 'waddr', 'wdata', 'renc', 'raddr']
BUSINESS_OUTPUTS = ['rdata']
UNKNOWN_DIRECTION_SIGNALS = []
OPTIONAL_SIGNALS = []
HANDSHAKE_GROUPS = json.loads('[]')
UNRESOLVED_ITEMS = ["Golden interface mentioned port 'wrstn', but it was not found in the RTL "
 'header.',
 "Golden interface mentioned port 'rrstn', but it was not found in the RTL "
 'header.',
 "Golden interface mentioned port 'winc', but it was not found in the RTL "
 'header.',
 "Golden interface mentioned port 'rinc', but it was not found in the RTL "
 'header.',
 "Golden interface mentioned port 'wfull', but it was not found in the RTL "
 'header.',
 "Golden interface mentioned port 'rempty', but it was not found in the RTL "
 'header.',
 "Golden interface described reset 'wrstn', but the signal was not found in "
 'the RTL ports.',
 "Golden interface described reset 'rrstn', but the signal was not found in "
 'the RTL ports.',
 'Spec/reset hint could not be mapped to a known reset port: wrstn: Write '
 'reset signal. Defined as 0 for reset and 1 for reset signal inactive.',
 'Spec/reset hint could not be mapped to a known reset port: rrstn: Read reset '
 'signal. Defined as 0 for reset and 1 for reset signal inactive.',
 'Spec/reset hint could not be mapped to a known reset port: The write pointer '
 'is incremented on the positive edge of the write clock (posedge wclk) and '
 'reset to 0 on write reset (~wrstn).',
 'Spec/reset hint could not be mapped to a known reset port: The read pointer '
 'is incremented on the positive edge of the read clock (posedge rclk) and '
 'reset to 0 on read reset (~rrstn).',
 'Spec/reset hint could not be mapped to a known reset port: The buffer '
 'registers are updated on the positive edge of the respective clocks and '
 'reset to 0 on the respective resets (~wrstn and ~rrstn).',
 'Multiple module headers were found in verified_asyn_fifo.v; using the first '
 "module 'dual_port_RAM'."]


@dataclass
class DualPortRamInterface:
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
