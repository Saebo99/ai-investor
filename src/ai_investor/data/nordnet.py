"""
Client for retrieving current holdings and cash positions from Nordnet.
"""

from __future__ import annotations

from typing import Any, Dict

from ..config import get_settings


class NordnetClient:
    """
    Lightweight abstraction over Nordnet data access.
    Replace the in-memory stubs with real API or scraping logic when available.
    """

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.data_providers.nordnet_username:
            raise ValueError("Nordnet credentials are required. Set NORDNET_USERNAME/PASSWORD.")

        self._username = settings.data_providers.nordnet_username
        self._password = settings.data_providers.nordnet_password

    async def fetch_holdings(self) -> Dict[str, Any]:
        """
        Retrieve holdings information.
        """
        # TODO: Replace with Nordnet API integration.
        return {}

    async def fetch_available_cash(self) -> float:
        """
        Retrieve available funds.
        """
        # TODO: Replace with Nordnet API integration.
        return 0.0
