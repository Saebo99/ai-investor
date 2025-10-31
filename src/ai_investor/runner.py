"""
Entrypoint helpers for invoking the AI Investor workflow.
"""

from __future__ import annotations

import asyncio
from typing import Iterable

from anthropic import AsyncAnthropic  # type: ignore[import]

from .analysis import InvestmentDecision
from .config import get_settings
from .data import EODHDClient, NordnetClient
from .portfolio import PortfolioManager
from .reporting import EmailReport
from .strategy import load_strategy


async def run_for_tickers(tickers: Iterable[str]) -> list[InvestmentDecision]:
    """
    Execute the screening workflow for the provided tickers.
    """
    settings = get_settings()
    _anthropic = AsyncAnthropic(api_key=settings.agent.anthropic_api_key)

    # TODO: Hook _anthropic into Claude Agent SDK driven orchestration.

    data_client = EODHDClient()
    holdings_client = NordnetClient()
    manager = PortfolioManager(data_client, holdings_client)
    decisions = await manager.run_screening(tickers)

    email = EmailReport()
    await email.send(decisions)
    return decisions


def main() -> None:
    """
    Convenience synchronous entrypoint.
    """
    tickers = ["AAPL", "MSFT", "NVDA"]
    asyncio.run(run_for_tickers(tickers))


if __name__ == "__main__":
    main()
