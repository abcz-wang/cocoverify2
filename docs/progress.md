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

- Status: planned
- Intended deliverables:
  - cocotb package rendering from contract + plan + oracle artifacts
  - multiple test files and shared helpers
  - render metadata
- Current next-step focus:
  - translate artifacts faithfully without re-inventing semantics

## Phase 5 - Simulation Execution

- Status: planned
- Intended deliverables:
  - runner abstraction
  - structured build / test result artifacts
  - basic cocotb execution support

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
