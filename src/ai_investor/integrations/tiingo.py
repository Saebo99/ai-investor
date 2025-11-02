"""Minimal Tiingo client used for news and ticker search."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from ..config import get_settings
from ..models import NewsItem


class TiingoError(RuntimeError):
    """Raised when Tiingo data retrieval fails."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


_TIMEFRAME_UNITS: dict[str, dict[str, int]] = {
    "s": {"seconds": 1},
    "m": {"minutes": 1},
    "h": {"hours": 1},
    "d": {"days": 1},
    "w": {"weeks": 1},
}


def _parse_timeframe(value: str) -> timedelta:
    value = value.strip().lower()
    if not value:
        raise ValueError("Timeframe must be non-empty.")

    if value.isdigit():
        return timedelta(days=int(value))

    number_part = "".join(ch for ch in value if ch.isdigit())
    unit_part = value[len(number_part) :]
    if not number_part or unit_part not in _TIMEFRAME_UNITS:
        raise ValueError(f"Unsupported timeframe value: {value}")

    quantity = int(number_part)
    if quantity <= 0:
        raise ValueError("Timeframe quantity must be positive.")
    unit_kwargs = _TIMEFRAME_UNITS[unit_part]
    return timedelta(**{k: v * quantity for k, v in unit_kwargs.items()})


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).replace(tzinfo=None)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).replace(tzinfo=None)

    text = str(value)
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(text, fmt)
            if dt.tzinfo:
                return dt.astimezone(timezone.utc).replace(tzinfo=None)
            return dt
        except (TypeError, ValueError):
            continue
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        return None


class TiingoClient:
    """Asynchronous wrapper around Tiingo REST endpoints used by the project."""

    def __init__(self) -> None:  # pragma: no cover - simple constructor
        settings = get_settings()
        self._base_url = settings.tiingo_api_base.rstrip("/")
        self._token = settings.tiingo_api_token
        self._timeout = settings.http_timeout_seconds

    @property
    def has_credentials(self) -> bool:
        return bool(self._token)

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """Convert ticker symbols to Tiingo-compatible format (e.g., BRK.B -> BRK-B)."""

        normalized = symbol.strip().upper()
        if not normalized:
            raise ValueError("Ticker symbol must be non-empty")

        if normalized.endswith(".US"):
            normalized = normalized[:-3]
        normalized = normalized.replace(".", "-")
        return normalized

    async def _request_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        if not self.has_credentials:
            raise TiingoError("Tiingo API token not configured. Set TIINGO_API_TOKEN.")

        headers = {"Authorization": f"Token {self._token}"}
        async with httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout) as client:
            try:
                response = await client.get(path, params=params, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:  # pragma: no cover - network driven
                detail = exc.response.text.strip()
                raise TiingoError(
                    f"Tiingo request failed ({exc.response.status_code}): {detail or exc}",
                    status_code=exc.response.status_code,
                ) from exc
            except httpx.HTTPError as exc:  # pragma: no cover - network driven
                raise TiingoError(f"Tiingo request encountered a network error: {exc}") from exc
            return response.json()

    async def get_news(
        self,
        symbol: str,
        *,
        limit: int = 5,
        timeframe: str | None = None,
    ) -> list[NewsItem]:
        normalized = self.normalize_symbol(symbol)
        params: dict[str, Any] = {"tickers": normalized}

        now_utc = datetime.now(timezone.utc)
        start_cutoff: datetime | None = None

        if timeframe:
            try:
                delta = _parse_timeframe(timeframe)
            except ValueError as exc:
                raise TiingoError(str(exc)) from exc
            start_cutoff = now_utc - delta
            params["startDate"] = start_cutoff.date().isoformat()
            params["endDate"] = now_utc.date().isoformat()

        if limit > 0:
            params["limit"] = limit

        data = await self._request_json("/tiingo/news", params=params)
        if not isinstance(data, list):
            raise TiingoError("Unexpected Tiingo news response format.")

        cutoff_naive: datetime | None = start_cutoff.replace(tzinfo=None) if start_cutoff else None
        items: list[NewsItem] = []
        for entry in data:
            if not isinstance(entry, dict):
                continue

            published_at = _parse_datetime(
                entry.get("publishedDate")
                or entry.get("publicationTime")
                or entry.get("pubDate")
                or entry.get("date")
            )
            if not published_at:
                continue
            if cutoff_naive and published_at < cutoff_naive:
                continue

            items.append(
                NewsItem(
                    title=str(entry.get("title") or "Untitled"),
                    url=str(entry.get("url") or entry.get("articleUrl") or ""),
                    published_at=published_at,
                    site=entry.get("source") or entry.get("sourceName"),
                    sentiment=None,
                    summary=entry.get("description") or entry.get("summary"),
                )
            )

        if limit > 0:
            items = items[:limit]
        return items

    async def search_tickers(self, query: str, *, limit: int = 25) -> list[dict[str, Any]]:
        params = {"query": query, "limit": limit}
        data = await self._request_json("/tiingo/utilities/search", params=params)
        if not isinstance(data, list):
            raise TiingoError("Unexpected Tiingo search response format.")
        return [item for item in data if isinstance(item, dict)]
