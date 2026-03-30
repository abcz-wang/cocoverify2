# cocoverify2 Progress Log

This file is the per-phase implementation journal.

- `README.md` is the short project status overview
- `docs/architecture.md` is the design document
- `docs/mvp_plan.md` is the original roadmap
- this file records what each phase actually shipped on `master`

Current supported default path on `master`:

`contract -> plan(hybrid optional) -> oracle(hybrid optional) -> render -> run -> triage`

Important boundary notes:

- deterministic render remains mandatory
- `fill` exists today, but only as an experimental post-render adjunct
- `verify`, `repair`, and `report` are still not implemented

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
  - optional spec text and interface-hint ingestion
- Key decisions:
  - fix the contract artifact before plan / oracle work
  - prefer conservative parsing over optimistic reconstruction
  - preserve ambiguities instead of hiding them
- Known limitations:
  - parser is intentionally lightweight
  - not a full SystemVerilog front-end
  - non-ANSI headers remain only partially recoverable
  - interface and timing inference remain heuristic
- Output to next phase:
  - stable contract schema consumed by planning
- Evidence:
  - `tests/test_contract_extractor.py`
  - `tests/test_rtl_parser.py`

## Phase 1.1 - Contract Quality Patch

- Status: done
- Deliverables:
  - more conservative timing inference
  - structured `handshake_groups`
  - stronger `contract_confidence` downgrade for weak contracts
  - improved recovery for weak or partially legacy interfaces
- Key decisions:
  - prefer `unknown` over incorrect `comb`
  - keep legacy `handshake_signals` only as a flattened compatibility view
  - make weak contracts visibly weak in the artifact itself
- Known limitations:
  - handshake grouping is still heuristic
  - timing remains coarse-grained
  - weak contracts still constrain later-stage semantic strength
- Output to next phase:
  - safer protocol hints and better weak-contract detection for planning
- Evidence:
  - `tests/test_contract_extractor.py`
  - `tests/test_models.py`

## Phase 2 - Test Plan Generation

- Status: done
- Deliverables:
  - `test_plan.json`
  - `test_plan_summary.yaml`
  - conservative rule-based `TestPlanGenerator`
  - hybrid LLM augmentation path for structured case enrichment / addition
  - persisted LLM artifacts in hybrid mode:
    - `llm_request.json`
    - `llm_response_raw.txt`
    - `llm_response_parsed.json`
    - `llm_response_normalized.json`
    - `llm_merge_report.json`
  - richer structured case fields such as `scenario_kind`, `stimulus_program`, `semantic_tags`, `execution_policy`, and `defer_reason`
  - `stage plan` CLI path
- Key decisions:
  - plan consumes `contract.json`; it does not re-parse RTL
  - hybrid mode is append / enrich / validate / merge over structured artifacts, not free-form testbench code generation
  - weak contracts are allowed to downgrade or defer cases instead of faking determinism
  - ambiguity is preserved in unresolved items and execution policy hints
- Known limitations:
  - complex sequential, FSM, metamorphic, and reference-model-lite scenarios still need deeper structured support
  - hybrid planning quality is bounded by schema validation and deterministic executability downstream
  - benchmark quality still depends more on executable scenario depth than on prompt prose
- Output to next phase:
  - structured plan cases, timing assumptions, observed signals, semantic tags, unresolved items, execution-policy hints, and optional hybrid merge artifacts
- Evidence:
  - `tests/test_test_plan_generator.py`
  - `tests/test_llm_validators.py`

## Phase 3 - Oracle Generation

- Status: done
- Deliverables:
  - `oracle.json`
  - `oracle_summary.yaml`
  - structured `OracleSpec`, `OracleCase`, `OracleCheck`, `TemporalWindow`, and `OracleConfidenceSummary`
  - artifact-level signal policy support:
    - `AssertionStrength`
    - `DefinednessMode`
    - `SignalAssertionPolicy`
  - conservative rule-based `OracleGenerator`
  - hybrid LLM augmentation path for structured oracle enrichment / addition
  - persisted hybrid artifacts analogous to Phase 2 merge outputs
  - `stage oracle` CLI path
- Key decisions:
  - consume only `contract.json + test_plan.json`
  - keep protocol / functional / property oracle layers separate
  - preserve ambiguity in temporal windows and signal policies instead of inventing exact-cycle certainty
  - hybrid mode stays at the structured-check layer and does not bypass the schema
- Known limitations:
  - functional strength remains bounded by upstream scenario executability
  - definedness and unknown-handling policy still needs calibration against actual stimulus, settle windows, and observability
  - hybrid oracle quality is constrained by validation and conservative merge rules
- Output to next phase:
  - render-ready structured checks, temporal windows, signal policies, and optional hybrid merge artifacts
- Evidence:
  - `tests/test_oracle_generator.py`
  - `tests/test_llm_validators.py`

## Phase 4 - Testbench Rendering

- Status: done
- Deliverables:
  - deterministic render pipeline from `contract.json + test_plan.json + oracle.json`
  - `render/metadata.json`
  - rendered `cocotb_tests/` package
  - shared interface / env / oracle / coverage / runtime helper modules
  - executable Makefile shell
  - render metadata for generated files, test modules, template inventory, confidence, and warnings
  - structured TODO block metadata to support optional post-render fill
  - `stage render` CLI path
- Key decisions:
  - render only translates structured artifacts; it does not re-parse RTL or re-invent oracle semantics
  - deterministic render is mandatory for the benchmark mainline
  - upstream hybrid artifacts may influence rendered structure, but rendering itself stays deterministic
  - TODO block metadata may be emitted, but benchmark mainline still remains `render -> run -> triage`
- Known limitations:
  - richer scenario kinds still need more deterministic runtime helper depth
  - render quality is bounded by plan / oracle artifact strength
  - TODO metadata is not a license to move code-level generation into the benchmark default path
- Output to next phase:
  - render metadata, generated helper / test files, executable Makefile shell, and optional fill metadata
- Evidence:
  - `tests/test_tb_renderer.py`
  - `tests/test_template_loader.py`

## Experimental Adjunct - Post-render TODO Fill

- Status: experimental
- Deliverables:
  - `stage fill` CLI path
  - `fill/metadata.json`
  - `fill_report.json`
  - `repair_report.json`
  - bounded, block-scoped fill for render-emitted `stimulus` and `oracle_check` TODO blocks
  - compile-time validation and one bounded repair pass
- Key decisions:
  - fill is post-render and block-local
  - fill is intentionally fenced off from the official benchmark mainline
  - fill is not the same thing as planned Phase 7 targeted repair
- Known limitations:
  - this path introduces code-level generation and therefore must remain experimental
  - correctness is bounded by block-local validation plus compile checks, not full benchmark semantics
  - it must not be wired into the default RTLLM benchmark flow
- Evidence:
  - `tests/test_todo_fill.py`

## Phase 5 - Simulation Execution

- Status: done
- Deliverables:
  - runner selection artifact (`runner_selection.json`)
  - structured execution result artifact (`simulation_result.json`)
  - make-mode execution path
  - cocotb-tools execution path
  - explicit mode selection and inspectable fallback recording
  - structured result parsing
  - logs / JUnit artifacts
  - `stage run` CLI path
- Key decisions:
  - execution consumes render artifacts and execution config only; it does not modify rendered test semantics
  - runner selection is explicit and persisted so fallback behavior is inspectable
  - execution is kept separate from triage and later repair / verdict decisions
  - make-mode remains a first-class path for real benchmark execution
- Known limitations:
  - default run currently selects only the first rendered test module unless `--test-module` is provided
  - simulator and cocotb runtime availability remain external prerequisites
  - a Phase 5 success still needs Phase 6 interpretation; execution success alone is not a final benchmark verdict
- Output to next phase:
  - selected runner metadata, structured execution result, logs, JUnit evidence, discovered / executed test lists, and fallback metadata
- Evidence:
  - `tests/test_simulator_runner.py`
  - `tests/test_result_parser.py`

## Phase 6 - Failure Classification / Triage

- Status: done
- Deliverables:
  - `triage.json`
  - `triage_summary.yaml`
  - `TriageResult` model
  - evidence-backed triage stage over Phase 5 artifacts
  - conservative classification for outcomes including:
    - `no_failure`
    - `environment_error`
    - `artifact_contract_error`
    - `configuration_error`
    - `compile_error`
    - `elaboration_error`
    - `timeout_error`
    - `runtime_test_failure`
    - `insufficient_stimulus`
  - `stage triage` CLI path
- Key decisions:
  - triage consumes Phase 5 artifacts only; it does not regenerate upstream stages
  - classification stays conservative when render confidence is weak or ambiguity remains unresolved
  - internal artifact-contract failures should not be mislabeled as generic environment failures
- Known limitations:
  - triage is heuristic evidence classification, not formal proof of root cause
  - triage does not yet trigger a targeted repair loop
  - benchmark interpretation still requires human review of false-positive / insufficient-stimulus patterns
- Output to next phase:
  - structured failure categories, evidence, suspected layer, and conservative confidence for targeted repair and later reporting
- Evidence:
  - `tests/test_triage.py`

## Auxiliary Tooling - RTLLM Batch Evaluation

- Status: shipped auxiliary tooling
- Deliverables:
  - `cocoverify2-rtllm-batch` CLI entry point
  - batch harness over the current mainline pipeline
  - per-task artifact roots plus aggregate:
    - `summary.json`
    - `summary.csv`
    - `summary.md`
  - aggregate metrics for fallback behavior, triage categories, rendered-module success, and assertion-strength distribution
  - benchmark input filtering that excludes generation leakage from files such as `reference.dat`, `reference.txt`, `testbench.v`, and `testbench.sv`
- Key decisions:
  - batch harness runs the current mainline path rather than inventing a separate benchmark-only pipeline
  - benchmark fairness rules apply at input resolution time
  - interface hints may be extracted from structured interface-only slices of spec text instead of duplicating the full spec into interface hints
- Known limitations:
  - the harness is not the same as the planned framework `report` stage
  - current quality work is concentrated on definedness calibration and richer deterministic support for complex scenario kinds
  - benchmark quality must be judged by all rendered modules and false positives, not by one passing module
- Evidence:
  - `tests/test_rtllm_batch.py`

## Phase 7 - Targeted Repair

- Status: planned
- Intended deliverables:
  - stage-local repair recommendations driven by triage
  - bounded remediation loops instead of monolithic regeneration
- Clarification:
  - planned Phase 7 repair is distinct from the current experimental `fill` adjunct

## Phase 8 - Report / Verdict

- Status: planned
- Intended deliverables:
  - final report artifact
  - verdict synthesis with confidence and risk
  - regression-friendly summary across tasks / runs
- Clarification:
  - RTLLM batch summaries exist today, but the framework-level `report` stage is still not implemented

## Updating Rule

When a major capability lands:

1. update `README.md` with the top-level status and current supported path
2. revise this file with concrete deliverables, key decisions, and current limitations
3. keep planned phases clearly marked as planned until code actually ships
4. keep experimental adjuncts explicitly labeled as experimental so they do not get mistaken for mainline stages
