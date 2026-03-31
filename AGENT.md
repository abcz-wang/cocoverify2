# AGENT.md

## Stable Rules
- cocoverify2 is a stage-based, artifact-oriented cocotb verification framework.
- Preserve the current architecture unless the task explicitly asks for redesign.
- Prefer small, contract-preserving changes over broad refactors.
- Distinguish clearly between current implementation, future plan, and design contract.
- Trust `docs/architecture.md`, current code, and tests first; use `tmp/` artifacts as evidence, not as design truth.

## Current Mainline
- The supported default path today is:
  - `contract -> plan(hybrid optional) -> oracle(hybrid optional) -> render -> run -> triage`
- Phase 1-6 are implemented.
- Phase 7 (`repair`) and Phase 8 (`report/verdict`) are not fully implemented yet.
- `plan` and `oracle` hybrid modes are part of the real mainline.
- `render` must remain deterministic even when upstream artifacts are LLM-enriched.
- `fill` exists only as an experimental post-render adjunct, not the benchmark default path.

## Phase Boundaries
- Phase 1 extracts `DUTContract`.
- Phase 2 generates `TestPlan`.
- Phase 3 generates `OracleSpec`.
- Phase 4 renders deterministic cocotb artifacts.
- Phase 5 executes rendered test modules and writes structured run artifacts.
- Phase 6 classifies failures from Phase 5 evidence only.
- Do not mix planning, oracle, rendering, execution, and repair logic in one place.
- Do not let LLM freely generate benchmark mainline cocotb test files.

## Validation Boundary
- Distinguish TB validation from candidate DUT evaluation.
- TB validation should use a trusted golden DUT.
- Candidate DUT evaluation should use an already validated TB artifact.
- Do not use benchmark `testbench.v`, `reference.dat`, or golden outputs as generation input.
- Golden DUT use for TB validation is acceptable; benchmark leakage into generation is not.

## Deterministic Mainline
- Important verification meaning must not depend on experimental TODO fill.
- Do not leave critical semantics only in TODO comments with `pass`.
- Strengthen deterministic mainline plan/oracle/render/runtime first.
- Keep ambiguity explicit when the contract/spec does not justify stronger claims.

## Multi-Module Execution
- Benchmark-quality evaluation must consider all rendered test modules, not only one module.
- Do not treat “one module passed” as proof that the task passed.
- Report clearly whether all rendered modules or only a subset were executed.

## Testing Expectations
- Do not rely only on happy-path or file-exists tests.
- Tests must check phase contracts, not only superficial artifact presence.
- Add regression tests for each meaningful contract bug you fix.
- For execution paths, test both runner selection and backend readiness.
- When changing semantic families or runtime checks, prove the semantics survive `plan -> oracle -> render -> run`.

## Current Working Direction
- Current quality work is focused on richer stimulus, stronger oracle semantics, and deterministic executable checks.
- Current closure work is focused on Phase 7/8:
  - targeted repair planning
  - verification/report loop
  - golden-DUT-based TB validation
- Follow:
  - `docs/architecture.md`
  - `docs/progress.md`
  - `docs/phase7_phase8_closed_loop_plan_20260331.md`
