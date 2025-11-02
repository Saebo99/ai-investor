"""Client for the CNN Fear & Greed Index."""

from __future__ import annotations

from typing import Any

import httpx

from ..config import get_settings
from ..models import FearGreedIndex


class FearGreedError(RuntimeError):
    """Raised when the Fear & Greed API fails."""


class FearGreedClient:
    """Fetches market sentiment data from CNN's API."""

    def __init__(self, endpoint: str | None = None) -> None:
        settings = get_settings()
        self._endpoint = endpoint or settings.fear_greed_endpoint
        self._timeout = settings.http_timeout_seconds

    async def fetch_index(self) -> FearGreedIndex:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
            ),
            "Accept": "application/json",
        }

        async with httpx.AsyncClient(timeout=self._timeout, headers=headers) as client:
            try:
                response = await client.get(self._endpoint)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise FearGreedError(
                    f"Fear & Greed request failed ({exc.response.status_code})"
                ) from exc
            except httpx.HTTPError as exc:
                raise FearGreedError(f"Fear & Greed request error: {exc}") from exc

        payload = response.json()
        return _parse_index(payload)


def _parse_index(payload: Any) -> FearGreedIndex:
    if not isinstance(payload, dict):
        raise FearGreedError("Unexpected response structure for Fear & Greed index.")

    market_mood = payload.get("fear_and_greed", {})
    if not isinstance(market_mood, dict):
        raise FearGreedError("Missing fear_and_greed data.")

    rating_map = {
        "extreme fear": "Extreme Fear",
        "fear": "Fear",
        "neutral": "Neutral",
        "greed": "Greed",
        "extreme greed": "Extreme Greed",
    }

    raw_rating = str(market_mood.get("rating") or "Neutral").strip().lower()
    rating = rating_map.get(raw_rating, "Neutral")

    def get_value(key: str) -> int | None:
        value = market_mood.get(key)
        return int(value) if value is not None else None

    return FearGreedIndex(
        value=get_value("score") or 0,
        rating=rating,
        description=market_mood.get("summary") or "No summary available.",
        previous_close=get_value("previous_close"),
        previous_1_week=get_value("previous_week"),
        previous_1_month=get_value("previous_month"),
        previous_1_year=get_value("previous_year"),
    )
