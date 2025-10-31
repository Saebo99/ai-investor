"""
Helpers for loading and validating strategy documents used to guide the agent.
"""

from __future__ import annotations

from pathlib import Path


def load_strategy(path: Path) -> str:
    """
    Load the investment strategy document as markdown text.
    """
    if not path.exists():
        return (
            "## Strategy Missing\n"
            "Define the investment strategy in the configured markdown file "
            "to guide the Claude agent's long-term decisions."
        )
    return path.read_text(encoding="utf-8")
