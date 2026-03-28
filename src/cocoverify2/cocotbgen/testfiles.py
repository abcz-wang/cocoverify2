"""Helpers for rendering cocotb testcase modules."""

from __future__ import annotations

from collections import defaultdict

from cocoverify2.cocotbgen.template_loader import render_template
from cocoverify2.cocotbgen.todo_blocks import build_todo_block
from cocoverify2.core.models import DUTContract, OracleCase, TestCasePlan, TestPlan
from cocoverify2.core.types import TestCategory

_BASIC_CATEGORIES = {
    TestCategory.RESET.value,
    TestCategory.BASIC.value,
    TestCategory.BACK_TO_BACK.value,
    TestCategory.NEGATIVE.value,
}
_TEST_MODULE_TEMPLATE = "test_module.py.tmpl"
_TEST_CASE_TEMPLATE = "test_case.py.tmpl"


def render_test_modules(
    contract: DUTContract,
    plan: TestPlan,
    *,
    oracle_cases_by_plan: dict[str, list[OracleCase]],
    env_module: str,
    oracle_module: str,
) -> dict[str, tuple[str, dict[str, object]]]:
    """Render testcase modules grouped by plan category."""
    module_name = contract.module_name
    env_class = f"{_camel(module_name)}Env"
    grouped_cases: dict[str, list[TestCasePlan]] = defaultdict(list)
    for case in plan.cases:
        if case.category == TestCategory.PROTOCOL.value:
            grouped_cases["protocol"].append(case)
        elif case.category == TestCategory.EDGE.value:
            grouped_cases["edge"].append(case)
        elif case.category in _BASIC_CATEGORIES:
            grouped_cases["basic"].append(case)
        else:
            grouped_cases["basic"].append(case)

    rendered: dict[str, tuple[str, dict[str, object]]] = {}
    for group_name in ("basic", "protocol", "edge"):
        if not grouped_cases[group_name]:
            continue
        filename = f"test_{module_name}_{group_name}.py"
        content, module_summary = _render_test_module(
            module_name=module_name,
            env_class=env_class,
            env_module=env_module,
            oracle_module=oracle_module,
            group_name=group_name,
            cases=grouped_cases[group_name],
            oracle_cases_by_plan=oracle_cases_by_plan,
        )
        rendered[filename] = (content, module_summary)
    return rendered


def _render_test_module(
    *,
    module_name: str,
    env_class: str,
    env_module: str,
    oracle_module: str,
    group_name: str,
    cases: list[TestCasePlan],
    oracle_cases_by_plan: dict[str, list[OracleCase]],
) -> tuple[str, dict[str, object]]:
    heading = {
        "basic": "Basic, reset, negative, and repeated-operation tests rendered from the plan.",
        "protocol": "Protocol-focused tests rendered conservatively from handshake-oriented plan cases.",
        "edge": "Edge and boundary tests rendered conservatively from the structured plan.",
    }[group_name]
    case_blocks: list[str] = []
    llm_todo_blocks: list[dict[str, object]] = []
    for case in cases:
        rendered_case, case_todo_blocks = _render_single_test_case(
            env_class=env_class,
            case=case,
            oracle_cases=oracle_cases_by_plan.get(case.case_id, []),
        )
        case_blocks.append(rendered_case)
        llm_todo_blocks.extend(case_todo_blocks)
    content = render_template(
        _TEST_MODULE_TEMPLATE,
        group_name=group_name,
        module_name=module_name,
        heading=heading,
        env_module=env_module,
        env_class=env_class,
        oracle_module=oracle_module,
        case_blocks="\n\n".join(case_blocks),
    )
    summary = {
        "group_name": group_name,
        "case_ids": [case.case_id for case in cases],
        "categories": sorted({case.category for case in cases}),
        "template_name": _TEST_MODULE_TEMPLATE,
        "llm_todo_blocks": llm_todo_blocks,
    }
    return content, summary


def _render_single_test_case(
    *,
    env_class: str,
    case: TestCasePlan,
    oracle_cases: list[OracleCase],
) -> tuple[str, list[dict[str, object]]]:
    func_name = f"test_{_sanitize_identifier(case.case_id)}"
    case_identifier = _sanitize_identifier(case.case_id)
    doc_lines = [case.goal]
    if case.notes:
        doc_lines.extend(f"Note: {note}" for note in case.notes[:2])
    docstring = " ".join(doc_lines)
    comment_lines = [
        f"# Plan category: {case.category}",
        f"# Coverage tags: {', '.join(case.coverage_tags) if case.coverage_tags else 'none'}",
    ]
    if case.timing_assumptions:
        comment_lines.extend(f"# Timing assumption: {item}" for item in case.timing_assumptions[:3])
    unresolved = []
    empty_functional = False
    for oracle_case in oracle_cases:
        unresolved.extend(oracle_case.unresolved_items)
        empty_functional = empty_functional or (oracle_case.case_id.startswith("functional_") and not oracle_case.checks)
    if empty_functional:
        comment_lines.append("# Conservative rendering: no concrete value-level functional oracle was emitted for this case.")
    for item in unresolved[:3]:
        comment_lines.append(f"# Unresolved: {item}")

    setup_todo_block, setup_todo_metadata = build_todo_block(
        fill_kind="testcase_setup",
        block_id=f"testcase_setup_{case.case_id}",
        template_name=_TEST_CASE_TEMPLATE,
        comment_lines=["Guidance: Optional per-case setup before env.exercise_case()."],
        instructions=[
            "Add optional per-case setup before env.exercise_case().",
            "Keep edits inside this TODO block so regeneration stays stable.",
        ],
        context={
            "case_id": case.case_id,
            "category": case.category,
            "dependencies": list(case.dependencies),
            "coverage_tags": list(case.coverage_tags),
            "semantic_tags": list(case.semantic_tags),
            "stimulus_signals": list(case.stimulus_signals),
        },
        indent="    ",
        case_id=case.case_id,
    )
    content = render_template(
        _TEST_CASE_TEMPLATE,
        case_identifier=case_identifier,
        case_id=case.case_id,
        case_id_literal=repr(case.case_id),
        func_name=func_name,
        docstring=docstring,
        comments="\n    ".join(comment_lines),
        env_class=env_class,
        setup_todo_block=setup_todo_block,
    )
    return content, [setup_todo_metadata]


def _camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_")) or "Rendered"


def _sanitize_identifier(name: str) -> str:
    sanitized = "".join(char if char.isalnum() or char == "_" else "_" for char in name)
    if sanitized and sanitized[0].isdigit():
        return f"case_{sanitized}"
    return sanitized or "rendered_case"
