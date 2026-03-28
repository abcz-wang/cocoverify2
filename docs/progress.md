# cocoverify2 Progress Log

This file is the per-phase progress journal.

- `README.md` is the short project status overview
- `docs/architecture.md` is the design document
- `docs/mvp_plan.md` is the original phase roadmap
- this file records what each phase actually delivered, key decisions, and current limits

## Phase 0 - Project Skeleton

- Status: done
- Deliverables:
  - installable package skeleton
  - typed core models and enums
  - CLI shell
  - thin orchestrator shell
  - smoke tests
  - in-repo design docs
- Key decisions:
  - artifact-oriented pipeline from day one
  - thin orchestrator, stage-owned business logic
  - typed artifacts before stage behavior
- Known limitations:
  - no stage business logic
  - no RTL parsing yet
  - no cocotb generation or runner logic
- Output to next phase:
  - stable package layout, CLI shape, and model foundation

## Phase 1 - Contract Extraction

- Status: done
- Deliverables:
  - `contract.json`
  - `contract_summary.yaml`
  - lightweight RTL header parsing
  - parameter / port extraction
  - basic clock / reset / handshake detection
  - `stage contract` CLI path
- Key decisions:
  - fix the contract artifact before plan/oracle work
  - prefer conservative parsing over optimistic reconstruction
  - preserve ambiguities instead of hiding them
- Known limitations:
  - parser is intentionally lightweight
  - not a full SystemVerilog front-end
  - non-ANSI headers remain weakly supported
- Output to next phase:
  - stable contract schema consumed by planning

## Phase 1.1 - Contract Quality Patch

- Status: done
- Deliverables:
  - more conservative timing inference
  - structured `handshake_groups`
  - stronger `contract_confidence` downgrade for weak contracts
- Key decisions:
  - prefer `unknown` over incorrect `comb`
  - keep legacy `handshake_signals` only as a flattened compatibility view
  - make weak contracts visibly weak in the artifact itself
- Known limitations:
  - handshake grouping is still heuristic
  - timing remains coarse-grained
- Output to next phase:
  - safer protocol hints and better weak-contract detection for planning

## Phase 2 - Test Plan Generation

- Status: done
- Deliverables:
  - `test_plan.json`
  - `test_plan_summary.yaml`
  - rule-based conservative `TestPlanGenerator`
  - `stage plan` CLI path
- Key decisions:
  - plan consumes only `contract.json`
  - do not re-parse RTL in Phase 2
  - for `timing=unknown`, avoid fixed-latency case design
  - use `handshake_groups` as hints, not protocol truth
- Known limitations:
  - still rule-based
  - no metamorphic or advanced semantic planning yet
  - no LLM assistance yet
- Output to next phase:
  - structured plan cases, timing assumptions, observed signals, coverage tags, unresolved items

## Phase 3 - Oracle Generation

- Status: done
- Deliverables:
  - `oracle.json`
  - `oracle_summary.yaml`
  - structured `OracleSpec`, `OracleCase`, `OracleCheck`, `TemporalWindow`, `OracleConfidenceSummary`
  - rule-based conservative `OracleGenerator`
  - `stage oracle` CLI path
- Key decisions:
  - consume only `contract.json + test_plan.json`
  - keep protocol / functional / property oracle layers separate
  - avoid exact-cycle checks when timing is weak or unknown
  - emit unresolved-safe or empty functional oracle cases instead of guessing values
- Known limitations:
  - still descriptive / heuristic, not reference-model-grade
  - no cocotb code generation yet
  - confidence scoring is simple and conservative
- Output to next phase:
  - render-ready structured oracle checks with explicit temporal windows and strictness

## Phase 4 - Testbench Rendering

- Status: done
- Deliverables:
  - deterministic render pipeline from `contract.json + test_plan.json + oracle.json`
  - `render/metadata.json`
  - rendered `cocotb_tests/` package
  - shared interface / env / oracle / coverage helpers
  - executable Makefile shell
  - `stage render` CLI path
- Key decisions:
  - render only translates structured artifacts; it does not re-parse RTL or re-invent oracle semantics
  - keep rendering deterministic and template-driven
  - Phase 4 renders the executable Makefile shell, while Phase 5 injects execution config and runs it
  - preserve unresolved items and conservative temporal semantics instead of strengthening weak artifacts
- Known limitations:
  - render quality is bounded by the upstream rule-based `TestPlan` and `OracleSpec`
  - rendered packages may contain multiple test modules, but Phase 4 does not decide multi-module execution policy
  - helper structure is ready for execution, not yet for benchmark-grade semantic confidence claims
- Output to next phase:
  - render metadata, generated helper/test files, executable Makefile shell
- Evidence:
  - `tmp/rtllm_eval4/render/metadata.json`
  - render output for RTLLM alu includes `test_verified_alu_basic.py`, `test_verified_alu_edge.py`, helper modules, and an executable Makefile shell

## Phase 5 - Simulation Execution

- Status: done
- Deliverables:
  - runner selection artifact (`runner_selection.json`)
  - structured execution result artifact (`simulation_result.json`)
  - make-mode execution path
  - cocotb-tools execution path
  - structured result parsing
  - logs / JUnit artifacts
  - `stage run` CLI path
- Key decisions:
  - execution consumes render artifacts and execution config only; it does not modify rendered test semantics
  - runner selection is explicit and persisted so fallback behavior is inspectable
  - make-mode contract is split cleanly: Phase 4 renders the executable shell, Phase 5 injects `SIM / TOPLEVEL / MODULE / VERILOG_SOURCES / include dirs / params / defines` and executes it
  - execution status remains coarse-grained in Phase 5; detailed fault attribution is deferred to Phase 6
- Known limitations:
  - default run currently selects only the first rendered test module unless `--test-module` is provided
  - oracle behavior remains conservative / descriptive because the mainline is still rule-based
  - LLM is still not integrated into the main execution path
  - successful benchmark smoke runs validate execution-path viability, not benchmark-grade semantic oracle quality
- Output to next phase:
  - selected runner metadata, structured execution result, logs, JUnit evidence, discovered/executed test lists
- Evidence:
  - upstream RTLLM alu artifacts:
    - `tmp/rtllm_eval4/contract/contract_summary.yaml`
    - `tmp/rtllm_eval4/plan/test_plan_summary.yaml`
    - `tmp/rtllm_eval4/oracle/oracle_summary.yaml`
    - `tmp/rtllm_eval4/render/metadata.json`
  - real make-mode execution artifacts:
    - `tmp/rtllm_eval4_run/run/simulation_result.json`
    - `tmp/rtllm_eval4_run/run/junit/results.xml`
    - `tmp/rtllm_eval4_edge_run/run/simulation_result.json`
    - `tmp/rtllm_eval4_edge_run/run/junit/results.xml`
  - interpretation:
    - `cocotb_tests.test_verified_alu_basic.test_basic_001` passed in make mode when run explicitly
    - `cocotb_tests.test_verified_alu_edge.test_edge_001` passed in make mode when run explicitly
    - this validates the real Phase 5 execution path, but not strong semantic oracle quality

## Phase 6 - Failure Classification / Triage

- Status: planned
- Intended deliverables:
  - structured failure categories
  - evidence-backed triage artifact

## Phase 7 - Targeted Repair

- Status: planned
- Intended deliverables:
  - stage-local repair recommendations
  - no monolithic full-regeneration fallback by default

## Phase 8 - Report / Verdict

- Status: planned
- Intended deliverables:
  - final report artifact
  - verdict synthesis with confidence and risk

## Updating Rule

When a phase lands:

1. update `README.md` with the new top-level status
2. append or revise this file with the concrete deliverables / decisions / limits
3. keep planned phases clearly marked as planned until code actually lands
