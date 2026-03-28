"""Interface helpers for `verified_synchronizer`.

This file is rendered from contract artifacts. It keeps interface handling
conservative and records unresolved items instead of inventing missing semantics.

Interface notes:
# - Golden interface mentioned port 'brstn', but it was not found in the RTL header.
# - Golden interface mentioned port 'data_in', but it was not found in the RTL header.
# - Golden interface described reset 'brstn', but the signal was not found in the RTL ports.
# - Spec/reset hint could not be mapped to a known reset port: brstn: Active-low reset signal B. Defined as 0 for reset and 1 for reset signal inactive.
# - Spec/reset hint could not be mapped to a known reset port: If the reset signal B (brstn) is high, the registers (en_clap_one and en_clap_two) are updated based on the value of en_data_reg. The register en_clap_one is assigned the value of en_data_reg, and en_clap_two is assigned the previous value of en_clap_one.
# - Reset polarity for 'clk_a' is unresolved.
# - Reset polarity for 'clk_b' is unresolved.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

MODULE_NAME = 'verified_synchronizer'
CLOCK_SIGNALS = ['clk_a', 'clk_b']
RESET_SIGNALS = ['arstn', 'clk_a', 'clk_b']
PROTOCOL_SIGNAL_NAMES = []
BUSINESS_INPUTS = ['input', 'input', 'data_en']
BUSINESS_OUTPUTS = ['dataout']
UNKNOWN_DIRECTION_SIGNALS = []
OPTIONAL_SIGNALS = []
HANDSHAKE_GROUPS = json.loads('[]')
UNRESOLVED_ITEMS = ["Golden interface mentioned port 'brstn', but it was not found in the RTL "
 'header.',
 "Golden interface mentioned port 'data_in', but it was not found in the RTL "
 'header.',
 "Golden interface described reset 'brstn', but the signal was not found in "
 'the RTL ports.',
 'Spec/reset hint could not be mapped to a known reset port: brstn: Active-low '
 'reset signal B. Defined as 0 for reset and 1 for reset signal inactive.',
 'Spec/reset hint could not be mapped to a known reset port: If the reset '
 'signal B (brstn) is high, the registers (en_clap_one and en_clap_two) are '
 'updated based on the value of en_data_reg. The register en_clap_one is '
 'assigned the value of en_data_reg, and en_clap_two is assigned the previous '
 'value of en_clap_one.',
 "Reset polarity for 'clk_a' is unresolved.",
 "Reset polarity for 'clk_b' is unresolved."]


@dataclass
class VerifiedSynchronizerInterface:
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
