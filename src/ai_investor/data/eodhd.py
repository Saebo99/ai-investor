"""
Client for interacting with the EODHD market data API.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

import httpx

from ..config import get_settings


class EODHDClient:
    """
    Minimal wrapper around the EODHD API for fetching quote and fundamental data.
    """

    BASE_URL = "https://eodhd.com/api"

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        settings = get_settings()
        api_key = settings.data_providers.eodhd_api_key
        if not api_key:
            raise ValueError("EODHD API key is required. Set EODHD_API_KEY in your environment.")
        self.api_key = api_key
        self._external_client = http_client

    async def fetch_fundamentals(self, tickers: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve fundamental data for a collection of tickers.
        """
        results: Dict[str, Dict[str, Any]] = {}
        client, close_after = await self._get_client()
        try:
            for ticker in tickers:
                response = await client.get(
                    f"{self.BASE_URL}/fundamentals/{ticker}",
                    params={"api_token": self.api_key},
                    timeout=30.0,
                )
                response.raise_for_status()
                results[ticker] = response.json()
        finally:
            if close_after:
                await client.aclose()
        return results

    async def fetch_quotes(self, tickers: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve latest quote information for provided tickers.
        """
        results: Dict[str, Dict[str, Any]] = {}
        client, close_after = await self._get_client()
        try:
            for ticker in tickers:
                response = await client.get(
                    f"{self.BASE_URL}/real-time/{ticker}",
                    params={"api_token": self.api_key},
                    timeout=10.0,
                )
                response.raise_for_status()
                results[ticker] = response.json()
        finally:
            if close_after:
                await client.aclose()
        return results

    async def _get_client(self) -> tuple[httpx.AsyncClient, bool]:
        if self._external_client is not None:
            return self._external_client, False
        return httpx.AsyncClient(), True
