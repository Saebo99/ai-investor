"""MCP (Model Context Protocol) tool definitions for Claude Agent."""

from __future__ import annotations

from typing import Any, Callable, Dict, List

# MCP Tool schema definitions
MCP_TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "get_nordnet_positions",
        "description": (
            "Fetch current stock positions held in the Nordnet account. "
            "Returns a list of positions with ticker, quantity, average price, "
            "current price, market value, and unrealized P&L."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_available_funds",
        "description": (
            "Fetch available cash and account value from Nordnet. "
            "Returns currency, available cash, total account value, and invested value."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_stock_fundamentals",
        "description": (
            "Fetch fundamental data for a stock from EODHD API. "
            "Returns financial metrics including dividend yield, P/E ratio, "
            "profit margins, ROA, ROE, debt ratios, and more."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., 'AAPL', 'MSFT')",
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "get_stock_news",
        "description": (
            "Fetch recent news articles for a stock from EODHD API. "
            "Returns news headlines, summaries, sentiment, and links from the past 30 days."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., 'AAPL', 'MSFT')",
                },
                "lookback_days": {
                    "type": "integer",
                    "description": "Number of days to look back for news (default: 30)",
                    "default": 30,
                },
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "evaluate_stock_decision",
        "description": (
            "Analyze a stock and determine investment decision (BUY/HOLD/TRIM/EXIT). "
            "This tool uses quantitative metrics, qualitative news analysis, and stability "
            "indicators to generate a comprehensive investment thesis with conviction score, "
            "rationale, risks, and catalysts. Takes into account current positions and "
            "holding periods for long-term investment strategy."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol to evaluate",
                },
                "fundamentals": {
                    "type": "object",
                    "description": "Fundamental data object from get_stock_fundamentals",
                },
                "news": {
                    "type": "array",
                    "description": "News articles array from get_stock_news",
                    "items": {"type": "object"},
                },
            },
            "required": ["ticker", "fundamentals", "news"],
        },
    },
    {
        "name": "execute_trade",
        "description": (
            "Execute a stock trade (buy/sell) on Nordnet. THIS IS MOCKED FOR TESTING. "
            "Simulates placing an order and updates mock positions. Returns order details "
            "including order ID, ticker, side, quantity, price, and status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol to trade",
                },
                "side": {
                    "type": "string",
                    "description": "Trade side: 'buy' or 'sell'",
                    "enum": ["buy", "sell"],
                },
                "quantity": {
                    "type": "integer",
                    "description": "Number of shares to trade",
                    "minimum": 1,
                },
                "price": {
                    "type": "number",
                    "description": "Price per share",
                    "minimum": 0,
                },
            },
            "required": ["ticker", "side", "quantity", "price"],
        },
    },
    {
        "name": "get_shortlist",
        "description": (
            "Get the current shortlist of candidate stocks to analyze. "
            "Returns dividend-paying large cap stocks that meet screening criteria."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


class MCPToolExecutor:
    """Execute MCP tool calls with actual implementation functions."""

    def __init__(
        self,
        nordnet_client: Any,
        eodhd_client: Any,
        decision_engine: Any,
        shortlist_pipeline: Any,
    ) -> None:
        self.nordnet = nordnet_client
        self.eodhd = eodhd_client
        self.engine = decision_engine
        self.shortlist = shortlist_pipeline
        
        # Map tool names to implementation functions
        self._tool_map: Dict[str, Callable] = {
            "get_nordnet_positions": self._get_positions,
            "get_available_funds": self._get_funds,
            "get_stock_fundamentals": self._get_fundamentals,
            "get_stock_news": self._get_news,
            "evaluate_stock_decision": self._evaluate_decision,
            "execute_trade": self._execute_trade,
            "get_shortlist": self._get_shortlist,
        }

    def execute(self, tool_name: str, tool_input: Dict[str, Any]) -> Any:
        """Execute a tool by name with given input."""
        if tool_name not in self._tool_map:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        handler = self._tool_map[tool_name]
        return handler(**tool_input)

    def _get_positions(self) -> List[Dict[str, Any]]:
        """Get current Nordnet positions."""
        return self.nordnet.list_positions()

    def _get_funds(self) -> Dict[str, float]:
        """Get available funds."""
        return self.nordnet.get_available_funds()

    def _get_fundamentals(self, ticker: str) -> Dict[str, Any]:
        """Get stock fundamentals."""
        return self.eodhd.get_fundamentals(ticker)

    def _get_news(self, ticker: str, lookback_days: int = 30) -> List[Dict[str, Any]]:
        """Get stock news."""
        return self.eodhd.get_news(ticker, lookback_days)

    def _evaluate_decision(
        self, ticker: str, fundamentals: Dict[str, Any], news: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate investment decision for a stock."""
        thesis = self.engine.evaluate(ticker, fundamentals, news)
        return thesis.dict()

    def _execute_trade(
        self, ticker: str, side: str, quantity: int, price: float
    ) -> Dict[str, Any]:
        """Execute a trade (mocked)."""
        return self.nordnet.place_order(
            ticker=ticker, side=side, quantity=quantity, price=price
        )

    def _get_shortlist(self) -> Dict[str, Any]:
        """Get current shortlist."""
        return self.shortlist.ensure_shortlist()
