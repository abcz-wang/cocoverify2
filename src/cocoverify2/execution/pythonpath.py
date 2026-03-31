"""Shared Python import-path helpers for execution backends."""

from __future__ import annotations

import os


def merge_pythonpath(required_entry: str, existing: str | None) -> str:
    """Prepend a required import root while preserving existing entries."""
    entries = [required_entry]
    if existing:
        entries.extend(item for item in existing.split(os.pathsep) if item and item != required_entry)
    return os.pathsep.join(entries)
