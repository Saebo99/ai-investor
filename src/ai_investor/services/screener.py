"""Ticker screening utilities aligned with the investment strategy."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from ..models import TickerMetrics


def _normalize_keywords(values: Iterable[str]) -> set[str]:
    return {value.strip().lower() for value in values if value and value.strip()}


@dataclass(slots=True)
class TickerScreener:
    """Evaluate whether a ticker aligns with the long-term, low-risk strategy."""

    min_market_cap: float = 10_000_000_000  # USD-equivalent threshold (large cap bias)
    max_pe_ratio: float = 35.0
    max_forward_pe: float = 35.0
    max_beta: float = 1.4
    require_dividend: bool = True
    excluded_keywords: tuple[str, ...] = ("tobacco", "weapon", "arms", "gambling", "defense")
    _excluded_cache: set[str] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        self._excluded_cache = _normalize_keywords(self.excluded_keywords)

    def evaluate(self, metrics_data: dict) -> tuple[bool, list[str]]:
        """Return (is_candidate, reasons) for the provided metrics payload."""

        reasons: list[str] = []
        try:
            metrics = TickerMetrics.model_validate(metrics_data)
        except Exception as exc:  # noqa: BLE001
            return False, [f"invalid_metrics:{exc}"]

        market_cap = metrics.market_cap
        if market_cap is None or market_cap < self.min_market_cap:
            reasons.append("market_cap_too_small")

        if metrics.pe_ratio is not None and metrics.pe_ratio > self.max_pe_ratio:
            reasons.append("pe_ratio_too_high")

        if metrics.forward_pe is not None and metrics.forward_pe > self.max_forward_pe:
            reasons.append("forward_pe_too_high")
        if metrics.pe_ratio is None and metrics.forward_pe is None:
            reasons.append("missing_pe_ratio")

        if metrics.beta is not None and metrics.beta > self.max_beta:
            reasons.append("beta_too_high")

        if self.require_dividend:
            if metrics.dividend_yield is None or metrics.dividend_yield <= 0:
                reasons.append("requires_dividend")

        sector_tokens = " ".join(
            filter(
                None,
                (
                    metrics.sector,
                    metrics.industry,
                    (metrics.summary or "")[:200],
                ),
            )
        ).lower()

        for keyword in self._excluded_cache:
            if keyword and keyword in sector_tokens:
                reasons.append(f"excluded_sector:{keyword}")
                break

        return len(reasons) == 0, reasons
