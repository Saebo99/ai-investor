"""Market data client mixing yfinance fundamentals with Tiingo news/search."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from ..models import NewsItem, TickerMetrics
from .tiingo import TiingoClient, TiingoError


class EODHDError(RuntimeError):
    """Raised when market data retrieval fails."""


def _coerce_float(value: Any) -> float | None:
    try:
        if value in (None, "", "None"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_get(fetcher, **kwargs) -> Any:
    try:
        return fetcher(**kwargs)
    except Exception:  # noqa: BLE001 - yfinance may raise for missing endpoints
        return None


def _extract_rating(summary: Any) -> str | None:
    if not isinstance(summary, dict):
        return None
    totals = summary.get("summary") or summary
    if not isinstance(totals, dict):
        return None
    best_key = None
    best_value = -1
    for key, value in totals.items():
        try:
            count = int(value)
        except (TypeError, ValueError):
            continue
        if count > best_value:
            best_key = key
            best_value = count
    if best_key:
        return str(best_key).replace("_", " ").title()
    return None


def _normalize_symbol(symbol: str) -> str:
    symbol = symbol.strip().upper()
    if symbol.endswith(".US"):
        return symbol[:-3]
    return symbol


def _extract_close(ticker: yf.Ticker) -> float | None:
    fast_info = getattr(ticker, "fast_info", None)
    if fast_info:
        candidates = [
            getattr(fast_info, "last_price", None),
            getattr(fast_info, "lastPrice", None),
            getattr(fast_info, "previous_close", None),
            getattr(fast_info, "previousClose", None),
        ]
        if isinstance(fast_info, dict):
            candidates.extend(
                fast_info.get(key)
                for key in ("last_price", "lastPrice", "previous_close", "previousClose")
            )
        for candidate in candidates:
            close = _coerce_float(candidate)
            if close is not None:
                return close

    history = ticker.history(period="5d", interval="1d")
    if not history.empty:
        return _coerce_float(history["Close"].iloc[-1])
    return None


class EODHDClient:
    """Asynchronous wrapper around yfinance fundamentals with Tiingo news."""

    def __init__(self) -> None:  # pragma: no cover - simple constructor
        self._tiingo = TiingoClient()

    @property
    def has_credentials(self) -> bool:
        # yfinance relies on public endpoints; assume availability.
        return True

    async def get_fundamentals(self, symbol: str) -> TickerMetrics:
        try:
            return await asyncio.to_thread(self._build_fundamentals, symbol)
        except Exception as exc:  # noqa: BLE001
            raise EODHDError(f"Failed to fetch fundamentals for {symbol}: {exc}") from exc

    async def get_news(
        self,
        symbol: str,
        *,
        limit: int = 5,
        timeframe: str | None = None,
    ) -> list[NewsItem]:
        try:
            return await self._tiingo.get_news(symbol, limit=limit, timeframe=timeframe)
        except TiingoError as exc:
            raise EODHDError(f"Failed to fetch news for {symbol}: {exc}") from exc

    async def get_eod_metrics(self, symbol: str) -> TickerMetrics:
        try:
            return await asyncio.to_thread(self._build_eod_metrics, symbol)
        except Exception as exc:  # noqa: BLE001
            raise EODHDError(f"Failed to fetch price snapshot for {symbol}: {exc}") from exc

    async def get_estimate_data(self, symbol: str) -> dict[str, Any]:
        try:
            return await asyncio.to_thread(self._build_estimate_data, symbol)
        except Exception as exc:  # noqa: BLE001
            raise EODHDError(f"Failed to fetch analyst estimates for {symbol}: {exc}") from exc

    async def get_growth_estimates(self, symbol: str) -> dict[str, Any]:
        try:
            return await asyncio.to_thread(self._build_growth_estimates, symbol)
        except Exception as exc:  # noqa: BLE001
            raise EODHDError(f"Failed to fetch growth estimates for {symbol}: {exc}") from exc

    async def search_tickers(self, query: str, limit: int = 25) -> list[dict[str, Any]]:
        try:
            return await self._tiingo.search_tickers(query, limit=limit)
        except TiingoError as exc:
            raise EODHDError(f"Failed to search Tiingo tickers: {exc}") from exc

    # ---------- Internal helpers ----------

    def _build_fundamentals(self, symbol: str) -> TickerMetrics:
        yahoo_symbol = _normalize_symbol(symbol)
        ticker = yf.Ticker(yahoo_symbol)

        info = ticker.info or {}
        close = _extract_close(ticker)
        summary = (
            info.get("longBusinessSummary")
            or info.get("longSummary")
            or info.get("shortBusinessSummary")
        )

        recommendations = _safe_get(ticker.get_recommendations_summary, as_dict=True)

        metrics = TickerMetrics(
            ticker=symbol.strip().upper(),
            company_name=info.get("longName") or info.get("shortName"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            latest_close=close,
            market_cap=_coerce_float(info.get("marketCap")),
            pe_ratio=_coerce_float(info.get("trailingPE")),
            forward_pe=_coerce_float(info.get("forwardPE")),
            dividend_yield=_coerce_float(info.get("dividendYield")),
            return_on_equity=_coerce_float(info.get("returnOnEquity")),
            debt_to_equity=_coerce_float(info.get("debtToEquity")),
            beta=_coerce_float(info.get("beta")),
            analyst_rating=_extract_rating(recommendations),
            summary=summary.strip()[:600] if isinstance(summary, str) else None,
        )
        return metrics

    def _build_eod_metrics(self, symbol: str) -> TickerMetrics:
        yahoo_symbol = _normalize_symbol(symbol)
        ticker = yf.Ticker(yahoo_symbol)
        close = _extract_close(ticker)
        if close is None:
            raise ValueError("No recent price data available")

        history = ticker.history(period="1mo", interval="1d")
        quoted_date: str | None = None
        if not history.empty:
            last_index = history.index[-1]
            if isinstance(last_index, datetime):
                quoted_date = last_index.date().isoformat()
            else:
                quoted_date = str(last_index)

        summary_parts = [
            "Latest end-of-day price snapshot sourced from Yahoo Finance.",
        ]
        if quoted_date:
            summary_parts.append(f"Quote date: {quoted_date}.")

        return TickerMetrics(
            ticker=symbol.strip().upper(),
            latest_close=close,
            summary=" ".join(summary_parts),
        )

    def _build_estimate_data(self, symbol: str) -> dict[str, Any]:
        yahoo_symbol = _normalize_symbol(symbol)
        ticker = yf.Ticker(yahoo_symbol)
        return {
            "recommendations_summary": _safe_get(ticker.get_recommendations_summary, as_dict=True) or {},
            "earnings_estimate": _safe_get(ticker.get_earnings_estimate, as_dict=True) or {},
            "revenue_estimate": _safe_get(ticker.get_revenue_estimate, as_dict=True) or {},
        }

    def _build_growth_estimates(self, symbol: str) -> dict[str, Any]:
        yahoo_symbol = _normalize_symbol(symbol)
        ticker = yf.Ticker(yahoo_symbol)
        data = _safe_get(ticker.get_growth_estimates, as_dict=True)
        return data or {}


__all__ = ["EODHDClient", "EODHDError", "_coerce_float"]
