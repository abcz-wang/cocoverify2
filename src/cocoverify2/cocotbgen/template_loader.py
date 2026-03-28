"""Small deterministic template loader for cocotb rendering."""

from __future__ import annotations

from importlib import resources
from string import Template


_TEMPLATE_ROOT = resources.files("cocoverify2.cocotbgen").joinpath("templates")


def load_template(template_name: str) -> str:
    """Load a bundled template by file name."""
    template_path = _TEMPLATE_ROOT.joinpath(template_name)
    if not template_path.is_file():
        raise FileNotFoundError(f"Template does not exist: {template_name}")
    return template_path.read_text(encoding="utf-8")


def render_template(template_name: str, **context: object) -> str:
    """Render a bundled template with strict placeholder substitution."""
    template_text = load_template(template_name)
    try:
        return Template(template_text).substitute(context)
    except KeyError as exc:
        missing = exc.args[0]
        raise ValueError(f"Template {template_name!r} requires placeholder {missing!r}") from exc

