"""Helpers for rendering the Phase 4 executable Makefile shell."""

from __future__ import annotations

MAKEFILE_CONTRACT_VERSION = "executable-shell-v1"
MAKEFILE_CONTRACT_MARKER = f"CV2_MAKEFILE_CONTRACT := {MAKEFILE_CONTRACT_VERSION}"


def render_makefile(module_name: str, *, default_test_module: str) -> tuple[str, dict[str, object]]:
    """Render an executable Makefile shell for Phase 5 make-mode execution."""
    content = f"""# Phase 4 render artifact for {module_name}
# Executable Makefile shell: Phase 5 injects simulator/config variables and runs it.
{MAKEFILE_CONTRACT_MARKER}

TOPLEVEL_LANG ?= verilog
SIM ?= icarus
TOPLEVEL ?= {module_name}
MODULE ?= {default_test_module}

# Phase 5 must inject RTL sources and resolve the cocotb makefiles directory.
COCOTB_MAKEFILES_DIR ?=
VERILOG_SOURCES ?=
INCLUDE_DIRS ?=
DEFINE_OVERRIDES ?=
PARAMETER_OVERRIDES ?=
PLUSARGS ?=
WAVES ?= 0
COCOTB_RESULTS_FILE ?=
EXTRA_COMPILE_ARGS ?=
EXTRA_SIM_ARGS ?=

ifeq ($(strip $(VERILOG_SOURCES)),)
$(error VERILOG_SOURCES must be provided by Phase 5 before running make)
endif
ifeq ($(strip $(COCOTB_MAKEFILES_DIR)),)
$(error COCOTB_MAKEFILES_DIR must be provided by Phase 5 preflight before running make)
endif

COMPILE_ARGS += $(foreach item,$(INCLUDE_DIRS),-I$(item))
COMPILE_ARGS += $(foreach item,$(DEFINE_OVERRIDES),-D$(item))
COMPILE_ARGS += $(foreach item,$(PARAMETER_OVERRIDES),-P$(TOPLEVEL).$(item))
COMPILE_ARGS += $(EXTRA_COMPILE_ARGS)
SIM_ARGS += $(PLUSARGS)
SIM_ARGS += $(EXTRA_SIM_ARGS)

.DEFAULT_GOAL := sim

include $(COCOTB_MAKEFILES_DIR)/Makefile.sim
"""
    summary = {
        "default_toplevel": module_name,
        "default_module": default_test_module,
        "contract_version": MAKEFILE_CONTRACT_VERSION,
        "is_executable_shell": True,
        "phase5_injected_variables": [
            "SIM",
            "TOPLEVEL",
            "MODULE",
            "COCOTB_MAKEFILES_DIR",
            "VERILOG_SOURCES",
            "INCLUDE_DIRS",
            "DEFINE_OVERRIDES",
            "PARAMETER_OVERRIDES",
            "PLUSARGS",
            "WAVES",
            "COCOTB_RESULTS_FILE",
        ],
    }
    return content, summary
