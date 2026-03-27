"""Helpers for rendering the Phase 4 Makefile scaffold."""

from __future__ import annotations


def render_makefile(module_name: str, *, default_test_module: str) -> tuple[str, dict[str, object]]:
    """Render a conservative Makefile scaffold for later execution stages."""
    content = f'''# Phase 4 render artifact for {module_name}
# This Makefile is a static scaffold only. Phase 5 will decide the actual
# execution mode, simulator options, and source-list wiring.

TOPLEVEL ?= {module_name}
MODULE ?= {default_test_module}
SIM ?= icarus

# Populate VERILOG_SOURCES in Phase 5 or from the command line.
VERILOG_SOURCES ?=

# Example:
#   make TOPLEVEL={module_name} MODULE={default_test_module} VERILOG_SOURCES="dut.v"
'''
    summary = {
        "default_toplevel": module_name,
        "default_module": default_test_module,
        "is_phase4_scaffold": True,
    }
    return content, summary
