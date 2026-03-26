"""Top-level package for cocoverify2."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cocoverify2")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = ["__version__"]
