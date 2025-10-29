"""Nordnet API integration scaffold."""

from __future__ import annotations

import httpx

from ai_investor.config import get_settings


class NordnetClient:
    """Authenticate and interact with the Nordnet API."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.nordnet_base_url.rstrip("/")
        self._username = settings.nordnet_username
        self._password = settings.nordnet_password
        self._account_id = settings.nordnet_account_id
        self._client = httpx.Client(timeout=20)
        self._authenticated = False

    def authenticate(self) -> None:
        """Perform authentication handshake."""

        raise NotImplementedError("Implement Nordnet authentication flow")

    def list_positions(self) -> list[dict]:
        """Return positions for configured account."""

        raise NotImplementedError("Call Nordnet positions endpoint")

    def place_order(self, *, ticker: str, side: str, quantity: int, price: float) -> dict:
        """Submit an order to Nordnet."""

        raise NotImplementedError("Submit order via Nordnet trading endpoint")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "NordnetClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
