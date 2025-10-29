"""Data models for investment theses."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Recommendation(str, Enum):
    BUY = "buy"
    HOLD = "hold"
    TRIM = "trim"
    EXIT = "exit"


class NarrativeInsight(BaseModel):
    headline: str
    sentiment: str = Field(default="neutral")
    summary: str


class Thesis(BaseModel):
    ticker: str
    recommendation: Recommendation
    conviction: float = Field(ge=0.0, le=1.0)
    quantitative_score: float = Field(ge=0.0, le=1.0)
    qualitative_score: float = Field(ge=0.0, le=1.0)
    rationale: str
    risks: List[str] = Field(default_factory=list)
    catalysts: List[str] = Field(default_factory=list)
    insights: List[NarrativeInsight] = Field(default_factory=list)
    suggested_action: Optional[str] = None
