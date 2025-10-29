"""Thin wrapper around the EODHD API."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from ai_investor.config import get_settings

logger = logging.getLogger(__name__)


class EODHDClient:
    """Provide typed access to EODHD fundamentals and news."""

    def __init__(self, *, session: Optional[httpx.Client] = None) -> None:
        settings = get_settings()
        self._api_token = settings.eodhd_api_key
        self._base_url = settings.eodhd_base_url.rstrip("/")
        self._client = session or httpx.Client(timeout=20)

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        query = {"api_token": self._api_token, "fmt": "json"}
        if params:
            query.update(params)
        url = f"{self._base_url}/{endpoint.lstrip('/')}"
        logger.debug("Requesting %s", url)
        response = self._client.get(url, params=query)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and payload.get("code"):
            raise RuntimeError(f"EODHD error {payload['code']}: {payload.get('message')}")
        return payload

    def list_dividend_large_caps(self, exchange: str) -> List[Dict[str, Any]]:
        """Return tickers matching conservative dividend filters."""

        filters = {
            "screener": "most_traded",
            "filters": "market_cap~more~10000,dividend_yield~more~2",
            "exchange": exchange,
            "limit": 200,
        }
        payload = self._request("screener", filters)
        return payload if isinstance(payload, list) else []

    def get_fundamentals(self, ticker: str) -> Dict[str, Any]:
        endpoint = f"fundamentals/{ticker}"
        payload = self._request(endpoint)
        return payload if isinstance(payload, dict) else {}

    def get_financials(self, ticker: str) -> Dict[str, Any]:
        endpoint = f"fundamentals/{ticker}"  # financials embedded in fundamentals response
        data = self._request(endpoint)
        return data if isinstance(data, dict) else {}

    def get_news(self, ticker: str, lookback_days: int = 30) -> List[Dict[str, Any]]:
        since = (datetime.utcnow() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
        payload = self._request(
            "news",
            {"s": ticker, "from": since, "to": datetime.utcnow().strftime("%Y-%m-%d")},
        )
        return payload if isinstance(payload, list) else []

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "EODHDClient":
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()
