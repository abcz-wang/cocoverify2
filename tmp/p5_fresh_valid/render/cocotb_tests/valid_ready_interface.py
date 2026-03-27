"""Interface helpers for `valid_ready`.

This file is rendered from contract artifacts. It keeps interface handling
conservative and records unresolved items instead of inventing missing semantics.

Interface notes:
# - Combinational body constructs were found, but detected clock/reset or handshake structure makes the timing model ambiguous.
# - Reset polarity for 'aresetn' is inferred heuristically from the signal name or sensitivity list.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

MODULE_NAME = 'valid_ready'
CLOCK_SIGNALS = ['aclk']
RESET_SIGNALS = ['aresetn']
PROTOCOL_SIGNAL_NAMES = ['in_valid', 'in_ready', 'out_valid', 'out_ready', 'start', 'done']
BUSINESS_INPUTS = ['in_data']
BUSINESS_OUTPUTS = ['out_data']
UNKNOWN_DIRECTION_SIGNALS = []
OPTIONAL_SIGNALS = []
HANDSHAKE_GROUPS = json.loads(('[\n'
 '  {\n'
 '    "confidence": 0.9,\n'
 '    "group_name": "in",\n'
 '    "pattern": "valid_ready",\n'
 '    "signals": {\n'
 '      "ready": "in_ready",\n'
 '      "valid": "in_valid"\n'
 '    },\n'
 '    "source": "rtl_heuristic"\n'
 '  },\n'
 '  {\n'
 '    "confidence": 0.9,\n'
 '    "group_name": "out",\n'
 '    "pattern": "valid_ready",\n'
 '    "signals": {\n'
 '      "ready": "out_ready",\n'
 '      "valid": "out_valid"\n'
 '    },\n'
 '    "source": "rtl_heuristic"\n'
 '  },\n'
 '  {\n'
 '    "confidence": 0.8,\n'
 '    "group_name": "default",\n'
 '    "pattern": "start_done",\n'
 '    "signals": {\n'
 '      "done": "done",\n'
 '      "start": "start"\n'
 '    },\n'
 '    "source": "rtl_heuristic"\n'
 '  }\n'
 ']'))
UNRESOLVED_ITEMS = ['Combinational body constructs were found, but detected clock/reset or '
 'handshake structure makes the timing model ambiguous.',
 "Reset polarity for 'aresetn' is inferred heuristically from the signal name "
 'or sensitivity list.']


@dataclass
class ValidReadyInterface:
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
