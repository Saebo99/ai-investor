"""Tests for agent orchestrator."""

from unittest.mock import Mock, patch

from ai_investor.agents.agent_orchestrator import AgentOrchestrator


def test_agent_orchestrator_format_email_report() -> None:
    """Test email report formatting."""
    orchestrator = AgentOrchestrator()
    
    agent_result = {
        "content": "Test analysis content",
        "iterations": 5,
        "tool_calls": [
            {"tool": "get_nordnet_positions", "success": True},
            {"tool": "get_stock_fundamentals", "success": True},
            {"tool": "execute_trade", "success": False, "error": "Test error"},
        ],
    }
    
    report = orchestrator.format_email_report(agent_result)
    
    assert "AI INVESTOR - AGENT ANALYSIS REPORT" in report
    assert "Agent Iterations: 5" in report
    assert "Tools Used: 3" in report
    assert "Test analysis content" in report
    assert "get_nordnet_positions" in report
    assert "Failed Tool Calls:" in report
    assert "Test error" in report


def test_agent_orchestrator_create_initial_message() -> None:
    """Test initial message creation."""
    orchestrator = AgentOrchestrator()
    
    message = orchestrator._create_initial_message()
    
    assert "perform a comprehensive investment analysis" in message
    assert "portfolio positions" in message
    assert "shortlist" in message
    assert "fundamentals and recent news" in message
    assert "BUY actions" in message
    assert "long-term value" in message


@patch("ai_investor.agents.agent_orchestrator.NordnetClient")
@patch("ai_investor.agents.agent_orchestrator.EODHDClient")
@patch("ai_investor.agents.agent_orchestrator.ShortlistPipeline")
def test_agent_orchestrator_run_basic_flow(
    mock_shortlist_cls: Mock,
    mock_eodhd_cls: Mock,
    mock_nordnet_cls: Mock,
) -> None:
    """Test basic orchestrator run flow."""
    # Setup mocks
    mock_nordnet = Mock()
    mock_nordnet.list_positions.return_value = []
    mock_nordnet_cls.return_value.__enter__.return_value = mock_nordnet
    
    mock_eodhd = Mock()
    mock_eodhd_cls.return_value.__enter__.return_value = mock_eodhd
    
    mock_shortlist = Mock()
    mock_shortlist_cls.return_value = mock_shortlist
    
    # Mock the agent's run_with_tools to return immediately
    orchestrator = AgentOrchestrator()
    orchestrator._analyst.run_with_tools = Mock(return_value={
        "content": "Mock analysis",
        "iterations": 1,
        "tool_calls": [],
    })
    
    result = orchestrator.run()
    
    assert result["content"] == "Mock analysis"
    assert result["iterations"] == 1
    mock_nordnet.authenticate.assert_called_once()
    mock_nordnet.list_positions.assert_called_once()
