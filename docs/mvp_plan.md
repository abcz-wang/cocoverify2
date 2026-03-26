# cocoverify2 MVP Plan

## Phase Breakdown

### Phase 0: Project Skeleton

Deliverables:

- in-repo design documentation
- installable package skeleton
- core pydantic models
- CLI skeleton
- orchestrator shell
- utility foundations for logging and file operations
- smoke tests for models, CLI, and minimal integration import path

Non-goals:

- no stage business logic
- no real RTL parsing
- no real cocotb generation
- no real runner implementation
- no triage or repair execution

### Phase 1: Contract Extraction MVP

Target:

- basic single-file RTL parsing
- port and parameter extraction
- initial `DUTContract` artifact dump

### Phase 2: Test Plan MVP

Target:

- structured test plan generation with schema validation
- enforce reset/basic/edge/back-to-back coverage categories

### Phase 3: Oracle MVP

Target:

- protocol/property/simple functional oracle generation
- unresolved behavior preserved explicitly

### Phase 4: Rendering MVP

Target:

- generate multiple cocotb test files
- split helper/interface/oracle files
- emit render metadata

### Phase 5: Execution MVP

Target:

- minimal cocotb-tools runner support
- structured result parsing
- build/test log persistence

### Phase 6: Triage MVP

Target:

- classify a minimum set of failure categories
- attach evidence and confidence

### Phase 7: Repair MVP

Target:

- stage-targeted repair recommendations only
- no multi-round automated repair loop yet

### Phase 8: Reporting MVP

Target:

- final report and verdict generation
- support `pass`, `fail`, `suspicious`, and `inconclusive`

## MVP Acceptance Criteria

The MVP must eventually support:

1. parsing DUT and basic interface information
2. generating a contract artifact
3. generating a structured test plan
4. generating a minimal oracle artifact
5. rendering multiple cocotb tests
6. running cocotb
7. emitting structured results
8. distinguishing `pass`, `fail`, `suspicious`, and `inconclusive`
9. mapping primary pass + independent confirmation fail to `suspicious`
10. at least three unit tests and one minimal integration test

## Phase 0 Deliverables Mapping

Phase 0 specifically implements:

- `docs/architecture.md`
- `docs/mvp_plan.md`
- package skeleton under `src/cocoverify2/`
- typed models in `core/models.py`
- enums and literals in `core/types.py`
- structured exceptions in `core/errors.py`
- framework config models in `core/config.py`
- orchestrator shell in `core/orchestrator.py`
- CLI skeleton in `cli.py`
- logging/file utilities in `utils/`
- smoke tests under `tests/`
