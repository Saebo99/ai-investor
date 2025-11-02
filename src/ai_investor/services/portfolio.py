"""Portfolio analysis services."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..models import ActionRecommendation, Holding, Portfolio, TickerMetrics


@dataclass(slots=True)
class PortfolioAnalyzer:
    """Performs basic analysis on portfolio holdings."""

    portfolio: Portfolio

    def evaluate_holdings(self, metrics: dict[str, TickerMetrics]) -> list[ActionRecommendation]:
        suggestions: list[ActionRecommendation] = []
        for holding in self.portfolio.holdings:
            suggestion = self._evaluate_single(holding, metrics.get(holding.ticker))
            suggestions.append(suggestion)
        return suggestions

    def _evaluate_single(
        self,
        holding: Holding,
        metrics: TickerMetrics | None,
    ) -> ActionRecommendation:
        if not metrics:
            return ActionRecommendation(
                ticker=holding.ticker,
                action="watch",
                conviction="low",
                rationale="No fundamental metrics available; consider refreshing data.",
            )

        rationale_parts: list[str] = []
        action: str = "hold"
        conviction: str = "medium"

        if metrics.forward_pe and metrics.forward_pe > 32:
            action = "trim"
            conviction = "medium"
            rationale_parts.append("Forward P/E above conservative threshold (>32).")

        if metrics.dividend_yield and metrics.dividend_yield >= 0.015:
            rationale_parts.append(
                f"Offers a dividend yield of {metrics.dividend_yield:.2%}, supporting income goals."
            )
        elif metrics.dividend_yield is None:
            rationale_parts.append("Dividend data unavailable.")

        if metrics.market_cap and metrics.market_cap > 150e9:
            rationale_parts.append("Large-cap exposure aligns with risk constraints.")
        else:
            rationale_parts.append("Validate whether market capitalization meets scale preference.")

        if metrics.beta and metrics.beta > 1.4:
            rationale_parts.append("Elevated beta suggests higher volatility than desired.")
            if action != "trim":
                action = "hold"
                conviction = "low"

        if not rationale_parts:
            rationale_parts.append("No notable data available.")

        return ActionRecommendation(
            ticker=holding.ticker,
            action=action,  # type: ignore[arg-type]
            conviction=conviction,  # type: ignore[arg-type]
            rationale=" ".join(rationale_parts),
        )

    def spot_opportunities(
        self,
        shortlist: Iterable[str],
        metrics: dict[str, TickerMetrics],
    ) -> list[ActionRecommendation]:
        opportunities: list[ActionRecommendation] = []

        portfolio_tickers = {holding.ticker for holding in self.portfolio.holdings}
        for ticker in shortlist:
            if ticker in portfolio_tickers:
                continue
            data = metrics.get(ticker)
            if not data:
                continue

            action = "watch"
            conviction = "low"
            rationale_parts: list[str] = []

            if data.forward_pe and data.forward_pe <= 28:
                action = "buy"
                conviction = "medium"
                rationale_parts.append("Reasonable forward valuation relative to quality.")

            if data.dividend_yield and data.dividend_yield >= 0.02:
                rationale_parts.append("Attractive dividend yield exceeding 2%.")

            if data.market_cap and data.market_cap >= 200e9:
                rationale_parts.append("Mega-cap profile aligns with defensive bias.")

            if data.summary:
                rationale_parts.append(f"Summary: {data.summary}")

            if not rationale_parts:
                rationale_parts.append("Insufficient data to issue a strong signal.")

            opportunities.append(
                ActionRecommendation(
                    ticker=ticker,
                    action=action,  # type: ignore[arg-type]
                    conviction=conviction,  # type: ignore[arg-type]
                    rationale=" ".join(rationale_parts),
                )
            )

        return opportunities
