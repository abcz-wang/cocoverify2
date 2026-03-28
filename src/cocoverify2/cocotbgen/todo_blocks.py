"""Helpers for building stable LLM-fillable TODO blocks."""

from __future__ import annotations

from typing import Any


def build_todo_block(
    *,
    fill_kind: str,
    block_id: str,
    template_name: str,
    comment_lines: list[str],
    instructions: list[str],
    context: dict[str, Any],
    indent: str = "",
    case_id: str = "",
    oracle_case_id: str = "",
    check_id: str = "",
) -> tuple[str, dict[str, Any]]:
    """Build a TODO block string plus structured metadata."""
    marker_suffix = _marker_suffix(
        block_id=block_id,
        case_id=case_id,
        oracle_case_id=oracle_case_id,
        check_id=check_id,
    )
    start_marker = f"{indent}# TODO(cocoverify2:{fill_kind}) BEGIN {marker_suffix}"
    end_marker = f"{indent}# TODO(cocoverify2:{fill_kind}) END {marker_suffix}"
    lines = [start_marker]
    lines.extend(f"{indent}# {line}" for line in comment_lines if line)
    lines.append(f"{indent}pass")
    lines.append(end_marker)
    metadata = {
        "block_id": block_id,
        "fill_kind": fill_kind,
        "relative_path": "",
        "file_role": "",
        "template_name": template_name,
        "case_id": case_id,
        "oracle_case_id": oracle_case_id,
        "check_id": check_id,
        "start_marker": start_marker,
        "end_marker": end_marker,
        "instructions": list(instructions),
        "context": dict(context),
    }
    return "\n".join(lines), metadata


def _marker_suffix(
    *,
    block_id: str,
    case_id: str,
    oracle_case_id: str,
    check_id: str,
) -> str:
    parts = [f"block_id={block_id}"]
    if case_id:
        parts.append(f"case_id={case_id}")
    if oracle_case_id:
        parts.append(f"oracle_case_id={oracle_case_id}")
    if check_id:
        parts.append(f"check_id={check_id}")
    return " ".join(parts)

