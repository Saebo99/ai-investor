"""
Typed models used throughout analysis workflows.
"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class CompanySnapshot(BaseModel):
    """Aggregated view of a company with fundamental and market data."""

    ticker: str
    name: str | None = None
    fundamentals: Dict[str, float] = Field(default_factory=dict)
    quote: Dict[str, float] = Field(default_factory=dict)
    qualitative_notes: List[str] = Field(default_factory=list)

    @property
    def dividend_yield(self) -> float | None:
        return self.fundamentals.get("dividend_yield")

    @property
    def pe_ratio(self) -> float | None:
        return self.fundamentals.get("pe_ratio")


class InvestmentDecision(BaseModel):
    """Action the portfolio manager should consider."""

    ticker: str
    action: str
    weight_delta: float
    rationale: str
