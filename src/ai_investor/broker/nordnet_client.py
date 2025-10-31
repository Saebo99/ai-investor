"""Nordnet API integration scaffold with mocked trading for testing."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import httpx

from ai_investor.config import get_settings

logger = logging.getLogger(__name__)


class NordnetClient:
    """Authenticate and interact with the Nordnet API (mocked for testing)."""

    def __init__(self, *, mock_mode: bool = True) -> None:
        settings = get_settings()
        self._base_url = settings.nordnet_base_url.rstrip("/")
        self._username = settings.nordnet_username
        self._password = settings.nordnet_password
        self._account_id = settings.nordnet_account_id
        self._client = httpx.Client(timeout=20)
        self._authenticated = False
        self._mock_mode = mock_mode
        self._mock_positions: list[dict[str, Any]] = []

    def authenticate(self) -> None:
        """Perform authentication handshake (mocked for testing)."""
        if self._mock_mode:
            logger.info(
                "MOCK: Authenticating to Nordnet with username=%s, account_id=%s",
                self._username,
                self._account_id,
            )
            self._authenticated = True
            logger.info("MOCK: Authentication successful")
            return

        raise NotImplementedError("Real Nordnet authentication not yet implemented")

    def list_positions(self) -> list[dict]:
        """Return positions for configured account (mocked for testing)."""
        if not self._authenticated:
            self.authenticate()

        if self._mock_mode:
            logger.info("MOCK: Fetching positions for account_id=%s", self._account_id)
            # Return mock positions data
            mock_positions = [
                {
                    "ticker": "AAPL",
                    "name": "Apple Inc.",
                    "quantity": 10,
                    "average_price": 150.50,
                    "current_price": 175.20,
                    "market_value": 1752.00,
                    "unrealized_pnl": 247.00,
                    "unrealized_pnl_percent": 16.41,
                },
                {
                    "ticker": "MSFT",
                    "name": "Microsoft Corporation",
                    "quantity": 5,
                    "average_price": 300.00,
                    "current_price": 350.75,
                    "market_value": 1753.75,
                    "unrealized_pnl": 253.75,
                    "unrealized_pnl_percent": 16.92,
                },
            ]
            self._mock_positions = mock_positions
            logger.info("MOCK: Retrieved %d positions", len(mock_positions))
            return mock_positions

        raise NotImplementedError("Real Nordnet positions endpoint not yet implemented")

    def place_order(
        self, *, ticker: str, side: str, quantity: int, price: float
    ) -> dict:
        """Submit an order to Nordnet (mocked for testing)."""
        if not self._authenticated:
            self.authenticate()

        if self._mock_mode:
            order_id = f"MOCK-{datetime.now().strftime('%Y%m%d%H%M%S')}-{ticker}"
            order_details = {
                "order_id": order_id,
                "ticker": ticker,
                "side": side,
                "quantity": quantity,
                "price": price,
                "total_value": quantity * price,
                "status": "simulated",
                "timestamp": datetime.now().isoformat(),
            }
            logger.warning(
                "MOCK ORDER: %s %d shares of %s at $%.2f (Total: $%.2f) - Order ID: %s",
                side.upper(),
                quantity,
                ticker,
                price,
                order_details["total_value"],
                order_id,
            )
            logger.warning("MOCK: No actual trade was executed - this is a simulation")

            # Update mock positions if this is a buy order
            if side.lower() == "buy":
                existing = next(
                    (p for p in self._mock_positions if p["ticker"] == ticker), None
                )
                if existing:
                    total_qty = existing["quantity"] + quantity
                    total_cost = (
                        existing["quantity"] * existing["average_price"]
                        + quantity * price
                    )
                    existing["quantity"] = total_qty
                    existing["average_price"] = total_cost / total_qty
                else:
                    self._mock_positions.append(
                        {
                            "ticker": ticker,
                            "name": f"{ticker} (Mock Position)",
                            "quantity": quantity,
                            "average_price": price,
                            "current_price": price,
                            "market_value": quantity * price,
                            "unrealized_pnl": 0.0,
                            "unrealized_pnl_percent": 0.0,
                        }
                    )
            elif side.lower() == "sell":
                existing = next(
                    (p for p in self._mock_positions if p["ticker"] == ticker), None
                )
                if existing:
                    existing["quantity"] = max(0, existing["quantity"] - quantity)
                    if existing["quantity"] == 0:
                        self._mock_positions.remove(existing)

            return order_details

        raise NotImplementedError("Real Nordnet trading endpoint not yet implemented")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "NordnetClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()
