"""Helpers for rendering cocotb testcase modules."""

from __future__ import annotations

from collections import defaultdict

from cocoverify2.core.models import DUTContract, OracleCase, TestCasePlan, TestPlan
from cocoverify2.core.types import TestCategory

_BASIC_CATEGORIES = {
    TestCategory.RESET.value,
    TestCategory.BASIC.value,
    TestCategory.BACK_TO_BACK.value,
    TestCategory.NEGATIVE.value,
}


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
    if grouped_cases["basic"]:
        filename = f"test_{module_name}_basic.py"
        rendered[filename] = (
            _render_test_module(
                module_name=module_name,
                env_class=env_class,
                env_module=env_module,
                oracle_module=oracle_module,
                group_name="basic",
                cases=grouped_cases["basic"],
                oracle_cases_by_plan=oracle_cases_by_plan,
            ),
            {
                "group_name": "basic",
                "case_ids": [case.case_id for case in grouped_cases["basic"]],
                "categories": sorted({case.category for case in grouped_cases["basic"]}),
            },
        )
    if grouped_cases["protocol"]:
        filename = f"test_{module_name}_protocol.py"
        rendered[filename] = (
            _render_test_module(
                module_name=module_name,
                env_class=env_class,
                env_module=env_module,
                oracle_module=oracle_module,
                group_name="protocol",
                cases=grouped_cases["protocol"],
                oracle_cases_by_plan=oracle_cases_by_plan,
            ),
            {
                "group_name": "protocol",
                "case_ids": [case.case_id for case in grouped_cases["protocol"]],
                "categories": sorted({case.category for case in grouped_cases["protocol"]}),
            },
        )
    if grouped_cases["edge"]:
        filename = f"test_{module_name}_edge.py"
        rendered[filename] = (
            _render_test_module(
                module_name=module_name,
                env_class=env_class,
                env_module=env_module,
                oracle_module=oracle_module,
                group_name="edge",
                cases=grouped_cases["edge"],
                oracle_cases_by_plan=oracle_cases_by_plan,
            ),
            {
                "group_name": "edge",
                "case_ids": [case.case_id for case in grouped_cases["edge"]],
                "categories": sorted({case.category for case in grouped_cases["edge"]}),
            },
        )
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
) -> str:
    heading = {
        "basic": "Basic, reset, negative, and repeated-operation tests rendered from the plan.",
        "protocol": "Protocol-focused tests rendered conservatively from handshake-oriented plan cases.",
        "edge": "Edge and boundary tests rendered conservatively from the structured plan.",
    }[group_name]
    case_blocks = "\n\n".join(
        _render_single_test_case(module_name=module_name, env_class=env_class, case=case, oracle_cases=oracle_cases_by_plan.get(case.case_id, []))
        for case in cases
    )
    return f'''"""Rendered {group_name} cocotb tests for `{module_name}`.

{heading}
"""

from __future__ import annotations

import cocotb

from .{env_module} import PLAN_CASES, {env_class}
from .{oracle_module} import linked_oracle_case_ids_for_plan_case, run_linked_plan_case

{case_blocks}
'''


def _render_single_test_case(
    *,
    module_name: str,
    env_class: str,
    case: TestCasePlan,
    oracle_cases: list[OracleCase],
) -> str:
    func_name = f"test_{_sanitize_identifier(case.case_id)}"
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
    comments = "\n    ".join(comment_lines)
    return f'''@cocotb.test()
async def {func_name}(dut):
    """{docstring}"""
    {comments}
    env = {env_class}(dut)
    await env.initialize()
    env.coverage.record_case_execution(
        {case.case_id!r},
        PLAN_CASES[{case.case_id!r}]["category"],
        list(PLAN_CASES[{case.case_id!r}].get("coverage_tags", [])),
    )
    await env.exercise_case({case.case_id!r})
    results = await run_linked_plan_case(env, {case.case_id!r})
    assert isinstance(results, list)
    assert linked_oracle_case_ids_for_plan_case({case.case_id!r}) == [result["case_id"] for result in results]
'''


def _camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_")) or "Rendered"


def _sanitize_identifier(name: str) -> str:
    sanitized = "".join(char if char.isalnum() or char == "_" else "_" for char in name)
    if sanitized and sanitized[0].isdigit():
        return f"case_{sanitized}"
    return sanitized or "rendered_case"
