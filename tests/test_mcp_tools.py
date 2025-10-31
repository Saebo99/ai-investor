"""Tests for MCP tools and tool executor."""

from unittest.mock import MagicMock, Mock

import pytest

from ai_investor.agents.mcp_tools import MCP_TOOL_SCHEMAS, MCPToolExecutor


def test_mcp_tool_schemas_defined() -> None:
    """Test that all expected MCP tool schemas are defined."""
    expected_tools = {
        "get_nordnet_positions",
        "get_available_funds",
        "get_stock_fundamentals",
        "get_stock_news",
        "evaluate_stock_decision",
        "execute_trade",
        "get_shortlist",
    }
    
    tool_names = {tool["name"] for tool in MCP_TOOL_SCHEMAS}
    assert tool_names == expected_tools, f"Expected {expected_tools}, got {tool_names}"


def test_mcp_tool_schemas_structure() -> None:
    """Test that tool schemas have required fields."""
    for tool in MCP_TOOL_SCHEMAS:
        assert "name" in tool, f"Tool missing 'name': {tool}"
        assert "description" in tool, f"Tool missing 'description': {tool}"
        assert "input_schema" in tool, f"Tool missing 'input_schema': {tool}"
        
        schema = tool["input_schema"]
        assert "type" in schema, f"Tool {tool['name']} schema missing 'type'"
        assert "properties" in schema, f"Tool {tool['name']} schema missing 'properties'"
        assert "required" in schema, f"Tool {tool['name']} schema missing 'required'"


def test_tool_executor_get_positions() -> None:
    """Test tool executor can fetch positions."""
    mock_nordnet = Mock()
    mock_nordnet.list_positions.return_value = [
        {"ticker": "AAPL", "quantity": 10, "average_price": 150.0}
    ]
    
    executor = MCPToolExecutor(
        nordnet_client=mock_nordnet,
        eodhd_client=Mock(),
        decision_engine=Mock(),
        shortlist_pipeline=Mock(),
    )
    
    result = executor.execute("get_nordnet_positions", {})
    
    assert len(result) == 1
    assert result[0]["ticker"] == "AAPL"
    mock_nordnet.list_positions.assert_called_once()


def test_tool_executor_get_funds() -> None:
    """Test tool executor can fetch available funds."""
    mock_nordnet = Mock()
    mock_nordnet.get_available_funds.return_value = {
        "currency": "USD",
        "available_cash": 10000.0,
    }
    
    executor = MCPToolExecutor(
        nordnet_client=mock_nordnet,
        eodhd_client=Mock(),
        decision_engine=Mock(),
        shortlist_pipeline=Mock(),
    )
    
    result = executor.execute("get_available_funds", {})
    
    assert result["currency"] == "USD"
    assert result["available_cash"] == 10000.0
    mock_nordnet.get_available_funds.assert_called_once()


def test_tool_executor_get_fundamentals() -> None:
    """Test tool executor can fetch stock fundamentals."""
    mock_eodhd = Mock()
    mock_eodhd.get_fundamentals.return_value = {
        "DividendYield": 0.025,
        "PE": 25.0,
    }
    
    executor = MCPToolExecutor(
        nordnet_client=Mock(),
        eodhd_client=mock_eodhd,
        decision_engine=Mock(),
        shortlist_pipeline=Mock(),
    )
    
    result = executor.execute("get_stock_fundamentals", {"ticker": "AAPL"})
    
    assert result["DividendYield"] == 0.025
    mock_eodhd.get_fundamentals.assert_called_once_with("AAPL")


def test_tool_executor_get_news() -> None:
    """Test tool executor can fetch stock news."""
    mock_eodhd = Mock()
    mock_eodhd.get_news.return_value = [
        {"title": "Test News", "sentiment": "positive"}
    ]
    
    executor = MCPToolExecutor(
        nordnet_client=Mock(),
        eodhd_client=mock_eodhd,
        decision_engine=Mock(),
        shortlist_pipeline=Mock(),
    )
    
    result = executor.execute("get_stock_news", {"ticker": "AAPL", "lookback_days": 30})
    
    assert len(result) == 1
    assert result[0]["title"] == "Test News"
    mock_eodhd.get_news.assert_called_once_with("AAPL", 30)


def test_tool_executor_evaluate_decision() -> None:
    """Test tool executor can evaluate investment decisions."""
    mock_engine = Mock()
    mock_thesis = Mock()
    mock_thesis.dict.return_value = {
        "ticker": "AAPL",
        "recommendation": "buy",
        "conviction": 0.85,
    }
    mock_engine.evaluate.return_value = mock_thesis
    
    executor = MCPToolExecutor(
        nordnet_client=Mock(),
        eodhd_client=Mock(),
        decision_engine=mock_engine,
        shortlist_pipeline=Mock(),
    )
    
    result = executor.execute(
        "evaluate_stock_decision",
        {"ticker": "AAPL", "fundamentals": {}, "news": []},
    )
    
    assert result["ticker"] == "AAPL"
    assert result["recommendation"] == "buy"
    mock_engine.evaluate.assert_called_once_with("AAPL", {}, [])


def test_tool_executor_execute_trade() -> None:
    """Test tool executor can execute trades."""
    mock_nordnet = Mock()
    mock_nordnet.place_order.return_value = {
        "order_id": "MOCK-123",
        "ticker": "AAPL",
        "side": "buy",
        "quantity": 10,
        "price": 150.0,
    }
    
    executor = MCPToolExecutor(
        nordnet_client=mock_nordnet,
        eodhd_client=Mock(),
        decision_engine=Mock(),
        shortlist_pipeline=Mock(),
    )
    
    result = executor.execute(
        "execute_trade",
        {"ticker": "AAPL", "side": "buy", "quantity": 10, "price": 150.0},
    )
    
    assert result["order_id"] == "MOCK-123"
    assert result["ticker"] == "AAPL"
    mock_nordnet.place_order.assert_called_once()


def test_tool_executor_get_shortlist() -> None:
    """Test tool executor can get shortlist."""
    mock_shortlist = Mock()
    mock_shortlist.ensure_shortlist.return_value = {
        "tickers": [{"ticker": "AAPL"}, {"ticker": "MSFT"}],
        "last_refresh": "2025-10-31",
    }
    
    executor = MCPToolExecutor(
        nordnet_client=Mock(),
        eodhd_client=Mock(),
        decision_engine=Mock(),
        shortlist_pipeline=mock_shortlist,
    )
    
    result = executor.execute("get_shortlist", {})
    
    assert len(result["tickers"]) == 2
    mock_shortlist.ensure_shortlist.assert_called_once()


def test_tool_executor_unknown_tool() -> None:
    """Test tool executor raises error for unknown tools."""
    executor = MCPToolExecutor(
        nordnet_client=Mock(),
        eodhd_client=Mock(),
        decision_engine=Mock(),
        shortlist_pipeline=Mock(),
    )
    
    with pytest.raises(ValueError, match="Unknown tool"):
        executor.execute("unknown_tool", {})
