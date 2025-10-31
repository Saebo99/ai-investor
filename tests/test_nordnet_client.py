"""Tests for Nordnet client enhancements."""

from ai_investor.broker.nordnet_client import NordnetClient


def test_nordnet_get_available_funds_mock() -> None:
    """Test that get_available_funds returns mock data in mock mode."""
    client = NordnetClient(mock_mode=True)
    client.authenticate()
    
    funds = client.get_available_funds()
    
    assert "currency" in funds
    assert "available_cash" in funds
    assert "total_value" in funds
    assert "invested_value" in funds
    assert funds["currency"] == "USD"
    assert funds["available_cash"] > 0


def test_nordnet_get_available_funds_requires_auth() -> None:
    """Test that get_available_funds authenticates if needed."""
    client = NordnetClient(mock_mode=True)
    
    # Should auto-authenticate
    funds = client.get_available_funds()
    
    assert client._authenticated is True
    assert funds is not None


def test_nordnet_mock_positions_integration() -> None:
    """Test that positions and funds are consistent."""
    client = NordnetClient(mock_mode=True)
    client.authenticate()
    
    positions = client.list_positions()
    funds = client.get_available_funds()
    
    # Calculate total from positions
    total_position_value = sum(pos.get("market_value", 0) for pos in positions)
    
    # Total value should be cash + positions
    expected_total = funds["available_cash"] + total_position_value
    
    # Allow small rounding differences
    assert abs(funds["total_value"] - expected_total) < 1.0
