"""Advice generation services."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from ..models import (
    ActionRecommendation,
    AdviceReport,
    FearGreedIndex,
    Portfolio,
    TickerMetrics,
)


class AdviceComposer:
    """Builds natural language advice reports."""

    def __init__(
        self,
        strategy_markdown: str,
        portfolio: Portfolio,
        fear_greed: FearGreedIndex | None,
        holding_recs: Iterable[ActionRecommendation],
        shortlist_recs: Iterable[ActionRecommendation],
    ) -> None:
        self.strategy_markdown = strategy_markdown
        self.portfolio = portfolio
        self.fear_greed = fear_greed
        self.holding_recs = list(holding_recs)
        self.shortlist_recs = list(shortlist_recs)

    def build(self) -> AdviceReport:
        return AdviceReport(
            generated_at=datetime.utcnow(),
            strategy_summary=self._summarize_strategy(),
            portfolio_overview=self._summarize_portfolio(),
            fear_greed_index=self.fear_greed,
            holding_evaluations=self.holding_recs,
            shortlist_opportunities=self.shortlist_recs,
            cash_management_plan=self._cash_plan(),
        )

    def _summarize_strategy(self) -> str:
        preview = self.strategy_markdown.strip().splitlines()
        if preview:
            return "\n".join(preview[:8])
        return "No strategy summary available."

    def _summarize_portfolio(self) -> str:
        holdings_summary = [
            f"- {h.ticker}: {h.shares:.2f} shares @ {h.average_cost:.2f}"
            for h in self.portfolio.holdings
        ]
        holdings_text = "\n".join(holdings_summary) if holdings_summary else "No holdings recorded."
        return (
            f"Currency: {self.portfolio.currency}\n"
            f"Available funds: {self.portfolio.available_funds:.2f}\n"
            f"Holdings:\n{holdings_text}"
        )

    def _cash_plan(self) -> str | None:
        if self.portfolio.available_funds <= 0:
            return None

        if not self.shortlist_recs:
            return "Hold cash until a shortlist candidate meets valuation criteria."

        buy_targets = [
            rec for rec in self.shortlist_recs if rec.action == "buy" and rec.conviction != "low"
        ]
        if not buy_targets:
            return "Maintain cash position while monitoring shortlist opportunities."

        target_tickers = ", ".join(rec.ticker for rec in buy_targets)
        return (
            f"Consider deploying capital into {target_tickers} using staged entries "
            "to respect risk constraints."
        )


def format_recommendation_summary(
    recommendations: Iterable[ActionRecommendation],
    metrics: dict[str, TickerMetrics],
) -> str:
    """Return a human-readable summary blending recommendations with key metrics."""

    lines: list[str] = []
    for rec in recommendations:
        data = metrics.get(rec.ticker)
        valuation = f"Forward P/E: {data.forward_pe:.1f}" if data and data.forward_pe else "P/E: N/A"
        dividend = (
            f"Dividend Yield: {data.dividend_yield:.2%}"
            if data and data.dividend_yield
            else "Dividend: N/A"
        )
        lines.append(
            f"{rec.ticker} → {rec.action.upper()} ({rec.conviction}) | {valuation} | {dividend}\n"
            f"Reasoning: {rec.rationale}"
        )
    return "\n\n".join(lines)
