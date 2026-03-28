"""Template loader tests for cocoverify2 cocotb generation."""

from __future__ import annotations

import pytest

from cocoverify2.cocotbgen.template_loader import load_template, render_template


def test_load_template_reads_bundled_template() -> None:
    template_text = load_template("env_module.py.tmpl")

    assert "Environment helpers" in template_text
    assert "${module_name}" in template_text


def test_load_template_raises_for_missing_template() -> None:
    with pytest.raises(FileNotFoundError):
        load_template("missing_template.py.tmpl")


def test_render_template_raises_for_missing_placeholder() -> None:
    with pytest.raises(ValueError):
        render_template("test_case.py.tmpl", case_identifier="basic_001")
