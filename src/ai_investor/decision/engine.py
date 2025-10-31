"""Translate raw metrics into explainable investment theses."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Optional

from ai_investor.agents.claude_agent import ClaudeAnalyst
from ai_investor.decision.models import NarrativeInsight, Recommendation, Thesis

logger = logging.getLogger(__name__)


class DecisionEngine:
    """Combine quantitative metrics and narrative insights."""

    def __init__(self, positions: Optional[List[dict]] = None, thesis_log_path: Optional[Path] = None) -> None:
        self._analyst = ClaudeAnalyst()
        self._positions = {pos.get("ticker"): pos for pos in (positions or [])}
        self._thesis_log_path = thesis_log_path or Path("data/thesis_log.jsonl")
        self._min_holding_days = 90  # Minimum 90 days before considering exit
        self._stability_weight = 0.15  # Weight for stability score

    def _score_stability(self, fundamentals: Dict[str, object]) -> float:
        """Score stability indicators: low debt, consistent earnings, mature business."""
        debt_to_equity = float(fundamentals.get("DebtToEquity", 100) or 100)
        beta = float(fundamentals.get("Beta", 1.5) or 1.5)
        earnings_stability = float(fundamentals.get("EarningsStability", 0.5) or 0.5)  # Placeholder
        
        # Lower debt is better (penalize above 1.0)
        debt_score = max(0, 1 - min(debt_to_equity / 2.0, 1.0))
        # Lower beta is better for long-term stability (penalize above 1.0)
        beta_score = max(0, 1 - min(abs(beta - 0.8) / 1.2, 1.0))
        # Reward consistent earnings (assumed metric)
        stability_score = debt_score * 0.4 + beta_score * 0.4 + earnings_stability * 0.2
        
        logger.debug("Stability score computed as %.3f (debt=%.2f, beta=%.2f)", 
                     stability_score, debt_to_equity, beta)
        return max(0.0, min(stability_score, 1.0))

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

    def _get_first_purchase_date(self, ticker: str) -> Optional[datetime]:
        """Read thesis log to find first BUY recommendation date for holding period tracking."""
        if not self._thesis_log_path.exists():
            return None
        
        try:
            with self._thesis_log_path.open("r", encoding="utf-8") as f:
                for line in f:
                    record = json.loads(line)
                    if record.get("ticker") == ticker and record.get("recommendation") == "buy":
                        ts = record.get("ts")
                        if ts:
                            return datetime.fromisoformat(ts)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Failed to parse thesis log for %s: %s", ticker, exc)
        return None

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

    def _derive_recommendation(
        self, 
        ticker: str,
        quantitative: float, 
        qualitative: float, 
        stability: float,
        is_held: bool
    ) -> Recommendation:
        # Incorporate stability into the blend for long-term focus
        blended = 0.5 * quantitative + 0.35 * qualitative + 0.15 * stability
        
        # Check holding period for exit protection
        holding_days = 0
        if is_held:
            first_purchase = self._get_first_purchase_date(ticker)
            if first_purchase:
                holding_days = (datetime.utcnow() - first_purchase).days
                logger.info("Ticker %s held for %d days", ticker, holding_days)
        
        # Position-aware thresholds
        if is_held:
            # More conservative thresholds for existing positions (favor holding)
            # Require stronger evidence to exit (lower threshold)
            # Don't recommend buying more of what we already own
            if holding_days < self._min_holding_days:
                # Within minimum holding period - never exit unless catastrophic
                if blended >= 0.35:
                    return Recommendation.HOLD
                else:
                    logger.warning(
                        "Ticker %s scoring %.2f within minimum holding period - forcing HOLD",
                        ticker, blended
                    )
                    return Recommendation.HOLD
            
            # After minimum holding period
            if blended >= 0.65:
                return Recommendation.HOLD  # Don't buy more
            if blended >= 0.45:
                return Recommendation.HOLD
            if blended >= 0.35:
                return Recommendation.TRIM
            return Recommendation.EXIT
        else:
            # Standard thresholds for new positions (slightly higher bar to avoid trend-chasing)
            if blended >= 0.75:  # Higher threshold for new buys
                return Recommendation.BUY
            if blended >= 0.60:
                return Recommendation.HOLD  # Wait and watch
            return Recommendation.HOLD  # Don't recommend positions we don't own

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
        
        # Score all dimensions
        quantitative_score = self._score_quantitative(fundamentals)
        qualitative_score = self._score_qualitative(insights)
        stability_score = self._score_stability(fundamentals)
        
        # Check if position is currently held
        is_held = ticker in self._positions
        position_info = ""
        if is_held:
            pos = self._positions[ticker]
            position_info = f"Currently held: {pos.get('quantity', 0)} shares at avg ${pos.get('average_price', 0):.2f}. "
        
        # Derive recommendation with position awareness
        recommendation = self._derive_recommendation(
            ticker, quantitative_score, qualitative_score, stability_score, is_held
        )
        
        # Enhanced rationale with long-term focus
        rationale_lines = [
            f"Long-term investment analysis for {ticker}:",
            position_info if position_info else "Not currently held.",
            f"Quantitative score: {quantitative_score:.2f} (dividend yield, profitability, ROA/ROE)",
            f"Qualitative score: {qualitative_score:.2f} (recent news sentiment)",
            f"Stability score: {stability_score:.2f} (debt levels, beta, earnings consistency)",
            f"Blended conviction: {0.5 * quantitative_score + 0.35 * qualitative_score + 0.15 * stability_score:.2f}",
        ]
        
        if is_held:
            first_purchase = self._get_first_purchase_date(ticker)
            if first_purchase:
                holding_days = (datetime.utcnow() - first_purchase).days
                rationale_lines.append(f"Holding period: {holding_days} days (min threshold: {self._min_holding_days} days)")
        
        thesis = Thesis(
            ticker=ticker,
            recommendation=recommendation,
            conviction=0.5 * quantitative_score + 0.35 * qualitative_score + 0.15 * stability_score,
            quantitative_score=quantitative_score,
            qualitative_score=qualitative_score,
            rationale="\n".join(rationale_lines),
            insights=insights,
            catalysts=catalysts,
            risks=risks,
        )
        return thesis
