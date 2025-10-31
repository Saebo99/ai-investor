"""Agent-based orchestration using Claude with MCP tools."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from ai_investor.agents.claude_agent import ClaudeAnalyst
from ai_investor.agents.mcp_tools import MCP_TOOL_SCHEMAS, MCPToolExecutor
from ai_investor.broker.nordnet_client import NordnetClient
from ai_investor.config import get_settings
from ai_investor.data_providers.eodhd_client import EODHDClient
from ai_investor.decision.engine import DecisionEngine
from ai_investor.logging.decision_log import thesis_logger
from ai_investor.shortlist.pipeline import ShortlistPipeline

logger = logging.getLogger(__name__)


AGENT_SYSTEM_PROMPT = """You are an AI investment advisor specializing in long-term, fundamental analysis-driven investing.

Your strategic principles:
1. Never invest in risky assets. Prefer "monopolies"/large companies with high upside long-term to reduce risk.
2. Always find stocks that can be held for several months to several years.
3. Prefer stocks distributing dividends.
4. Diversification in both number of companies and industries is key, without spreading too thin.

You have access to tools for:
- Fetching current portfolio positions and available funds
- Getting stock fundamentals and news from EODHD
- Evaluating investment decisions using a quantitative + qualitative + stability framework
- Executing trades (MOCKED for testing)
- Getting a pre-screened shortlist of dividend-paying large caps

Your workflow:
1. First, get current positions and available funds to understand the portfolio state
2. Get the shortlist of candidate stocks to analyze
3. For each candidate (and existing positions), fetch fundamentals and news
4. Use the evaluation tool to generate buy/hold/trim/exit recommendations with conviction scores
5. For BUY recommendations with high conviction (>0.70), consider executing trades if funds are available
6. For EXIT recommendations on held positions, consider executing sell trades
7. Document your reasoning for all decisions

Important constraints:
- Minimum 90-day holding period before considering exits (unless catastrophic)
- Higher threshold for new positions (conviction >= 0.75) to avoid trend-chasing
- More lenient thresholds for holding existing positions (>= 0.45)
- Consider stability (low debt, low beta) as important as growth metrics
- Trades are MOCKED - no real money is involved

Output format:
Provide a clear summary of:
- Portfolio overview (current positions, cash available)
- Analysis of each evaluated stock with reasoning
- Recommended actions with justification
- Expected outcomes

Be thorough in your reasoning but concise in your final recommendations."""


class AgentOrchestrator:
    """Run Claude agent with MCP tools to manage investment decisions."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._analyst = ClaudeAnalyst()
        self._thesis_log = thesis_logger()

    def run(self) -> Dict[str, Any]:
        """Execute agent-based investment workflow."""
        logger.info("Starting agent-based orchestration workflow")
        
        # Initialize clients and dependencies
        with NordnetClient(mock_mode=True) as nordnet:
            nordnet.authenticate()
            positions = nordnet.list_positions()
            
            with EODHDClient() as eodhd:
                shortlist = ShortlistPipeline()
                engine = DecisionEngine(
                    positions=positions,
                    thesis_log_path=Path(self._settings.thesis_storage_path),
                )
                
                # Create tool executor
                tool_executor = MCPToolExecutor(
                    nordnet_client=nordnet,
                    eodhd_client=eodhd,
                    decision_engine=engine,
                    shortlist_pipeline=shortlist,
                )
                
                # Prepare initial message for agent
                initial_message = self._create_initial_message()
                
                # Run agent with tools
                result = self._analyst.run_with_tools(
                    system_prompt=AGENT_SYSTEM_PROMPT,
                    initial_message=initial_message,
                    tools=MCP_TOOL_SCHEMAS,
                    tool_executor=tool_executor,
                    max_iterations=25,  # Allow enough iterations for analysis
                )
                
                logger.info(
                    "Agent completed: %d iterations, %d tool calls",
                    result.get("iterations", 0),
                    len(result.get("tool_calls", [])),
                )
                
                return result

    def _create_initial_message(self) -> str:
        """Create the initial message to send to the agent."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        
        return f"""Today is {today}. Please perform a comprehensive investment analysis:

1. Start by checking current portfolio positions and available funds
2. Get the shortlist of candidate stocks to evaluate
3. For each stock (both candidates and current holdings):
   - Fetch fundamentals and recent news
   - Evaluate using the decision tool to get a recommendation
4. Based on the evaluations and available funds:
   - Recommend BUY actions for high-conviction opportunities (conviction >= 0.75)
   - Recommend HOLD for solid positions
   - Recommend TRIM or EXIT for underperforming positions (respecting 90-day minimum hold)
5. If you decide to execute trades, use the execute_trade tool (remember: it's mocked)
6. Provide a comprehensive summary of your analysis and decisions

Focus on long-term value, stability, and dividend income. Avoid trend-chasing.
Document your thought process clearly."""

    def format_email_report(self, agent_result: Dict[str, Any]) -> str:
        """Format agent results into an email report."""
        lines = [
            "=" * 60,
            "AI INVESTOR - AGENT ANALYSIS REPORT",
            "=" * 60,
            "",
            f"Analysis Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            f"Agent Iterations: {agent_result.get('iterations', 0)}",
            f"Tools Used: {len(agent_result.get('tool_calls', []))}",
            "",
            "=" * 60,
            "AGENT REASONING AND DECISIONS:",
            "=" * 60,
            "",
        ]
        
        # Add agent's main content
        content = agent_result.get("content", "No content available")
        lines.append(content)
        
        lines.extend([
            "",
            "=" * 60,
            "TOOL EXECUTION SUMMARY:",
            "=" * 60,
            "",
        ])
        
        # Summarize tool calls
        tool_calls = agent_result.get("tool_calls", [])
        if tool_calls:
            tool_summary: Dict[str, int] = {}
            for call in tool_calls:
                tool_name = call.get("tool", "unknown")
                tool_summary[tool_name] = tool_summary.get(tool_name, 0) + 1
            
            for tool_name, count in sorted(tool_summary.items()):
                lines.append(f"  {tool_name}: {count} call(s)")
            
            # Show failed tool calls if any
            failed_calls = [c for c in tool_calls if not c.get("success", True)]
            if failed_calls:
                lines.extend([
                    "",
                    "Failed Tool Calls:",
                ])
                for call in failed_calls:
                    lines.append(
                        f"  - {call.get('tool', 'unknown')}: {call.get('error', 'Unknown error')}"
                    )
        else:
            lines.append("  No tools were executed")
        
        lines.extend([
            "",
            "=" * 60,
            "This is an automated investment analysis report.",
            "All trades are MOCKED for testing purposes - no real transactions occurred.",
            "=" * 60,
        ])
        
        return "\n".join(lines)
