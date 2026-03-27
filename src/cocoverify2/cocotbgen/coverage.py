"""Helpers for rendering coverage scaffolds."""

from __future__ import annotations

from pprint import pformat

from cocoverify2.core.models import TestPlan


def render_coverage_module(module_name: str, plan: TestPlan) -> tuple[str, dict[str, object]]:
    """Render the `<dut>_coverage.py` scaffold and summary."""
    class_name = f"{_camel(module_name)}Coverage"
    coverage_tags = sorted({tag for case in plan.cases for tag in case.coverage_tags})
    case_categories = sorted({case.category for case in plan.cases})
    content = f'''"""Coverage scaffold for `{module_name}`.

This file intentionally keeps coverage lightweight in Phase 4. It records planned
coverage tags and oracle activity without introducing a full backend yet.
"""

from __future__ import annotations

COVERAGE_TAGS = {pformat(coverage_tags)}
CASE_CATEGORIES = {pformat(case_categories)}


class {class_name}:
    """Minimal coverage registry rendered from plan coverage tags."""

    def __init__(self) -> None:
        self.case_hits: dict[str, int] = {{}}
        self.tag_hits: dict[str, int] = {{tag: 0 for tag in COVERAGE_TAGS}}
        self.oracle_checks: list[dict[str, object]] = []

    def record_case_execution(self, case_id: str, category: str, tags: list[str]) -> None:
        """Record that a rendered test case was exercised."""
        self.case_hits[case_id] = self.case_hits.get(case_id, 0) + 1
        for tag in tags:
            self.tag_hits[tag] = self.tag_hits.get(tag, 0) + 1
        self.oracle_checks.append({{"case_id": case_id, "category": category, "kind": "case_execution"}})

    def record_oracle_check(self, check_id: str, check_type: str, strictness: str) -> None:
        """Record that an oracle check helper was invoked."""
        self.oracle_checks.append(
            {{"check_id": check_id, "check_type": check_type, "strictness": strictness, "kind": "oracle_check"}}
        )

    def summary(self) -> dict[str, object]:
        """Return a lightweight summary for later stages."""
        return {{
            "case_hits": dict(self.case_hits),
            "tag_hits": dict(self.tag_hits),
            "oracle_check_count": len(self.oracle_checks),
        }}
'''
    summary = {
        "class_name": class_name,
        "coverage_tags": coverage_tags,
        "case_categories": case_categories,
    }
    return content, summary


def _camel(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_")) or "Rendered"
