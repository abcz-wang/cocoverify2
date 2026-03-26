# cocoverify2 Architecture

## 1. Goal and Positioning

`cocoverify2` is a standalone, stage-based LLM-assisted cocotb verification framework.
It replaces the old monolithic `cocotbverify_v1` approach with a structured artifact pipeline:

1. Contract Extraction
2. Test Plan Generation
3. Oracle Generation
4. Testbench Rendering
5. Simulation Execution
6. Failure Classification / Triage
7. Targeted Repair
8. Report / Verdict

The primary goals are:

- reduce false positives by separating stimulus and oracle generation
- reduce false negatives by exposing ambiguity and infrastructure assumptions explicitly
- improve diagnosability with stage-local artifacts and structured failures
- improve maintainability with clear stage boundaries and typed interfaces

## 2. High-Level Design

The framework is organized as an artifact-oriented pipeline with a thin orchestrator.
The orchestrator only sequences stages, persists intermediate results, and coordinates repair.
Stage implementations own the business logic.

Recommended package layout:

```text
cocoverify2/
  docs/
  src/cocoverify2/
    cli.py
    core/
    stages/
    parsers/
    llm/
    cocotbgen/
    execution/
    checkers/
    utils/
  tests/
```

## 3. Core Modules and Responsibilities

### `core/`

- `models.py`: typed pydantic models for stage inputs and outputs
- `types.py`: enums and common literals for verdicts, stages, and categories
- `errors.py`: structured framework exceptions
- `config.py`: runtime configuration models
- `orchestrator.py`: thin verification pipeline coordinator

### `stages/`

- `contract_extractor.py`: derive `DUTContract` from RTL, task description, spec, and optional golden artifacts
- `test_plan_generator.py`: create structured `TestPlan` before any code generation
- `oracle_generator.py`: create protocol, functional, and property oracle artifacts
- `tb_renderer.py`: render structured artifacts into a cocotb package
- `simulator_runner.py`: coordinate runner selection and execution
- `triage.py`: turn simulation results into structured failure classification
- `repair.py`: recommend targeted stage-local repairs
- `report.py`: produce final verdicts and reports

### `parsers/`

- `rtl_parser.py`: parse single-file RTL, source lists, and filelists
- `port_parser.py`: extract and normalize port metadata
- `parameter_parser.py`: extract parameters and defaults
- `golden_interface_parser.py`: import golden module/port definitions

### `llm/`

- `client.py`: only place that talks to the LLM backend
- `prompts.py`: centralized prompt text and templates
- `schemas.py`: stage-local structured output schemas
- `validators.py`: schema validation and semantic validation helpers

### `cocotbgen/`

- `interface.py`, `env.py`, `driver.py`, `monitor.py`, `scoreboard.py`, `coverage.py`
- `templates/` stores rendering fragments and reusable code blocks

### `execution/`

- `runner_base.py`: runner abstraction
- `cocotb_runner.py`: cocotb-tools runner support
- `make_runner.py`: Makefile execution support
- `result_parser.py`: junit/log metadata parsing

### `checkers/`

- `oracle_consistency.py`
- `stimulus_diversity.py`
- `protocol_checker.py`
- `failure_classifier.py`

### `utils/`

- `files.py`, `json_utils.py`, `logging.py`, `subprocess.py`, `timing.py`

## 4. Stage Inputs and Outputs

### Stage 1: Contract Extraction

Inputs:

- RTL source(s)
- task description
- optional spec
- optional golden testbench or interface

Output:

- `DUTContract`

Required contract content:

- module name
- parameters and ports
- widths and directions
- clock and reset candidates
- reset polarity guess with confidence
- handshake signals
- sequential/comb guess
- latency model
- observable outputs
- illegal input constraints
- assumptions and ambiguities

### Stage 2: Test Plan Generation

Inputs:

- `DUTContract`
- task description
- optional spec

Output:

- `TestPlan`

Each test case includes:

- case id
- goal
- category
- preconditions
- stimulus intent
- expected properties
- observed signals
- timing window
- dependencies
- coverage tags
- priority

### Stage 3: Oracle Generation

Inputs:

- `DUTContract`
- `TestPlan`
- task description and spec

Output:

- `OracleSpec`

Oracle classes:

1. protocol oracle
2. functional oracle
3. property oracle

### Stage 4: Testbench Rendering

Inputs:

- contract
- plan
- oracle
- simulation config

Output:

- cocotb test package and metadata

Expected generated artifacts:

- `test_<dut>_basic.py`
- `test_<dut>_protocol.py`
- `test_<dut>_edge.py`
- `<dut>_env.py`
- `<dut>_interface.py`
- `<dut>_oracle.py`
- `<dut>_coverage.py`
- runner config / Makefile
- `metadata.json`

### Stage 5: Simulation Execution

Inputs:

- generated cocotb package
- `SimulationConfig`

Output:

- `SimulationResult`

Execution must support:

- cocotb-tools runner mode
- Makefile mode
- filelist mode
- multi-file RTL
- include directories
- parameter passing

### Stage 6: Failure Classification / Triage

Inputs:

- contract
- plan
- oracle
- simulation result

Output:

- `TriageResult`

Required primary categories:

- `compile_error`
- `elaboration_error`
- `environment_error`
- `timeout_error`
- `bad_port_mapping`
- `reset_assumption_error`
- `latency_assumption_error`
- `protocol_monitor_error`
- `oracle_error`
- `weak_testbench`
- `unresolved_ambiguity`
- `likely_dut_bug`

### Stage 7: Targeted Repair

Inputs:

- triage result
- relevant upstream artifacts

Output:

- `RepairAction`

Repair must be stage-local and must not weaken assertions or drop critical cases.

### Stage 8: Report / Verdict

Inputs:

- all upstream artifacts and summaries

Output:

- `VerificationReport`
- `FinalVerdict`

Verdict values:

- `pass`
- `fail`
- `suspicious`
- `inconclusive`

Key rules:

- if primary run passes but independent confirmation fails, verdict cannot be `pass`
- unresolved ambiguity on core behavior should lead to `inconclusive`
- verdict must include rationale and risk signals

## 5. How the New Design Reduces False Positives and False Negatives

### False Positive Reduction

- separate stimulus generation from oracle generation
- use structured test plans before rendering code
- keep protocol monitors separate from drivers
- use independent confirmation logic and mark failures as `suspicious`
- do not accept confirmation failures as warnings-only passes
- preserve unresolved ambiguity instead of inventing exact expected values

### False Negative Reduction

- represent reset, clock, and latency assumptions explicitly with confidence
- support richer runner modes and real multi-file projects
- classify infrastructure and assumption failures separately from DUT failures
- avoid over-reliance on weak heuristics such as assertion counts or raw signal access counts

## 6. Key Differences from `cocotbverify_v1`

Old behavior:

- mixed planning, rendering, fallback, repair, and confirmation logic in one implementation
- often used one large cocotb test
- let one LLM response define both stimulus and expectation
- could keep a `pass` despite failed confirmation
- weak coverage quality signals
- runner optimized for a very narrow single-file flow
- limited failure taxonomy

New behavior:

- stage-oriented pipeline with persistent artifacts
- multi-test cocotb package
- oracle generated independently from stimulus plan
- confirmation failure yields `suspicious`, not `pass`
- structured triage and repair
- runner abstraction for realistic projects

## 7. Risks and Constraints

- functional oracle quality is bounded by spec quality
- some designs require unresolved behavior to remain unresolved
- reset and latency inference can be uncertain and must carry confidence
- LLM schema drift must be contained through validation
- multi-file parsing is a staged engineering effort and should start simple in MVP

## 8. Phase 0 Scope

Phase 0 only creates the project skeleton and typed interfaces.
It does not implement business logic for contract extraction, plan generation, oracle generation, runner execution, triage, or repair.
The objective is to establish:

- installable packaging
- typed core models
- CLI skeleton
- orchestrator shell
- documentation in-repo
- smoke tests for models and CLI
