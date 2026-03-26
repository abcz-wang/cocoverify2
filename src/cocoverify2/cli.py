"""Command-line interface skeleton for cocoverify2."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from cocoverify2 import __version__
from cocoverify2.core.errors import CocoverifyError, ConfigurationError, PhaseNotImplementedError
from cocoverify2.stages.contract_extractor import ContractExtractor, load_optional_text
from cocoverify2.stages.test_plan_generator import TestPlanGenerator


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""
    parser = argparse.ArgumentParser(
        prog="cocoverify2",
        description="Stage-based LLM-assisted cocotb verification framework.",
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
            "run",
            "triage",
            "repair",
            "report",
        ],
        help="Optional stage name.",
    )
    stage_parser.add_argument("--in-dir", type=Path, help="Input artifact or source directory.")
    stage_parser.add_argument("--out-dir", type=Path, help="Output artifact directory.")
    stage_parser.add_argument("--contract", type=Path, help="Contract artifact path for the plan stage.")
    stage_parser.add_argument("--rtl", action="append", default=[], help="RTL source path. May be passed multiple times.")
    stage_parser.add_argument("--task-description", default="", help="Optional task description text.")
    stage_parser.add_argument("--spec", type=Path, help="Optional specification file path.")
    stage_parser.add_argument("--golden-interface", type=Path, help="Optional golden interface text file.")
    stage_parser.set_defaults(handler=_handle_stage)

    repair_parser = subparsers.add_parser(
        "repair",
        help="Plan or execute a targeted repair step.",
        description="Plan or execute a targeted repair step.",
    )
    repair_parser.add_argument("--out-dir", type=Path, help="Artifact root for repair planning.")
    repair_parser.add_argument("--triage", type=Path, help="Optional triage artifact path.")
    repair_parser.set_defaults(handler=_handle_repair)

    return parser


def _handle_verify(args: argparse.Namespace) -> int:
    """Handle the placeholder verify command."""
    _ = args
    raise PhaseNotImplementedError("Phase 2 only implements the contract and plan stages; verify is not implemented yet.")


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
        )
        print(f"Test plan generated for module '{plan.module_name}' -> {out_dir / 'plan' / 'test_plan.json'}")
        return 0

    raise PhaseNotImplementedError(
        "Phase 2 implements the contract and plan stages only; other stage commands are not implemented yet."
    )


def _handle_repair(args: argparse.Namespace) -> int:
    """Handle the placeholder repair command."""
    _ = args
    raise PhaseNotImplementedError("Phase 2 only implements the contract and plan stages; repair is not implemented yet.")


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
