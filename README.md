# cocoverify2

`cocoverify2` is a stage-based LLM-assisted cocotb verification framework.

Phase 0 in this repository provides:

- project documentation
- installable Python package skeleton
- typed core models
- CLI command skeleton
- orchestrator shell
- smoke tests for package health

It intentionally does **not** implement verification business logic yet.

## Installation

```bash
pip install -e .
```

For development and tests:

```bash
pip install -e .[dev]
```

## CLI

```bash
cocoverify2 --help
cocoverify2 verify --help
cocoverify2 stage --help
cocoverify2 repair --help
```

## Documentation

- `docs/architecture.md`
- `docs/mvp_plan.md`
