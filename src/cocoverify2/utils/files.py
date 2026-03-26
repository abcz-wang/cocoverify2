"""Filesystem helpers for cocoverify2 artifacts and fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml


def ensure_dir(path: Path) -> Path:
    """Create a directory if needed and return the normalized path."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text(path: Path, content: str) -> Path:
    """Write UTF-8 text to a path, creating parent directories as needed."""
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    return path


def read_text(path: Path) -> str:
    """Read UTF-8 text from a path."""
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: Any, *, indent: int = 2) -> Path:
    """Serialize JSON payload to disk with deterministic formatting."""
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=indent, sort_keys=True, default=str), encoding="utf-8")
    return path


def read_json(path: Path) -> Any:
    """Read JSON content from disk."""
    return json.loads(read_text(path))


def write_yaml(path: Path, payload: Any) -> Path:
    """Serialize YAML payload to disk with stable key ordering."""
    ensure_dir(path.parent)
    path.write_text(yaml.safe_dump(payload, sort_keys=False, allow_unicode=False), encoding="utf-8")
    return path
