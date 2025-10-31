"""
Top-level package for the AI Investor agent framework.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("ai-investor")
except PackageNotFoundError:
    __version__ = "0.0.0"

__all__ = ["__version__"]
