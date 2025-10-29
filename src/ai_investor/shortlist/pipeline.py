"""Shortlist maintenance logic."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from ai_investor.config import get_settings
from ai_investor.data_providers.eodhd_client import EODHDClient

logger = logging.getLogger(__name__)


class ShortlistPipeline:
    """Refresh and persist a manageable list of candidate tickers."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        settings = get_settings()
        self._target_size = settings.shortlist_target_size
        self._refresh_days = settings.shortlist_refresh_days
        self._exchange = settings.default_exchange
        self._cache_path = (cache_dir or Path("data")) / "shortlist.json"
        self._cache_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self._cache_path.exists():
            return {"tickers": [], "last_refresh": None}
        try:
            return json.loads(self._cache_path.read_text())
        except json.JSONDecodeError:
            logger.warning("Shortlist cache corrupted; starting fresh")
            return {"tickers": [], "last_refresh": None}

    def save(self, tickers: List[Dict[str, Any]]) -> None:
        payload = {
            "tickers": tickers,
            "last_refresh": datetime.utcnow().isoformat(),
        }
        self._cache_path.write_text(json.dumps(payload, indent=2))

    def needs_refresh(self, cache: Dict[str, Any]) -> bool:
        last_refresh = cache.get("last_refresh")
        if not last_refresh:
            return True
        try:
            refreshed_at = datetime.fromisoformat(last_refresh)
        except ValueError:
            return True
        return datetime.utcnow() - refreshed_at >= timedelta(days=self._refresh_days)

    def refresh(self) -> Dict[str, Any]:
        logger.info("Refreshing shortlist for exchange %s", self._exchange)
        with EODHDClient() as client:
            universe = client.list_dividend_large_caps(self._exchange)
            sorted_universe = sorted(
                universe,
                key=lambda item: (
                    -(item.get("avg_volume", 0) or 0),
                    -(item.get("market_cap", 0) or 0),
                ),
            )
            shortlist = sorted_universe[: self._target_size]
        self.save(shortlist)
        return {"tickers": shortlist, "last_refresh": datetime.utcnow().isoformat()}

    def ensure_shortlist(self) -> Dict[str, Any]:
        cache = self.load()
        if self.needs_refresh(cache):
            return self.refresh()
        logger.debug("Using cached shortlist")
        return cache
