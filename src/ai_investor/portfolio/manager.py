"""
Coordinates data gathering, analysis, and recommendation workflows.
"""

from __future__ import annotations

from typing import Iterable, List

from ..analysis import CompanySnapshot, FundamentalAnalyzer, InvestmentDecision
from ..data import EODHDClient, NordnetClient


class PortfolioManager:
    """
    High-level orchestrator that will eventually be controlled by the Claude agent.
    """

    def __init__(
        self,
        data_client: EODHDClient,
        holdings_client: NordnetClient,
        analyzer: FundamentalAnalyzer | None = None,
    ) -> None:
        self.data_client = data_client
        self.holdings_client = holdings_client
        self.analyzer = analyzer or FundamentalAnalyzer()

    async def run_screening(self, tickers: Iterable[str]) -> List[InvestmentDecision]:
        """
        Basic end-to-end screening for a shortlist of tickers.
        """
        fundamentals = await self.data_client.fetch_fundamentals(tickers)
        quotes = await self.data_client.fetch_quotes(tickers)
        holdings = await self.holdings_client.fetch_holdings()

        snapshots = []
        for ticker in tickers:
            snapshots.append(
                CompanySnapshot(
                    ticker=ticker,
                    name=fundamentals.get(ticker, {}).get("General", {}).get("Name"),
                    fundamentals=_extract_financial_metrics(fundamentals.get(ticker, {})),
                    quote=_extract_quote_metrics(quotes.get(ticker, {})),
                )
            )

        filtered = self.analyzer.filter_candidates(snapshots)
        ranked = self.analyzer.rank(filtered)
        return self.analyzer.propose_actions(ranked, holdings.get("positions", {}))


def _extract_financial_metrics(raw: dict) -> dict:
    """Select fundamental metrics we care about."""
    general = raw.get("General", {})
    highlights = raw.get("Highlights", {})

    return {
        "sector": general.get("Sector"),
        "industry": general.get("Industry"),
        "dividend_yield": highlights.get("DividendYield"),
        "pe_ratio": highlights.get("PERatio"),
        "market_cap": highlights.get("MarketCapitalization"),
    }


def _extract_quote_metrics(raw: dict) -> dict:
    """Select quote metrics we care about."""
    return {
        "close": raw.get("close"),
        "change": raw.get("change"),
        "change_p": raw.get("change_p"),
    }
