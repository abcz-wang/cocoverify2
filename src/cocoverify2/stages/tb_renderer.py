"""Template-driven cocotb testbench rendering for Phase 4."""

from __future__ import annotations

from pathlib import Path
from statistics import fmean

from cocoverify2.cocotbgen.coverage import render_coverage_module
from cocoverify2.cocotbgen.env import render_env_module
from cocoverify2.cocotbgen.interface import render_interface_module
from cocoverify2.cocotbgen.makefile import render_makefile
from cocoverify2.cocotbgen.oracle import render_oracle_module
from cocoverify2.cocotbgen.runtime_helpers import render_runtime_helpers_module
from cocoverify2.cocotbgen.testfiles import render_test_modules
from cocoverify2.core.errors import ArtifactError, ConfigurationError
from cocoverify2.core.models import DUTContract, LLMTodoBlock, OracleCase, OracleSpec, RenderMetadata, RenderedFile, TestPlan
from cocoverify2.core.types import SequentialKind
from cocoverify2.utils.files import ensure_dir, read_json, write_json, write_text
from cocoverify2.utils.logging import get_logger


class TBRenderer:
    """Render a conservative cocotb package from structured upstream artifacts."""

    __test__ = False

    def __init__(self) -> None:
        """Initialize the renderer with a stage-scoped logger."""
        self.logger = get_logger(__name__)

    def run(
        self,
        *,
        contract: DUTContract,
        plan: TestPlan,
        oracle: OracleSpec,
        task_description: str | None,
        spec_text: str | None,
        out_dir: Path,
        based_on_contract: str = "",
        based_on_plan: str = "",
        based_on_oracle: str = "",
    ) -> RenderMetadata:
        """Render the Phase 4 cocotb package and persist stable metadata."""
        self._validate_inputs(contract=contract, plan=plan, oracle=oracle)
        render_dir = ensure_dir(out_dir / "render")
        package_dir = ensure_dir(render_dir / "cocotb_tests")
        package_name = contract.module_name
        interface_module = f"{package_name}_interface"
        env_module = f"{package_name}_env"
        oracle_module = f"{package_name}_oracle"
        coverage_module = f"{package_name}_coverage"
        runtime_module = f"{package_name}_runtime"

        temporal_modes_used = _temporal_modes_used(oracle)
        oracle_cases_by_plan = _oracle_cases_by_plan(oracle)

        self.logger.debug(
            "Rendering cocotb package for module=%s plan_cases=%d temporal_modes=%s",
            contract.module_name,
            len(plan.cases),
            temporal_modes_used,
        )

        interface_content, interface_summary = render_interface_module(contract)
        coverage_content, coverage_summary = render_coverage_module(contract.module_name, plan)
        runtime_content, _runtime_summary = render_runtime_helpers_module(contract.module_name)
        env_content, env_summary = render_env_module(
            contract,
            plan,
            temporal_modes_used=temporal_modes_used,
            interface_module=interface_module,
            coverage_module=coverage_module,
            runtime_module=runtime_module,
        )
        oracle_content, oracle_summary = render_oracle_module(contract, oracle, runtime_module=runtime_module)
        test_modules = render_test_modules(
            contract,
            plan,
            oracle_cases_by_plan=oracle_cases_by_plan,
            env_module=env_module,
            oracle_module=oracle_module,
        )
        default_test_module = f"test_{contract.module_name}_basic"
        makefile_content, _makefile_summary = render_makefile(contract.module_name, default_test_module=default_test_module)

        generated_files: list[RenderedFile] = []
        llm_todo_blocks: list[LLMTodoBlock] = []
        self._write_generated_file(
            package_dir / "__init__.py",
            '"""Rendered cocotb test package for Phase 4."""\n',
            generated_files,
            role="package_init",
            description="Marks the rendered cocotb test directory as a Python package.",
        )
        self._write_generated_file(
            package_dir / f"{interface_module}.py",
            interface_content,
            generated_files,
            role="interface",
            description="Conservative DUT interface helpers derived from the contract artifact.",
        )
        self._write_generated_file(
            package_dir / f"{env_module}.py",
            env_content,
            generated_files,
            role="env",
            description="Thin environment wrapper that composes interface, timing-safe waits, and coverage helpers.",
            template_name=str(env_summary.get("template_name", "")),
            todo_blocks=env_summary.get("llm_todo_blocks", []),
            llm_todo_blocks=llm_todo_blocks,
        )
        self._write_generated_file(
            package_dir / f"{oracle_module}.py",
            oracle_content,
            generated_files,
            role="oracle",
            description="Structured oracle helper functions rendered from the oracle artifact.",
            template_name=str(oracle_summary.get("template_name", "")),
            todo_blocks=oracle_summary.get("llm_todo_blocks", []),
            llm_todo_blocks=llm_todo_blocks,
        )
        self._write_generated_file(
            package_dir / f"{runtime_module}.py",
            runtime_content,
            generated_files,
            role="runtime",
            description="Stable runtime helpers exposed to LLM-filled stimulus and oracle TODO blocks.",
        )
        self._write_generated_file(
            package_dir / f"{coverage_module}.py",
            coverage_content,
            generated_files,
            role="coverage",
            description="Coverage scaffold rendered from plan coverage tags for later execution stages.",
        )
        for filename, (content, module_summary) in test_modules.items():
            self._write_generated_file(
                package_dir / filename,
                content,
                generated_files,
                role="test_module",
                description=f"Rendered {module_summary['group_name']} cocotb tests aligned to structured plan cases.",
                template_name=str(module_summary.get("template_name", "")),
                todo_blocks=module_summary.get("llm_todo_blocks", []),
                llm_todo_blocks=llm_todo_blocks,
            )
        self._write_generated_file(
            package_dir / "Makefile",
            makefile_content,
            generated_files,
            role="makefile",
            description="Phase 4 executable Makefile shell; Phase 5 injects run-time variables and executes it.",
        )

        render_warnings = _render_warnings(contract=contract, plan=plan, oracle=oracle, test_modules=test_modules)
        if task_description:
            render_warnings.append("Task description was provided to the render stage but not used to invent new testbench semantics.")
        if spec_text:
            render_warnings.append("Spec text was provided to the render stage but only upstream artifacts were trusted for code generation.")
        render_warnings = _deduped(render_warnings)

        metadata = RenderMetadata(
            module_name=contract.module_name,
            artifact_stage="render",
            based_on_contract=based_on_contract or contract.module_name,
            based_on_plan=based_on_plan or plan.module_name,
            based_on_oracle=based_on_oracle or oracle.module_name,
            generated_files=generated_files,
            test_modules=[Path(item.relative_path).stem for item in generated_files if item.role == "test_module"],
            interface_summary=interface_summary,
            env_summary={
                **env_summary,
                "driver_helpers": ["exercise_case", "drive_inputs", "wait_for_settle", "record_case_inputs"],
                "monitor_helpers": ["safe_observe", "note_oracle_result", "sample_outputs"],
                "oracle_helper_module": oracle_module,
            },
            oracle_summary={
                **oracle_summary,
                "preserves_temporal_modes": temporal_modes_used,
                "runtime_helper_module": runtime_module,
            },
            coverage_summary=coverage_summary,
            template_inventory=_template_inventory(generated_files=generated_files, llm_todo_blocks=llm_todo_blocks),
            llm_todo_blocks=llm_todo_blocks,
            filled_todo_block_ids=[],
            unfilled_todo_block_ids=[block.block_id for block in llm_todo_blocks],
            fill_status="pending" if llm_todo_blocks else "not_required",
            fill_warnings=["Rendered TODO blocks require the fill stage before this package becomes a strong functional testbench."],
            render_warnings=render_warnings,
            render_confidence=_estimate_render_confidence(contract=contract, plan=plan, oracle=oracle, warnings=render_warnings),
        )
        write_json(render_dir / "metadata.json", metadata.model_dump(mode="json"))
        self.logger.info("Rendered cocotb package for module '%s' into %s", contract.module_name, package_dir)
        return metadata

    def run_from_artifacts(
        self,
        *,
        contract_path: Path,
        plan_path: Path,
        oracle_path: Path,
        task_description: str | None,
        spec_text: str | None,
        out_dir: Path,
    ) -> RenderMetadata:
        """Load artifacts from disk and render the Phase 4 package."""
        return self.run(
            contract=load_contract_artifact(contract_path),
            plan=load_test_plan_artifact(plan_path),
            oracle=load_oracle_artifact(oracle_path),
            task_description=task_description,
            spec_text=spec_text,
            out_dir=out_dir,
            based_on_contract=str(contract_path),
            based_on_plan=str(plan_path),
            based_on_oracle=str(oracle_path),
        )

    def _validate_inputs(self, *, contract: DUTContract, plan: TestPlan, oracle: OracleSpec) -> None:
        if not contract.module_name or not plan.module_name or not oracle.module_name:
            raise ConfigurationError("Render stage requires non-empty module_name in contract, plan, and oracle artifacts.")
        if len({contract.module_name, plan.module_name, oracle.module_name}) != 1:
            raise ConfigurationError(
                "Render stage requires matching module_name across contract, plan, and oracle artifacts: "
                f"contract={contract.module_name!r}, plan={plan.module_name!r}, oracle={oracle.module_name!r}."
            )

    def _write_generated_file(
        self,
        path: Path,
        content: str,
        generated_files: list[RenderedFile],
        *,
        role: str,
        description: str,
        template_name: str = "",
        todo_blocks: list[dict[str, object]] | None = None,
        llm_todo_blocks: list[LLMTodoBlock] | None = None,
    ) -> None:
        write_text(path, content)
        relative_path = str(path.relative_to(path.parents[1]))
        finalized_todo_blocks = _finalize_todo_blocks(
            todo_blocks=todo_blocks or [],
            relative_path=relative_path,
            role=role,
            template_name=template_name,
        )
        generated_files.append(
            RenderedFile(
                relative_path=relative_path,
                role=role,
                description=description,
                template_name=template_name,
                todo_block_ids=[block.block_id for block in finalized_todo_blocks],
            )
        )
        if llm_todo_blocks is not None:
            llm_todo_blocks.extend(finalized_todo_blocks)


def load_contract_artifact(path: Path) -> DUTContract:
    """Load a ``DUTContract`` artifact from JSON."""
    if not path.exists():
        raise ArtifactError(f"Contract artifact does not exist: {path}")
    return DUTContract.model_validate(read_json(path))



def load_test_plan_artifact(path: Path) -> TestPlan:
    """Load a ``TestPlan`` artifact from JSON."""
    if not path.exists():
        raise ArtifactError(f"Test plan artifact does not exist: {path}")
    return TestPlan.model_validate(read_json(path))



def load_oracle_artifact(path: Path) -> OracleSpec:
    """Load an ``OracleSpec`` artifact from JSON."""
    if not path.exists():
        raise ArtifactError(f"Oracle artifact does not exist: {path}")
    return OracleSpec.model_validate(read_json(path))



def _oracle_cases_by_plan(oracle: OracleSpec) -> dict[str, list[OracleCase]]:
    mapping: dict[str, list[OracleCase]] = {}
    for case in [*oracle.protocol_oracles, *oracle.functional_oracles, *oracle.property_oracles]:
        mapping.setdefault(case.linked_plan_case_id, []).append(case)
    return mapping



def _temporal_modes_used(oracle: OracleSpec) -> list[str]:
    modes = {
        check.temporal_window.mode
        for case in [*oracle.protocol_oracles, *oracle.functional_oracles, *oracle.property_oracles]
        for check in case.checks
    }
    return sorted(modes)


def _finalize_todo_blocks(
    *,
    todo_blocks: list[dict[str, object]],
    relative_path: str,
    role: str,
    template_name: str,
) -> list[LLMTodoBlock]:
    finalized: list[LLMTodoBlock] = []
    for block in todo_blocks:
        payload = dict(block)
        payload["relative_path"] = relative_path
        payload["file_role"] = role
        if not payload.get("template_name"):
            payload["template_name"] = template_name
        finalized.append(LLMTodoBlock.model_validate(payload))
    return finalized


def _template_inventory(*, generated_files: list[RenderedFile], llm_todo_blocks: list[LLMTodoBlock]) -> list[str]:
    names = {
        item.template_name
        for item in generated_files
        if item.template_name
    }
    names.update(block.template_name for block in llm_todo_blocks if block.template_name)
    return sorted(names)



def _render_warnings(
    *,
    contract: DUTContract,
    plan: TestPlan,
    oracle: OracleSpec,
    test_modules: dict[str, tuple[str, dict[str, object]]],
) -> list[str]:
    warnings = list(contract.extraction_warnings) + list(contract.ambiguities) + list(plan.unresolved_items) + list(oracle.unresolved_items)
    if contract.timing.sequential_kind == SequentialKind.UNKNOWN:
        warnings.append("Timing is unresolved; rendering preserves event-based and safety-style checks only.")
    if contract.contract_confidence < 0.6:
        warnings.append("Contract confidence is low; interface and testcase rendering remain conservative.")
    if plan.plan_confidence < 0.6:
        warnings.append("Plan confidence is limited; testcase grouping avoids inventing stronger sequencing semantics.")
    if oracle.oracle_confidence.overall_confidence < 0.6:
        warnings.append("Oracle confidence is limited; rendered checks preserve unresolved items and avoid stronger value-level assertions.")
    if any(not case.checks for case in oracle.functional_oracles):
        warnings.append("Some functional oracle cases are intentionally empty; render output preserves them as conservative protocol/property-driven tests.")
    if "test_{}_protocol.py".format(contract.module_name) not in test_modules and contract.handshake_groups:
        warnings.append("Handshake hints exist, but no protocol testcase module was rendered because the plan/oracle did not justify one.")
    warnings.append("Rendered Makefile is an executable Phase 4 shell; Phase 5 injects execution variables and selects the backend.")
    return warnings



def _estimate_render_confidence(
    *,
    contract: DUTContract,
    plan: TestPlan,
    oracle: OracleSpec,
    warnings: list[str],
) -> float:
    base = fmean([contract.contract_confidence, plan.plan_confidence, oracle.oracle_confidence.overall_confidence])
    penalty = min(0.3, 0.02 * len(warnings))
    if contract.timing.sequential_kind == SequentialKind.UNKNOWN:
        penalty += 0.05
    return max(0.05, min(base - penalty, 0.95))



def _deduped(items: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_items: list[str] = []
    for item in items:
        if not item or item in seen:
            continue
        seen.add(item)
        unique_items.append(item)
    return unique_items
