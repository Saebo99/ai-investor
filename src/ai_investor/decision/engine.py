"""Translate raw metrics into explainable investment theses."""

from __future__ import annotations

import logging
from statistics import mean
from typing import Dict, Iterable, List

from ai_investor.agents.claude_agent import ClaudeAnalyst
from ai_investor.decision.models import NarrativeInsight, Recommendation, Thesis

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Combine quantitative metrics and narrative insights."""

    def __init__(self) -> None:
        self._analyst = ClaudeAnalyst()

    def _score_quantitative(self, fundamentals: Dict[str, object]) -> float:
        dividend_yield = float(fundamentals.get("DividendYield", 0) or 0)
        payout_ratio = float(fundamentals.get("PayoutRatio", 0) or 0)
        net_margin = float(fundamentals.get("NetProfitMargin", 0) or 0)
        score = 0.0
        score += min(dividend_yield / 6.0, 1.0) * 0.3
        score += (1 - min(abs(payout_ratio - 50) / 50, 1.0)) * 0.2
        score += min(max(net_margin, 0) / 30.0, 1.0) * 0.2
        roa = float(fundamentals.get("ReturnOnAssetsTTM", 0) or 0)
        roe = float(fundamentals.get("ReturnOnEquityTTM", 0) or 0)
        score += min(max(roa, 0) / 15.0, 1.0) * 0.15
        score += min(max(roe, 0) / 20.0, 1.0) * 0.15
        logger.debug("Quantitative score computed as %.3f", score)
        return max(0.0, min(score, 1.0))

    def _score_qualitative(self, insights: Iterable[NarrativeInsight]) -> float:
        mapped = []
        for item in insights:
            if item.sentiment == "positive":
                mapped.append(0.75)
            elif item.sentiment == "negative":
                mapped.append(0.25)
            else:
                mapped.append(0.5)
        if not mapped:
            return 0.5
        return max(0.0, min(mean(mapped), 1.0))

    def _derive_recommendation(self, quantitative: float, qualitative: float) -> Recommendation:
        blended = 0.6 * quantitative + 0.4 * qualitative
        if blended >= 0.7:
            return Recommendation.BUY
        if blended >= 0.55:
            return Recommendation.HOLD
        if blended >= 0.4:
            return Recommendation.TRIM
        return Recommendation.EXIT

    def evaluate(self, ticker: str, fundamentals: Dict[str, object], news: List[dict]) -> Thesis:
        insights_payload = self._analyst.summarize_news(ticker, news)
        insights = []
        catalysts: List[str] = []
        risks: List[str] = []
        for item in insights_payload:
            insights.append(
                NarrativeInsight(
                    headline=item.get("headline", ""),
                    sentiment=item.get("sentiment", "neutral"),
                    summary=item.get("summary", ""),
                )
            )
            if item.get("catalyst"):
                catalysts.append(item["catalyst"])
            if item.get("risk"):
                risks.append(item["risk"])
        quantitative_score = self._score_quantitative(fundamentals)
        qualitative_score = self._score_qualitative(insights)
        recommendation = self._derive_recommendation(quantitative_score, qualitative_score)
        rationale_lines = [
            f"Quantitative score {quantitative_score:.2f} based on dividend yield and profitability.",
            f"Qualitative score {qualitative_score:.2f} from recent narratives.",
        ]
        thesis = Thesis(
            ticker=ticker,
            recommendation=recommendation,
            conviction=0.6 * quantitative_score + 0.4 * qualitative_score,
            quantitative_score=quantitative_score,
            qualitative_score=qualitative_score,
            rationale="\n".join(rationale_lines),
            insights=insights,
            catalysts=catalysts,
            risks=risks,
        )
        return thesis
