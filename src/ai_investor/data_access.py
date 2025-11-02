"""Local data access utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import DATA_DIR, DOCS_DIR
from .models import Portfolio


def _read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> Any:
    """Load JSON data from the given path."""

    return json.loads(_read_text(path))


def load_portfolio() -> Portfolio:
    """Return the current portfolio data."""

    raw = load_json(DATA_DIR / "portfolio.json")
    return Portfolio.model_validate(raw)


def load_ticker_shortlist() -> list[str]:
    """Return the shortlist of eligible tickers."""

    data = load_json(DATA_DIR / "shortlist.json")
    if not isinstance(data, list):
        raise ValueError("shortlist.json must contain a list of tickers.")
    return [str(item).upper() for item in data]


def save_ticker_shortlist(tickers: list[str]) -> None:
    """Persist the shortlist of eligible tickers."""

    path = DATA_DIR / "shortlist.json"
    payload = [str(item).upper() for item in tickers]
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_investment_strategy() -> str:
    """Return the investment strategy markdown."""

    return _read_text(DOCS_DIR / "investment_strategy.md")
