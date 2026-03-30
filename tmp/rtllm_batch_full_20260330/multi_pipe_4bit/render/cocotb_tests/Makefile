# Phase 4 render artifact for verified_multi_pipe
# Executable Makefile shell: Phase 5 injects simulator/config variables and runs it.
CV2_MAKEFILE_CONTRACT := executable-shell-v1

TOPLEVEL_LANG ?= verilog
SIM ?= icarus
TOPLEVEL ?= verified_multi_pipe
MODULE ?= test_verified_multi_pipe_basic

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
