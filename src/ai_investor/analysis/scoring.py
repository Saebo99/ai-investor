"""
Company analysis and filtering logic aligned with the stated investment strategy.
"""

from __future__ import annotations

from typing import Iterable, List

from .models import CompanySnapshot, InvestmentDecision


class FundamentalAnalyzer:
    """
    Applies conservative screening rules to potential investments.
    """

    def __init__(
        self,
        min_dividend_yield: float = 0.02,
        max_pe_ratio: float = 30.0,
    ) -> None:
        self.min_dividend_yield = min_dividend_yield
        self.max_pe_ratio = max_pe_ratio

    def filter_candidates(self, companies: Iterable[CompanySnapshot]) -> list[CompanySnapshot]:
        """
        Retain only companies that meet baseline conservative thresholds.
        """
        results: list[CompanySnapshot] = []
        for company in companies:
            dividend = company.dividend_yield
            pe_ratio = company.pe_ratio
            if dividend is None or dividend < self.min_dividend_yield:
                continue
            if pe_ratio is None or pe_ratio > self.max_pe_ratio:
                continue
            results.append(company)
        return results

    def rank(self, companies: Iterable[CompanySnapshot]) -> list[CompanySnapshot]:
        """
        Order companies by combined dividend yield and inverse P/E ratio.
        """
        scored = []
        for company in companies:
            dividend = company.dividend_yield or 0.0
            pe_ratio = company.pe_ratio or self.max_pe_ratio
            score = dividend - (pe_ratio / max(self.max_pe_ratio, 1.0))
            scored.append((score, company))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [company for _, company in scored]

    def propose_actions(
        self,
        ranked_companies: Iterable[CompanySnapshot],
        current_positions: dict[str, float],
        max_positions: int = 15,
    ) -> List[InvestmentDecision]:
        """
        Convert ranked list into high-level investment actions.
        """
        decisions: List[InvestmentDecision] = []
        for company in ranked_companies:
            position_size = current_positions.get(company.ticker, 0.0)
            if position_size <= 0:
                action = "buy"
                weight_delta = 0.05
            else:
                action = "reassess_hold"
                weight_delta = 0.0
            decisions.append(
                InvestmentDecision(
                    ticker=company.ticker,
                    action=action,
                    weight_delta=weight_delta,
                    rationale="Initial heuristic decision; replace with Claude-guided reasoning.",
                )
            )
            if len(decisions) >= max_positions:
                break
        return decisions
