"""Domain models and structured outputs for the AI Investor server."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Holding(BaseModel):
    ticker: str
    name: str
    shares: float = Field(ge=0)
    average_cost: float = Field(ge=0)
    target_weight: float | None = Field(default=None, ge=0, le=1)


class Portfolio(BaseModel):
    currency: str = Field(default="USD", min_length=3, max_length=3)
    available_funds: float = Field(default=0, ge=0)
    holdings: list[Holding] = Field(default_factory=list)


class TickerMetrics(BaseModel):
    ticker: str
    company_name: str | None = None
    sector: str | None = None
    industry: str | None = None
    latest_close: float | None = Field(default=None, ge=0)
    market_cap: float | None = Field(default=None, ge=0)
    pe_ratio: float | None = Field(default=None, ge=0)
    forward_pe: float | None = Field(default=None, ge=0)
    dividend_yield: float | None = Field(default=None, ge=0)
    return_on_equity: float | None = None
    debt_to_equity: float | None = None
    beta: float | None = None
    analyst_rating: str | None = None
    summary: str | None = None


class NewsItem(BaseModel):
    title: str
    url: str
    published_at: datetime
    site: str | None = None
    sentiment: str | None = None
    summary: str | None = None


class FearGreedIndex(BaseModel):
    value: int
    rating: Literal["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
    description: str
    previous_close: int | None = None
    previous_1_week: int | None = None
    previous_1_month: int | None = None
    previous_1_year: int | None = None


class ActionRecommendation(BaseModel):
    ticker: str
    action: Literal["buy", "hold", "trim", "watch"]
    conviction: Literal["low", "medium", "high"]
    rationale: str


class AdviceReport(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    strategy_summary: str
    portfolio_overview: str
    fear_greed_index: FearGreedIndex | None = None
    holding_evaluations: list[ActionRecommendation] = Field(default_factory=list)
    shortlist_opportunities: list[ActionRecommendation] = Field(default_factory=list)
    cash_management_plan: str | None = None
