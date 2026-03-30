# cocoverify2

`cocoverify2` is a stage-based, artifact-oriented cocotb verification framework for Verilog/SystemVerilog DUTs.

The project intentionally avoids the "ask an LLM to write one full testbench and hope it works" pattern. Instead, it keeps semantics in structured artifacts, keeps rendering deterministic, and preserves ambiguity instead of inventing confidence.

## Why this project exists

The short version:

- decouple stimulus / plan from oracle generation to reduce false positives
- preserve ambiguity / assumptions explicitly to reduce false negatives
- keep stage-local artifacts and structured failures to improve diagnosability
- enforce clear phase boundaries so the codebase stays maintainable as the pipeline grows

## Verification Pipeline

The long-term 8-stage pipeline is:

1. Contract Extraction
2. Test Plan Generation
3. Oracle Generation
4. Testbench Rendering
5. Simulation Execution
6. Failure Classification / Triage
7. Targeted Repair
8. Report / Verdict

## Current Mainline

The supported default path on `master` today is:

`contract -> plan(hybrid optional) -> oracle(hybrid optional) -> render -> run -> triage`

Important architecture notes:

- `plan` and `oracle` support both `rule_based` and `hybrid` generation modes.
- `render` remains deterministic even when upstream artifacts were LLM-enriched.
- `fill` exists as an experimental post-render adjunct, but it is not the benchmark default path.
- `verify`, `repair`, and `report` are not implemented yet, even though the long-term pipeline reserves those stages.

## Current Status

`README.md` is the short status overview. Detailed design lives in `docs/`, detailed implementation history lives in `docs/progress.md`, and generated sample artifacts usually live under `tmp/`.

| Phase | Status | Deliverables | Key decisions | Known limitations |
| --- | --- | --- | --- | --- |
| Phase 0 | done | project skeleton, typed models, CLI shell, docs, smoke tests | start artifact-first and keep orchestrator thin | no stage business logic yet |
| Phase 1 | done | `contract.json`, `contract_summary.yaml`, RTL/header parsing, contract CLI stage | fix the contract artifact first so later stages consume one stable schema | parsing remains heuristic and lightweight |
| Phase 1.1 | done | contract quality patch, conservative timing inference, `handshake_groups`, clearer confidence downgrade | prefer `unknown` over incorrect certainty | handshake semantics are still heuristic |
| Phase 2 | done | `test_plan.json`, `test_plan_summary.yaml`, rule-based planning, optional hybrid LLM augmentation artifacts | hybrid mode is validate-and-merge over structured cases, not free-form codegen | richer complex sequential / metamorphic / reference-model-lite scenarios still need deeper structured support |
| Phase 3 | done | `oracle.json`, `oracle_summary.yaml`, rule-based oracle generation, optional hybrid LLM augmentation artifacts, signal assertion policies | keep protocol / functional / property layers separate and preserve ambiguity in signal policies | definedness / unknown policy still needs calibration against real stimulus and settle behavior |
| Phase 4 | done | deterministic `render/metadata.json`, rendered `cocotb_tests/` package, runtime helpers, executable Makefile shell, optional TODO metadata for experimental fill | rendering stays deterministic and does not let LLM write benchmark mainline test logic | some complex scenario kinds still need stronger deterministic execution support |
| Phase 5 | done | `runner_selection.json`, `simulation_result.json`, structured logs, JUnit support, explicit backend selection and fallback | execution is inspectable and separate from render / triage | default run still executes the first rendered test module unless `--test-module` is provided |
| Phase 6 | done | `triage.json`, `triage_summary.yaml`, evidence-backed failure classification, `stage triage` CLI path | triage consumes Phase 5 artifacts only and stays conservative about weak upstream evidence | classification is heuristic and does not yet trigger a repair loop |
| Phase 7 | planned | targeted repair recommendations | repair should be driven by triage and stay stage-local | not implemented |
| Phase 8 | planned | final report / verdict stage | report should synthesize evidence, ambiguity, and risk | not implemented |

## Current Capabilities

### Mainline pipeline

- `stage contract`, `stage plan`, `stage oracle`, `stage render`, `stage run`, and `stage triage` are implemented in the CLI.
- `plan` and `oracle` hybrid mode write structured `llm_request.json`, raw/parsed/normalized responses, and merge reports, and they fall back conservatively when the LLM output is invalid.
- `render` emits deterministic cocotb packages plus policy-aware runtime helpers and metadata that make downstream execution and triage inspectable.
- `triage` classifies success and common failure families such as environment, artifact-contract, configuration, compile, elaboration, runtime-test, timeout, and insufficient-stimulus outcomes.

### Experimental and auxiliary paths

- `stage fill` is an experimental, bounded post-render TODO fill path. It is intentionally not the benchmark default path and is not a substitute for Phase 7 repair.
- `cocoverify2-rtllm-batch` runs the current mainline pipeline across RTLLM benchmark tasks and emits `summary.json`, `summary.csv`, and `summary.md`.
- QiMeng-Agent integration lives in `QiMeng-Agent/qimeng_agent/tools/cocoverify_verilog.py`.

## Current Limitations and Active Work

- `verify`, `repair`, and `report` remain unimplemented top-level orchestration stages.
- The main quality bottleneck is no longer basic schema adherence. Current work is concentrated on aligning definedness policy with stimulus, settle windows, and observability instead of turning every weakly-constrained signal into a generic hard failure.
- Complex sequential / FSM / protocol / metamorphic / reference-model-lite scenarios still need stronger structured execution support in deterministic templates and runtime helpers.
- Benchmark quality should be judged by all rendered test modules, false positives, and triage mix, not just by "at least one module ran successfully".
- `fill` remains experimental and must not be treated as the official benchmark path.

## Docs Guide

If you are re-entering this repo later, start here:

- architecture and rationale: `docs/architecture.md`
- phase-by-phase implementation log: `docs/progress.md`
- original roadmap and MVP framing: `docs/mvp_plan.md`
- stage entry points: `src/cocoverify2/stages/`
- shared schemas and artifacts: `src/cocoverify2/core/models.py`
- CLI glue: `src/cocoverify2/cli.py`
- LLM schema / prompt / validation layer: `src/cocoverify2/llm/`
- RTLLM batch harness: `src/cocoverify2/eval/rtllm_batch.py`
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
cocoverify2-rtllm-batch --help
```

Typical mainline stage commands supported today:

```bash
cocoverify2 stage contract --rtl path/to/dut.v --out-dir out
cocoverify2 stage plan --contract out/contract/contract.json --out-dir out --generation-mode hybrid
cocoverify2 stage oracle --contract out/contract/contract.json --plan out/plan/test_plan.json --out-dir out --generation-mode hybrid
cocoverify2 stage render --contract out/contract/contract.json --plan out/plan/test_plan.json --oracle out/oracle/oracle.json --out-dir out
cocoverify2 stage run --render out/render/metadata.json --out-dir run_out
cocoverify2 stage triage --in-dir run_out --out-dir triage_out
```

Experimental post-render fill:

```bash
cocoverify2 stage fill --render out/render/metadata.json --out-dir fill_out
```

Typical RTLLM batch invocation:

```bash
cocoverify2-rtllm-batch --root path/to/RTLLM_for_ivl --out-dir tmp/rtllm_batch_run --generation-mode hybrid
```

Environment notes:

- `stage run` needs `cocotb`, `cocotb_tools`, `cocotb-config`, and an available simulator such as `iverilog`.
- Hybrid `plan` / `oracle` mode uses an OpenAI-compatible endpoint configured through `COCOVERIFY_LLM_*` environment variables or `--llm-*` CLI overrides.
- The current LLM client supports `provider=openai` only.

## Project Status Note

This README is intentionally a status overview and phase checkpoint page, not the full design spec.

- use `docs/architecture.md` for the big-picture design
- use `docs/progress.md` for the shipped implementation history
- use `docs/mvp_plan.md` for the original roadmap
- use `tmp/` and the tests for concrete artifact and behavior examples

When a new phase lands, update this README and the progress log together.
