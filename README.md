# cocoverify2

`cocoverify2` is a stage-based, artifact-oriented, LLM-assisted cocotb verification framework.

It exists to replace monolithic "generate one testbench and hope it passes" flows with a staged pipeline that is easier to inspect, debug, and evolve.

## Why this project exists

The short version:

- decouple stimulus / plan from oracle generation to reduce false positives
- preserve ambiguity / assumptions explicitly to reduce false negatives
- keep stage-local artifacts and structured failures to improve diagnosability
- enforce clear phase boundaries so the codebase stays maintainable as the pipeline grows

## Verification Pipeline

The full 8-stage pipeline is:

1. Contract Extraction
2. Test Plan Generation
3. Oracle Generation
4. Testbench Rendering
5. Simulation Execution
6. Failure Classification / Triage
7. Targeted Repair
8. Report / Verdict

## Current Status

README is the project status overview. Detailed design lives in `docs/`, detailed phase history lives in `docs/progress.md`, and generated sample artifacts usually live under `tmp/`. This file should be updated at the end of each phase.

| Phase | Status | Deliverables | Key decisions | Known limitations |
| --- | --- | --- | --- | --- |
| Phase 0 | done | project skeleton, typed models, CLI shell, docs, smoke tests | start artifact-first and keep orchestrator thin | no stage business logic yet |
| Phase 1 | done | `contract.json`, `contract_summary.yaml`, RTL/header parsing, contract CLI stage | fixed the contract artifact first so later stages consume one stable schema | parsing is still heuristic and header-focused |
| Phase 1.1 | done | contract quality patch | timing inference became more conservative, `handshake_groups` was added, weak contracts now degrade `contract_confidence` more clearly | handshake semantics are still heuristic, not proven |
| Phase 2 | done | `test_plan.json`, `test_plan_summary.yaml`, plan CLI stage | plan generation consumes only `contract.json`; it does not re-parse RTL | still rule-based and intentionally conservative |
| Phase 3 | done | `oracle.json`, `oracle_summary.yaml`, oracle CLI stage | oracle is split into protocol / functional / property layers and avoids exact-cycle checks under unknown timing | no render/runtime code yet; functional oracle remains descriptive |
| Phase 4 | done | deterministic cocotb package rendering, `render/metadata.json`, rendered `cocotb_tests/` package, executable Makefile shell | render translates `contract + plan + oracle` artifacts into code without re-inventing semantics | rendered checks still inherit conservative upstream artifacts; render does not strengthen weak oracle semantics |
| Phase 5 | done | `runner_selection.json`, structured `simulation_result.json`, make-mode execution path, cocotb-tools execution path, structured logs and JUnit support | Phase 4 renders the executable Makefile shell and Phase 5 injects execution config, selects the backend, and runs it | default run currently executes the first rendered test module unless `--test-module` is provided |
| Phase 6 | planned | structured failure classification | triage should classify failures by layer with evidence | not started |
| Phase 7 | planned | targeted repair recommendations | repair must be stage-local, not monolithic regeneration | not started |
| Phase 8 | planned | final report and verdict | verdict must combine evidence, ambiguity, and risk | not started |

## Current Implemented Path

- Phases 1-5 are implemented today as the current mainline path: `contract -> plan -> oracle -> render -> run`.
- The implementation on `master` is still a rule-based MVP; it is artifact-oriented and deterministic by default.
- LLM support remains part of the long-term architecture, but it is not yet in the main execution path.
- Recent RTLLM alu artifacts under `tmp/rtllm_eval4/`, `tmp/rtllm_eval4_run/`, and `tmp/rtllm_eval4_edge_run/` show that the Phase 1-5 path can reach real make-mode execution for:
  - `cocotb_tests.test_verified_alu_basic.test_basic_001`
  - `cocotb_tests.test_verified_alu_edge.test_edge_001`

## Current Limitations

- `TestPlan` and `OracleSpec` are still rule-based and conservative; they are designed to preserve ambiguity rather than maximize semantic strength.
- The RTLLM alu smoke success proves execution-path viability and a real Phase 5 happy path, not benchmark-grade semantic oracle quality.
- Default `stage run` currently executes the first rendered test module unless `--test-module` is provided explicitly.
- Real Phase 5 runs require `cocotb`, `cocotb_tools`, `cocotb-config`, and an available simulator such as `iverilog`.

## Completed Phases in Brief

### Phase 0

- Artifacts: package skeleton, typed core models, CLI shell, orchestrator shell, smoke tests
- Why: establish stable project boundaries before stage logic exists
- Limits: no real verification logic yet
- Feeds next phase with: package layout, models, CLI, docs

### Phase 1

- Artifacts: `contract.json`, `contract_summary.yaml`
- Why: fix the contract artifact before any planning/oracle work depends on it
- Limits: RTL parsing is intentionally lightweight and conservative
- Feeds next phase with: `module_name`, `ports`, `parameters`, `timing`, `handshake_groups`, `assumptions`, `ambiguities`

### Phase 1.1

- Patch summary: conservative timing inference, structured `handshake_groups`, stronger `contract_confidence` downgrade for weak contracts
- Why: make the contract more usable for planning without pretending certainty
- Limits: handshake grouping is still name-based
- Feeds next phase with: safer timing classification and structured protocol hints

### Phase 2

- Artifacts: `test_plan.json`, `test_plan_summary.yaml`
- Why: lock a stable plan artifact before any oracle or render logic exists
- Limits: plan generation is rule-based and avoids strong timing claims under `timing=unknown`
- Feeds next phase with: case categories, timing assumptions, observed signals, unresolved items, coverage tags

### Phase 3

- Artifacts: `oracle.json`, `oracle_summary.yaml`
- Why: separate plan/stimulus intent from oracle intent to lower false positives
- Limits: oracle generation is still conservative and avoids exact-cycle checks when timing is weak or unknown
- Feeds next phase with: `protocol_oracles`, `functional_oracles`, `property_oracles`, `TemporalWindow`, `OracleConfidenceSummary`

### Phase 4

- Artifacts: `render/metadata.json`, rendered `cocotb_tests/` package, shared interface/env/oracle/coverage helpers, executable Makefile shell
- Why: render deterministically translates structured artifacts into a maintainable cocotb package without re-deriving contract, plan, or oracle semantics
- Limits: render preserves conservative upstream assumptions; it does not make weak or unresolved oracle semantics stronger
- Feeds next phase with: render metadata, test modules, helper modules, and the executable Makefile shell used by Phase 5

### Phase 5

- Artifacts: `runner_selection.json`, `simulation_result.json`, structured logs, optional JUnit output, make and cocotb-tools execution paths
- Why: execute render artifacts through an explicit runner-selection layer while keeping execution concerns separate from triage and verdicting
- Limits: the current mainline remains rule-based, default execution selects the first rendered test module unless overridden, and smoke success should not be read as strong semantic validation
- Feeds next phase with: execution status, selected backend/mode, structured logs, discovered/executed test lists, and JUnit metadata

## Docs Guide / Where to Look Next

If you are re-entering this repo later, start here:

- architecture and rationale: `docs/architecture.md`
- phase breakdown and MVP scope: `docs/mvp_plan.md`
- per-phase log / current progress journal: `docs/progress.md`
- stage entry points: `src/cocoverify2/stages/`
- shared schemas: `src/cocoverify2/core/models.py`
- CLI glue: `src/cocoverify2/cli.py`
- generated sample artifacts: `tmp/`
- small runnable fixtures: `tests/fixtures/`

## Minimal Run Commands

Install:

```bash
pip install -e .
pip install -e .[dev]
```

Run tests:

```bash
pytest -q
```

CLI help:

```bash
cocoverify2 --help
cocoverify2 stage --help
```

Typical stage commands supported today:

```bash
cocoverify2 stage contract --rtl path/to/dut.v --out-dir out
cocoverify2 stage plan --contract out/contract/contract.json --out-dir out
cocoverify2 stage oracle --contract out/contract/contract.json --plan out/plan/test_plan.json --out-dir out
cocoverify2 stage render --contract out/contract/contract.json --plan out/plan/test_plan.json --oracle out/oracle/oracle.json --out-dir out
cocoverify2 stage run --render out/render/metadata.json --out-dir run_out
```

Environment note for real Phase 5 execution:

- `stage run` needs `cocotb`, `cocotb_tools`, `cocotb-config`, and a simulator/runtime pair that can actually execute the rendered package.

## Project Status Note

This README is intentionally a status overview and phase checkpoint page, not the full design spec.

- use `docs/architecture.md` for the big-picture design
- use `docs/mvp_plan.md` for the intended phase roadmap
- use `docs/progress.md` for the per-phase log
- use `tmp/` and test fixtures for concrete artifact examples

When a new phase lands, update this README and the progress log together.
