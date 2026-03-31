"""Command-line interface skeleton for cocoverify2."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from cocoverify2 import __version__
from cocoverify2.core.config import ArtifactConfig, LLMConfig, VerificationConfig
from cocoverify2.core.errors import CocoverifyError, ConfigurationError, PhaseNotImplementedError
from cocoverify2.core.orchestrator import VerificationOrchestrator
from cocoverify2.core.models import SimulationConfig
from cocoverify2.core.types import GenerationMode, SimulationMode
from cocoverify2.stages.contract_extractor import ContractExtractor, load_optional_text
from cocoverify2.stages.oracle_generator import OracleGenerator
from cocoverify2.stages.repair import RepairPlannerStage, earliest_repair_stage
from cocoverify2.stages.simulator_runner import SimulatorRunnerStage
from cocoverify2.stages.tb_renderer import TBRenderer
from cocoverify2.stages.todo_fill import TodoFillStage
from cocoverify2.stages.triage import TriageStage
from cocoverify2.stages.test_plan_generator import TestPlanGenerator


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""
    parser = argparse.ArgumentParser(
        prog="cocoverify2",
        description="Stage-based cocotb verification framework with hybrid LLM support in plan/oracle stages and experimental post-render fill.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    verify_parser = subparsers.add_parser(
        "verify",
        help="Run the end-to-end verification pipeline.",
        description="Run the end-to-end verification pipeline.",
    )
    verify_parser.add_argument("--rtl", action="append", default=[], help="RTL source path. May be passed multiple times.")
    verify_parser.add_argument("--task-id", default="", help="Task identifier.")
    verify_parser.add_argument("--task-description", default="", help="Task description or prompt.")
    verify_parser.add_argument("--spec", type=Path, help="Optional specification file path.")
    verify_parser.add_argument("--golden-tb", type=Path, help="Optional golden testbench path.")
    verify_parser.add_argument("--out-dir", type=Path, required=False, help="Output directory for generated artifacts.")
    verify_parser.add_argument("--filelist", type=Path, help="Optional RTL filelist path for the run stage.")
    verify_parser.add_argument("--include-dir", action="append", default=[], help="Include directory. May be passed multiple times.")
    verify_parser.add_argument("--simulator", default="icarus", help="Simulator backend name for the run stage.")
    verify_parser.add_argument(
        "--mode",
        choices=[mode.value for mode in SimulationMode],
        default=SimulationMode.AUTO.value,
        help="Execution mode for the run stage.",
    )
    verify_parser.add_argument("--top-module", default="", help="Optional HDL toplevel override for the run stage.")
    verify_parser.add_argument("--test-module", default="", help="Optional Python test module override for the run stage.")
    verify_parser.add_argument("--timeout-seconds", type=int, default=60, help="Execution timeout for the run stage.")
    verify_parser.add_argument("--waves", action="store_true", help="Enable waveform collection when supported.")
    verify_parser.add_argument("--junit", action="store_true", help="Request JUnit output when supported.")
    verify_parser.add_argument("--parameter", action="append", default=[], help="Parameter override in KEY=VALUE form.")
    verify_parser.add_argument("--env", action="append", default=[], help="Extra environment entry in KEY=VALUE form.")
    verify_parser.add_argument("--plusarg", action="append", default=[], help="Plusarg passed through to the runner.")
    verify_parser.add_argument("--make-target", action="append", default=[], help="Optional make target override.")
    verify_parser.add_argument("--working-dir", type=Path, help="Optional working directory override for runner execution.")
    verify_parser.add_argument("--clean-build", action="store_true", help="Request a clean build when the backend supports it.")
    verify_parser.add_argument(
        "--generation-mode",
        choices=[mode.value for mode in GenerationMode],
        default=GenerationMode.RULE_BASED.value,
        help="Generation mode for the plan/oracle stages.",
    )
    verify_parser.add_argument("--llm-provider", default="", help="Optional LLM provider override for the plan/oracle stages.")
    verify_parser.add_argument("--llm-model", default="", help="Optional LLM model override for the plan/oracle stages.")
    verify_parser.add_argument("--llm-base-url", default="", help="Optional LLM base_url override for the plan/oracle stages.")
    verify_parser.add_argument("--llm-api-key", default="", help="Optional LLM API key override for the plan/oracle stages.")
    verify_parser.add_argument("--llm-temperature", type=float, default=None, help="Optional LLM temperature override for the plan/oracle stages.")
    verify_parser.add_argument("--llm-timeout-seconds", type=int, default=None, help="Optional LLM timeout override for the plan/oracle stages.")
    verify_parser.add_argument("--llm-max-retries", type=int, default=None, help="Optional LLM retry-count override for the plan/oracle stages.")
    verify_parser.add_argument("--max-repair-rounds", type=int, default=1, help="Maximum number of repair rounds in the verify loop.")
    verify_parser.set_defaults(handler=_handle_verify)

    stage_parser = subparsers.add_parser(
        "stage",
        help="Run or inspect a single pipeline stage.",
        description="Run or inspect a single pipeline stage.",
    )
    stage_parser.add_argument(
        "stage_name",
        nargs="?",
        choices=[
            "contract",
            "plan",
            "oracle",
            "render",
            "fill",
            "run",
            "triage",
            "repair",
            "report",
        ],
        help="Optional stage name.",
    )
    stage_parser.add_argument("--in-dir", type=Path, help="Input artifact or source directory.")
    stage_parser.add_argument("--out-dir", type=Path, help="Output artifact directory.")
    stage_parser.add_argument("--contract", type=Path, help="Contract artifact path for the plan/oracle/render stages.")
    stage_parser.add_argument("--plan", type=Path, help="Test plan artifact path for the oracle/render stages.")
    stage_parser.add_argument("--oracle", type=Path, help="Oracle artifact path for the render stage.")
    stage_parser.add_argument("--render", type=Path, help="Render metadata path for the run stage.")
    stage_parser.add_argument("--rtl", action="append", default=[], help="RTL source path. May be passed multiple times.")
    stage_parser.add_argument("--filelist", type=Path, help="Optional RTL filelist path for the run stage.")
    stage_parser.add_argument("--include-dir", action="append", default=[], help="Include directory. May be passed multiple times.")
    stage_parser.add_argument("--simulator", default="icarus", help="Simulator backend name for the run stage.")
    stage_parser.add_argument(
        "--mode",
        choices=[mode.value for mode in SimulationMode],
        default=SimulationMode.AUTO.value,
        help="Execution mode for the run stage.",
    )
    stage_parser.add_argument("--top-module", default="", help="Optional HDL toplevel override for the run stage.")
    stage_parser.add_argument("--test-module", default="", help="Optional Python test module override for the run stage.")
    stage_parser.add_argument("--timeout-seconds", type=int, default=60, help="Execution timeout for the run stage.")
    stage_parser.add_argument("--waves", action="store_true", help="Enable waveform collection when supported.")
    stage_parser.add_argument("--junit", action="store_true", help="Request JUnit output when supported.")
    stage_parser.add_argument("--parameter", action="append", default=[], help="Parameter override in KEY=VALUE form.")
    stage_parser.add_argument("--env", action="append", default=[], help="Extra environment entry in KEY=VALUE form.")
    stage_parser.add_argument("--plusarg", action="append", default=[], help="Plusarg passed through to the runner.")
    stage_parser.add_argument("--make-target", action="append", default=[], help="Optional make target override.")
    stage_parser.add_argument("--working-dir", type=Path, help="Optional working directory override for runner execution.")
    stage_parser.add_argument("--clean-build", action="store_true", help="Request a clean build when the backend supports it.")
    stage_parser.add_argument("--task-description", default="", help="Optional task description text.")
    stage_parser.add_argument("--spec", type=Path, help="Optional specification file path.")
    stage_parser.add_argument("--golden-interface", type=Path, help="Optional golden interface text file.")
    stage_parser.add_argument(
        "--generation-mode",
        choices=[mode.value for mode in GenerationMode],
        default=GenerationMode.RULE_BASED.value,
        help="Generation mode for the plan/oracle stages.",
    )
    stage_parser.add_argument("--llm-provider", default="", help="Optional LLM provider override for the plan/oracle stages.")
    stage_parser.add_argument("--llm-model", default="", help="Optional LLM model override for the plan/oracle stages.")
    stage_parser.add_argument("--llm-base-url", default="", help="Optional LLM base_url override for the plan/oracle stages.")
    stage_parser.add_argument("--llm-api-key", default="", help="Optional LLM API key override for the plan/oracle stages.")
    stage_parser.add_argument("--llm-temperature", type=float, default=None, help="Optional LLM temperature override for the plan/oracle stages.")
    stage_parser.add_argument("--llm-timeout-seconds", type=int, default=None, help="Optional LLM timeout override for the plan/oracle stages.")
    stage_parser.add_argument("--llm-max-retries", type=int, default=None, help="Optional LLM retry-count override for the plan/oracle stages.")
    stage_parser.set_defaults(handler=_handle_stage)

    repair_parser = subparsers.add_parser(
        "repair",
        help="Plan or execute a targeted repair step.",
        description="Plan or execute a targeted repair step.",
    )
    repair_parser.add_argument("--in-dir", type=Path, help="Artifact root or triage directory for repair planning.")
    repair_parser.add_argument("--out-dir", type=Path, help="Artifact root for repair planning.")
    repair_parser.add_argument("--triage", type=Path, help="Optional triage artifact path.")
    repair_parser.set_defaults(handler=_handle_repair)

    return parser


def _handle_verify(args: argparse.Namespace) -> int:
    """Handle the end-to-end verify command."""
    out_dir = args.out_dir or Path("out")
    llm_config = _build_llm_config(args)
    orchestrator = VerificationOrchestrator(
        config=VerificationConfig(
            llm=llm_config,
            artifacts=ArtifactConfig(out_dir=out_dir),
            max_repair_rounds=args.max_repair_rounds,
        )
    )
    report = orchestrator.verify(
        rtl=[Path(path) for path in args.rtl],
        task_id=args.task_id,
        task_description=args.task_description,
        spec=args.spec,
        golden_tb=args.golden_tb,
        out_dir=out_dir,
        generation_mode=GenerationMode(args.generation_mode),
        llm_config=llm_config,
        simulation_config=_build_simulation_config(args),
        max_repair_rounds=args.max_repair_rounds,
    )
    module_name = report.contract.module_name if report.contract else "<unknown>"
    print(
        "Verification completed for module "
        f"'{module_name}' with verdict '{report.final_verdict.verdict}' -> {out_dir / 'report' / 'verification_report.json'}"
    )
    return 0


def _handle_stage(args: argparse.Namespace) -> int:
    """Handle stage execution for the currently implemented phases."""
    if args.stage_name == "contract":
        rtl_paths = [Path(path) for path in args.rtl] or _discover_rtl_paths(args.in_dir)
        if not rtl_paths:
            raise ConfigurationError("The contract stage requires --rtl or an --in-dir containing .v/.sv sources.")
        out_dir = args.out_dir or Path("out")

        spec_path = args.spec or _resolve_optional_input(args.in_dir, "spec.txt")
        golden_interface_path = args.golden_interface or _resolve_optional_input(args.in_dir, "golden_interface.txt")
        extractor = ContractExtractor()
        contract = extractor.run(
            rtl_paths=rtl_paths,
            task_description=args.task_description or None,
            spec_text=load_optional_text(spec_path),
            golden_interface_text=load_optional_text(golden_interface_path),
            out_dir=out_dir,
        )
        print(f"Contract extracted for module '{contract.module_name}' -> {out_dir / 'contract' / 'contract.json'}")
        return 0

    if args.stage_name == "plan":
        contract_path = args.contract or _resolve_contract_path(args.in_dir)
        if contract_path is None:
            raise ConfigurationError("The plan stage requires --contract or an --in-dir containing contract/contract.json.")
        out_dir = args.out_dir or Path("out")
        spec_path = args.spec or _resolve_optional_input(args.in_dir, "spec.txt")
        generator = TestPlanGenerator()
        plan = generator.run_from_artifact(
            contract_path=contract_path,
            task_description=args.task_description or None,
            spec_text=load_optional_text(spec_path),
            out_dir=out_dir,
            generation_mode=GenerationMode(args.generation_mode),
            llm_config=_build_llm_config(args),
        )
        print(f"Test plan generated for module '{plan.module_name}' -> {out_dir / 'plan' / 'test_plan.json'}")
        return 0

    if args.stage_name == "oracle":
        contract_path = args.contract or _resolve_contract_path(args.in_dir)
        if contract_path is None:
            raise ConfigurationError("The oracle stage requires --contract or an --in-dir containing contract/contract.json.")
        plan_path = args.plan or _resolve_plan_path(args.in_dir)
        if plan_path is None:
            raise ConfigurationError("The oracle stage requires --plan or an --in-dir containing plan/test_plan.json.")
        out_dir = args.out_dir or Path("out")
        spec_path = args.spec or _resolve_optional_input(args.in_dir, "spec.txt")
        generator = OracleGenerator()
        oracle = generator.run_from_artifacts(
            contract_path=contract_path,
            plan_path=plan_path,
            task_description=args.task_description or None,
            spec_text=load_optional_text(spec_path),
            out_dir=out_dir,
            generation_mode=GenerationMode(args.generation_mode),
            llm_config=_build_llm_config(args),
        )
        print(f"Oracle generated for module '{oracle.module_name}' -> {out_dir / 'oracle' / 'oracle.json'}")
        return 0

    if args.stage_name == "render":
        contract_path = args.contract or _resolve_contract_path(args.in_dir)
        if contract_path is None:
            raise ConfigurationError("The render stage requires --contract or an --in-dir containing contract/contract.json.")
        plan_path = args.plan or _resolve_plan_path(args.in_dir)
        if plan_path is None:
            raise ConfigurationError("The render stage requires --plan or an --in-dir containing plan/test_plan.json.")
        oracle_path = args.oracle or _resolve_oracle_path(args.in_dir)
        if oracle_path is None:
            raise ConfigurationError("The render stage requires --oracle or an --in-dir containing oracle/oracle.json.")
        out_dir = args.out_dir or Path("out")
        spec_path = args.spec or _resolve_optional_input(args.in_dir, "spec.txt")
        renderer = TBRenderer()
        metadata = renderer.run_from_artifacts(
            contract_path=contract_path,
            plan_path=plan_path,
            oracle_path=oracle_path,
            task_description=args.task_description or None,
            spec_text=load_optional_text(spec_path),
            out_dir=out_dir,
        )
        print(f"Render package generated for module '{metadata.module_name}' -> {out_dir / 'render' / 'metadata.json'}")
        return 0

    if args.stage_name == "run":
        render_path = args.render or _resolve_render_path(args.in_dir)
        if render_path is None:
            raise ConfigurationError("The run stage requires --render or an --in-dir containing render/metadata.json.")
        out_dir = args.out_dir or Path("out")
        stage = SimulatorRunnerStage()
        result = stage.run_from_artifact(
            render_metadata_path=render_path,
            config=_build_simulation_config(args),
            out_dir=out_dir,
        )
        print(
            "Simulation execution finished for module "
            f"'{result.module_name or '<unknown>'}' with status '{result.status}' -> {out_dir / 'run' / 'simulation_result.json'}"
        )
        return 0

    if args.stage_name == "fill":
        render_path = args.render or _resolve_render_path(args.in_dir)
        if render_path is None:
            raise ConfigurationError("The fill stage requires --render or an --in-dir containing render/metadata.json.")
        out_dir = args.out_dir or Path("out")
        spec_path = args.spec or _resolve_optional_input(args.in_dir, "spec.txt")
        stage = TodoFillStage()
        report = stage.run_from_artifact(
            render_metadata_path=render_path,
            out_dir=out_dir,
            llm_config=_build_llm_config(args),
            task_description=args.task_description or None,
            spec_text=load_optional_text(spec_path),
        )
        print(
            "Experimental TODO fill completed for module "
            f"'{report.module_name or '<unknown>'}' with status '{report.fill_status}' -> {out_dir / 'fill' / 'metadata.json'}"
        )
        return 0

    if args.stage_name == "triage":
        if args.in_dir is None:
            raise ConfigurationError("The triage stage requires --in-dir pointing to a run directory or a phase root containing run/.")
        out_dir = args.out_dir or Path("out")
        stage = TriageStage()
        result = stage.run_from_dir(in_dir=args.in_dir, out_dir=out_dir)
        print(
            "Triage completed for module "
            f"'{result.module_name or '<unknown>'}' with category '{result.primary_category}' -> {out_dir / 'triage' / 'triage.json'}"
        )
        return 0

    if args.stage_name == "repair":
        if args.in_dir is None:
            raise ConfigurationError("The repair stage requires --in-dir pointing to a phase root or triage directory.")
        out_dir = args.out_dir or args.in_dir
        stage = RepairPlannerStage()
        actions = stage.run_from_dir(in_dir=args.in_dir, out_dir=out_dir)
        target_stage = earliest_repair_stage(actions) or "none"
        print(
            "Repair planning completed with "
            f"{len(actions)} action(s); earliest target stage '{target_stage}' -> {out_dir / 'repair' / 'repair_actions.json'}"
        )
        return 0

    raise PhaseNotImplementedError(
        "cocoverify2 currently implements the contract, plan, oracle, render, fill, run, triage, and repair stages only; other stage commands are not implemented yet."
    )


def _handle_repair(args: argparse.Namespace) -> int:
    """Handle repair planning from existing artifacts."""
    stage = RepairPlannerStage()
    if args.triage is not None:
        artifact_root = args.triage.parent.parent
        out_dir = args.out_dir or artifact_root
        actions = stage.run_from_artifact(triage_path=args.triage, out_dir=out_dir)
    else:
        artifact_root = args.in_dir or args.out_dir
        if artifact_root is None:
            raise ConfigurationError("The repair command requires --triage or --in-dir/--out-dir pointing to existing artifacts.")
        out_dir = args.out_dir or artifact_root
        actions = stage.run_from_dir(in_dir=artifact_root, out_dir=out_dir)
    target_stage = earliest_repair_stage(actions) or "none"
    print(
        "Repair planning completed with "
        f"{len(actions)} action(s); earliest target stage '{target_stage}' -> {out_dir / 'repair' / 'repair_actions.json'}"
    )
    return 0


def _discover_rtl_paths(in_dir: Path | None) -> list[Path]:
    if in_dir is None:
        return []
    if not in_dir.exists():
        raise ConfigurationError(f"Input directory does not exist: {in_dir}")
    return sorted({*in_dir.rglob("*.v"), *in_dir.rglob("*.sv")})


def _resolve_optional_input(in_dir: Path | None, filename: str) -> Path | None:
    if in_dir is None:
        return None
    candidate = in_dir / filename
    return candidate if candidate.exists() else None


def _resolve_contract_path(in_dir: Path | None) -> Path | None:
    """Resolve a default contract artifact path from an input directory."""
    if in_dir is None:
        return None
    direct_candidate = in_dir / "contract.json"
    if direct_candidate.exists():
        return direct_candidate
    nested_candidate = in_dir / "contract" / "contract.json"
    if nested_candidate.exists():
        return nested_candidate
    return None


def _resolve_plan_path(in_dir: Path | None) -> Path | None:
    """Resolve a default test-plan artifact path from an input directory."""
    if in_dir is None:
        return None
    direct_candidate = in_dir / "test_plan.json"
    if direct_candidate.exists():
        return direct_candidate
    nested_candidate = in_dir / "plan" / "test_plan.json"
    if nested_candidate.exists():
        return nested_candidate
    return None


def _resolve_oracle_path(in_dir: Path | None) -> Path | None:
    """Resolve a default oracle artifact path from an input directory."""
    if in_dir is None:
        return None
    direct_candidate = in_dir / "oracle.json"
    if direct_candidate.exists():
        return direct_candidate
    nested_candidate = in_dir / "oracle" / "oracle.json"
    if nested_candidate.exists():
        return nested_candidate
    return None


def _resolve_render_path(in_dir: Path | None) -> Path | None:
    """Resolve a default render metadata path from an input directory."""
    if in_dir is None:
        return None
    direct_candidate = in_dir / "metadata.json"
    if direct_candidate.exists():
        return direct_candidate
    nested_candidate = in_dir / "render" / "metadata.json"
    if nested_candidate.exists():
        return nested_candidate
    return None


def _build_simulation_config(args: argparse.Namespace) -> SimulationConfig:
    """Build a structured ``SimulationConfig`` from CLI arguments."""
    return SimulationConfig(
        simulator=args.simulator,
        mode=SimulationMode(args.mode),
        rtl_sources=[Path(path) for path in args.rtl],
        filelist_path=args.filelist,
        include_dirs=[Path(path) for path in args.include_dir],
        top_module=args.top_module,
        test_module=args.test_module,
        extra_env=_parse_key_value_pairs(args.env),
        parameters=_parse_key_value_pairs(args.parameter),
        waves_enabled=bool(args.waves),
        junit_enabled=bool(args.junit),
        timeout_seconds=args.timeout_seconds,
        working_dir=args.working_dir,
        clean_build=bool(args.clean_build),
        plusargs=list(args.plusarg),
        make_targets=list(args.make_target),
    )


def _build_llm_config(args: argparse.Namespace) -> LLMConfig:
    """Build a structured ``LLMConfig`` from CLI arguments and environment defaults."""
    defaults = LLMConfig()
    return LLMConfig(
        provider=args.llm_provider or defaults.provider,
        model=args.llm_model or defaults.model,
        base_url=args.llm_base_url or defaults.base_url,
        api_key=args.llm_api_key or defaults.api_key,
        temperature=defaults.temperature if args.llm_temperature is None else args.llm_temperature,
        timeout_seconds=defaults.timeout_seconds if args.llm_timeout_seconds is None else args.llm_timeout_seconds,
        max_retries=defaults.max_retries if args.llm_max_retries is None else args.llm_max_retries,
    )


def _parse_key_value_pairs(items: Sequence[str]) -> dict[str, str]:
    """Parse repeated ``KEY=VALUE`` arguments into a dictionary."""
    parsed: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ConfigurationError(f"Expected KEY=VALUE format, got: {item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ConfigurationError(f"Expected non-empty KEY in KEY=VALUE item: {item}")
        parsed[key] = value
    return parsed


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point for cocoverify2."""
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0
    try:
        return handler(args)
    except CocoverifyError as exc:
        parser.exit(status=2, message=f"error: {exc}\n")
    except NotImplementedError as exc:
        parser.exit(status=2, message=f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
