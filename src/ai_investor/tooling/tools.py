"""MCP tool implementations."""

from __future__ import annotations

import asyncio
from typing import Any

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.session import ServerSession

from ..data_access import (
    load_investment_strategy,
    load_portfolio,
    load_ticker_shortlist,
    save_ticker_shortlist,
)
from ..integrations.eodhd import EODHDClient, EODHDError
from ..integrations.fear_greed import FearGreedClient, FearGreedError
from ..models import AdviceReport, Portfolio, TickerMetrics
from ..services.advice import AdviceComposer, format_recommendation_summary
from ..services.portfolio import PortfolioAnalyzer
from ..services.screener import TickerScreener

mcp = FastMCP("AI Investor MCP Server")

DEFAULT_NEWS_TIMEFRAME = "7d"


# ---------- Helper functions ----------


def _serialize_portfolio(portfolio: Portfolio) -> dict[str, Any]:
    return portfolio.model_dump()


def _serialize_metrics(metrics: TickerMetrics | None) -> dict[str, Any]:
    return metrics.model_dump() if metrics else {}


async def _gather_metrics(
    client: EODHDClient,
    tickers: set[str],
    ctx: Context[ServerSession, None] | None = None,
) -> dict[str, TickerMetrics]:
    results: dict[str, TickerMetrics] = {}

    if not tickers:
        return results

    if not client.has_credentials:
        if ctx:
            await ctx.warning("Market data provider unavailable; skipping live metrics fetch.")
        return results

    async def fetch(symbol: str) -> tuple[str, TickerMetrics | None]:
        try:
            return symbol, await client.get_fundamentals(symbol)
        except EODHDError as exc:
            if ctx:
                await ctx.warning(f"Failed to fetch fundamentals for {symbol}: {exc}")
            return symbol, None

    tasks = [fetch(ticker) for ticker in sorted(tickers)]
    for coro in asyncio.as_completed(tasks):
        symbol, data = await coro
        if data:
            results[symbol] = data
    return results


async def _fetch_ticker_payload(
    client: EODHDClient,
    ticker: str,
    *,
    fetch_metrics: bool = True,
    fetch_estimates: bool = True,
    fetch_growth: bool = False,
    fetch_news: bool = False,
    news_limit: int = 5,
    news_timeframe: str = DEFAULT_NEWS_TIMEFRAME,
) -> dict[str, Any]:
    symbol = ticker.upper().strip()
    payload: dict[str, Any] = {"ticker": symbol}

    metrics_success = True
    metrics_error: str | None = None

    if fetch_metrics:
        try:
            metrics = await client.get_fundamentals(symbol)
        except EODHDError:
            try:
                metrics = await client.get_eod_metrics(symbol)
            except EODHDError as fallback_exc:
                metrics_success = False
                metrics_error = str(fallback_exc)
                payload["metrics_error"] = metrics_error
            else:
                payload["metrics"] = _serialize_metrics(metrics)
                payload["data_source"] = "end_of_day"
                payload["note"] = (
                    "Detailed fundamentals were unavailable; returned a recent "
                    "end-of-day price snapshot from Yahoo Finance."
                )
        else:
            payload["metrics"] = _serialize_metrics(metrics)
            payload["data_source"] = "fundamentals"

    if fetch_estimates:
        try:
            estimates = await client.get_estimate_data(symbol)
            payload.update(estimates)
        except EODHDError as exc:
            payload["estimates_error"] = str(exc)

    if fetch_growth:
        try:
            payload["growth_estimates"] = await client.get_growth_estimates(symbol)
        except EODHDError as exc:
            payload["growth_estimates_error"] = str(exc)

    if fetch_news:
        limit = max(news_limit, 0)
        try:
            news_items = await client.get_news(symbol, limit=limit, timeframe=news_timeframe)
            payload["news"] = [item.model_dump() for item in news_items]
        except EODHDError as exc:
            payload["news_error"] = str(exc)

    if fetch_metrics:
        payload["success"] = metrics_success
        if not metrics_success:
            payload.setdefault("error", metrics_error or "Unable to fetch metrics.")
    else:
        payload["success"] = True

    return payload


def _normalize_tickers(values: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for entry in values:
        symbol = entry.upper().strip()
        if not symbol or symbol in seen:
            continue
        seen.add(symbol)
        normalized.append(symbol)
    return normalized


async def fetch_ticker_data(
    ticker: str,
    *,
    include_news: bool = False,
    news_timeframe: str = DEFAULT_NEWS_TIMEFRAME,
) -> dict[str, Any]:
    """Return fundamental metrics for a ticker, optionally including recent news."""

    client = EODHDClient()
    return await _fetch_ticker_payload(
        client,
        ticker,
        fetch_metrics=True,
        fetch_estimates=True,
        fetch_growth=True,
        fetch_news=include_news,
        news_timeframe=news_timeframe,
    )


async def fetch_ticker_news(
    ticker: str,
    *,
    limit: int = 5,
    timeframe: str = DEFAULT_NEWS_TIMEFRAME,
) -> dict[str, Any]:
    """Return recent news articles and growth figures for the provided ticker."""

    client = EODHDClient()
    return await _fetch_ticker_payload(
        client,
        ticker,
        fetch_metrics=False,
        fetch_estimates=False,
        fetch_growth=True,
        fetch_news=True,
        news_limit=limit,
        news_timeframe=timeframe,
    )


# ---------- Tool registrations ----------


@mcp.tool()
async def portfolio() -> dict[str, Any]:
    """Return the current portfolio snapshot."""

    data = load_portfolio()
    return {
        "success": True,
        "portfolio": _serialize_portfolio(data),
    }


@mcp.tool()
async def fetch_ticker_shortlist() -> dict[str, Any]:
    """Return the shortlist of approved tickers."""

    shortlist = load_ticker_shortlist()
    return {
        "success": True,
        "shortlist": shortlist,
    }


@mcp.tool()
async def fetch_investment_strategy() -> dict[str, Any]:
    """Return the investment strategy markdown."""

    strategy = load_investment_strategy()
    return {
        "success": True,
        "strategy_markdown": strategy,
    }




@mcp.tool()
async def fetch_ticker_details(
    ticker: str,
    news_limit: int = 5,
    news_timeframe: str = DEFAULT_NEWS_TIMEFRAME,
    include_growth_estimates: bool = True,
) -> dict[str, Any]:
    """Fetch metrics, estimates, growth projections, and news for a single ticker."""

    client = EODHDClient()
    payload = await _fetch_ticker_payload(
        client,
        ticker,
        fetch_metrics=True,
        fetch_estimates=True,
        fetch_growth=include_growth_estimates,
        fetch_news=True,
        news_limit=news_limit,
        news_timeframe=news_timeframe,
    )
    return payload


@mcp.tool()
async def fetch_multiple_ticker_details(
    tickers: list[str],
    news_limit: int = 5,
    news_timeframe: str = DEFAULT_NEWS_TIMEFRAME,
    include_growth_estimates: bool = True,
    include_estimates: bool = True,
) -> dict[str, Any]:
    """Gather data and news for several tickers in parallel."""

    normalized = _normalize_tickers(tickers)

    if not normalized:
        return {"success": True, "results": []}

    client = EODHDClient()
    limit = max(news_limit, 0)

    async def fetch(symbol: str) -> dict[str, Any]:
        return await _fetch_ticker_payload(
            client,
            symbol,
            fetch_metrics=True,
            fetch_estimates=include_estimates,
            fetch_growth=include_growth_estimates,
            fetch_news=True,
            news_limit=limit,
            news_timeframe=news_timeframe,
        )

    results = await asyncio.gather(*(fetch(symbol) for symbol in normalized))
    return {"success": True, "results": results}


@mcp.tool()
async def update_ticker_shortlist(
    candidates: list[str],
    min_market_cap: float = 10_000_000_000,
    max_pe: float = 35.0,
    max_forward_pe: float = 35.0,
    max_beta: float = 1.4,
    require_dividend: bool = True,
    include_existing: bool = True,
    max_companies: int = 10,
) -> dict[str, Any]:
    """Fetch and screen Tiingo tickers, persisting a shortlist capped by the requested size."""

    if max_companies <= 0:
        return {"success": False, "error": "max_companies must be a positive integer."}

    screener = TickerScreener(
        min_market_cap=min_market_cap,
        max_pe_ratio=max_pe,
        max_forward_pe=max_forward_pe,
        max_beta=max_beta,
        require_dividend=require_dividend,
    )

    client = EODHDClient()
    normalized_candidates = {ticker.upper().strip() for ticker in candidates if ticker.strip()}
    normalized_candidates = {item for item in normalized_candidates if item}

    def _sanitize_name(value: str | None) -> str:
        if not isinstance(value, str):
            return ""
        return "".join(ch for ch in value.upper() if ch.isalnum())

    candidate_names = {_sanitize_name(cand) for cand in candidates if cand.strip()}
    candidate_names = {item for item in candidate_names if item}
    existing: list[str] = []

    if include_existing:
        try:
            existing = [ticker.upper().strip() for ticker in load_ticker_shortlist()]
        except Exception:  # noqa: BLE001
            existing = []
        normalized_candidates.update(ticker for ticker in existing if ticker)
        candidate_names.update(_sanitize_name(ticker) for ticker in existing if ticker)
        candidate_names = {item for item in candidate_names if item}

    async def search(term: str) -> list[dict[str, Any]]:
        try:
            return await client.search_tickers(term, limit=25)
        except EODHDError:
            return []

    search_terms = {term.strip() for term in candidates if term.strip()}
    # Include readable versions of existing shortlist when requested
    if include_existing:
        search_terms.update(existing)

    search_results: list[dict[str, Any]] = []
    for term in sorted(search_terms):
        search_results.extend(await search(term))

    filtered_entries: dict[str, dict[str, Any]] = {}

    def _maybe_add_entry(symbol: str, metadata: dict[str, Any]) -> None:
        normalized_symbol = symbol.strip().upper()
        if not normalized_symbol:
            return
        if normalized_symbol in filtered_entries:
            existing_entry = filtered_entries[normalized_symbol]
            if existing_entry.get("market_cap", 0) < metadata.get("market_cap", 0):
                filtered_entries[normalized_symbol] = metadata
        else:
            filtered_entries[normalized_symbol] = metadata

    for entry in search_results:
        symbol = entry.get("ticker") or entry.get("symbol")
        name_value = entry.get("name") or entry.get("NAME")
        if not isinstance(symbol, str):
            continue

        sanitized_name = _sanitize_name(name_value)
        if normalized_candidates or candidate_names:
            symbol_match = symbol.strip().upper() in normalized_candidates if normalized_candidates else False
            name_match = sanitized_name in candidate_names if candidate_names else False
            if not (symbol_match or name_match):
                # Allow fuzzy contains match for human-provided names
                name_match = any(
                    cand in sanitized_name or sanitized_name in cand for cand in candidate_names
                ) if candidate_names and sanitized_name else False
            if not (symbol_match or name_match):
                continue

        market_cap_value = _coerce_float(entry.get("marketCap") or entry.get("marketcap"))
        if market_cap_value is None and "marketCapInMillions" in entry:
            market_cap_value = _coerce_float(entry.get("marketCapInMillions"))
            if market_cap_value is not None:
                market_cap_value *= 1_000_000

        metadata = {
            "symbol": symbol.strip().upper(),
            "market_cap": market_cap_value or 0.0,
        }
        _maybe_add_entry(symbol, metadata)

    # Ensure directly provided tickers are considered even if search returned nothing.
    for direct_symbol in normalized_candidates:
        if direct_symbol not in filtered_entries:
            filtered_entries[direct_symbol] = {"symbol": direct_symbol, "market_cap": 0.0}

    sorted_entries = sorted(
        filtered_entries.values(),
        key=lambda item: item.get("market_cap") or 0.0,
        reverse=True,
    )

    shortlisted_symbols: list[str] = []
    selection_details: list[dict[str, Any]] = []
    evaluated = 0
    seen: set[str] = set()

    for entry in sorted_entries:
        if len(shortlisted_symbols) >= max_companies:
            break

        symbol = entry["symbol"]
        if symbol in seen:
            continue
        seen.add(symbol)

        payload = await _fetch_ticker_payload(
            client,
            symbol,
            fetch_metrics=True,
            fetch_estimates=False,
            fetch_growth=False,
            fetch_news=False,
        )
        evaluated += 1

        if not payload.get("success"):
            continue

        metrics = payload.get("metrics")
        if not metrics:
            continue

        is_candidate, _ = screener.evaluate(metrics)
        if not is_candidate:
            continue

        shortlisted_symbols.append(symbol)
        selection_details.append(
            {
                "ticker": symbol,
                "market_cap": metrics.get("market_cap"),
                "dividend_yield": metrics.get("dividend_yield"),
                "pe_ratio": metrics.get("pe_ratio"),
            }
        )

    save_ticker_shortlist(shortlisted_symbols)

    return {
        "success": True,
        "shortlist": shortlisted_symbols,
        "selection_details": selection_details,
        "evaluated": evaluated,
    }


@mcp.tool()
async def fetch_fear_greed_index() -> dict[str, Any]:
    """Fetch the latest CNN Fear & Greed Index."""

    client = FearGreedClient()
    try:
        index = await client.fetch_index()
        return {
            "success": True,
            "fear_greed": index.model_dump(),
        }
    except FearGreedError as exc:
        return {"success": False, "error": str(exc)}


@mcp.tool()
async def advice_investor(
    ctx: Context[ServerSession, None],
    max_shortlist_tickers: int = 5,
) -> dict[str, Any]:
    """Generate investment advice given the portfolio, shortlist, and strategy."""

    portfolio_data = load_portfolio()
    shortlist = load_ticker_shortlist()[:max_shortlist_tickers]
    strategy = load_investment_strategy()

    await ctx.debug("Loaded local data assets.")

    tickers = {holding.ticker for holding in portfolio_data.holdings}
    tickers.update(shortlist)

    eodhd_client = EODHDClient()
    metrics = await _gather_metrics(eodhd_client, tickers, ctx=ctx)
    await ctx.debug(f"Fetched metrics for {len(metrics)} tickers.")

    analyzer = PortfolioAnalyzer(portfolio_data)
    holding_recs = analyzer.evaluate_holdings(metrics)
    shortlist_recs = analyzer.spot_opportunities(shortlist, metrics)

    fear_greed_client = FearGreedClient()
    try:
        fear_greed = await fear_greed_client.fetch_index()
    except FearGreedError as exc:
        await ctx.warning(f"Could not fetch Fear & Greed index: {exc}")
        fear_greed = None

    composer = AdviceComposer(
        strategy_markdown=strategy,
        portfolio=portfolio_data,
        fear_greed=fear_greed,
        holding_recs=holding_recs,
        shortlist_recs=shortlist_recs,
    )
    report: AdviceReport = composer.build()

    return {
        "success": True,
        "report": report.model_dump(),
        "holding_summary": format_recommendation_summary(holding_recs, metrics),
        "shortlist_summary": format_recommendation_summary(shortlist_recs, metrics),
    }
