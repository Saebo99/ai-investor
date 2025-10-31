# MCP Tools Architecture

## Overview

The AI Investor now uses the Model Context Protocol (MCP) to enable Claude to autonomously interact with various data sources and systems. This creates a true agentic workflow where Claude can:

1. Query information as needed
2. Make decisions based on analysis
3. Execute actions (trades)
4. Report on its reasoning

## MCP Tools

### Portfolio Management Tools

#### `get_nordnet_positions`
- **Purpose**: Fetch current stock holdings
- **Input**: None
- **Output**: List of positions with ticker, quantity, prices, P&L
- **Example**:
```json
[
  {
    "ticker": "AAPL",
    "quantity": 10,
    "average_price": 150.50,
    "current_price": 175.20,
    "market_value": 1752.00,
    "unrealized_pnl": 247.00
  }
]
```

#### `get_available_funds`
- **Purpose**: Check available cash for trading
- **Input**: None
- **Output**: Account balances and values
- **Example**:
```json
{
  "currency": "USD",
  "available_cash": 10000.00,
  "total_value": 13505.75,
  "invested_value": 3505.75
}
```

### Data Retrieval Tools

#### `get_stock_fundamentals`
- **Purpose**: Fetch financial metrics from EODHD
- **Input**: `ticker` (string)
- **Output**: Fundamental data object with metrics like:
  - Dividend yield, P/E ratio
  - Profit margins, ROA, ROE
  - Debt ratios, beta
- **Example**:
```json
{
  "DividendYield": 0.025,
  "PE": 25.0,
  "NetProfitMargin": 0.15,
  "ReturnOnAssetsTTM": 12.5,
  "DebtToEquity": 0.8
}
```

#### `get_stock_news`
- **Purpose**: Fetch recent news articles
- **Input**: `ticker` (string), `lookback_days` (optional, default 30)
- **Output**: Array of news articles with titles, summaries, sentiment
- **Example**:
```json
[
  {
    "title": "Company Reports Strong Earnings",
    "summary": "Q3 results beat expectations...",
    "sentiment": "positive",
    "link": "https://..."
  }
]
```

#### `get_shortlist`
- **Purpose**: Get pre-screened candidate stocks
- **Input**: None
- **Output**: List of dividend-paying large cap stocks
- **Example**:
```json
{
  "tickers": [
    {"ticker": "AAPL", "name": "Apple Inc."},
    {"ticker": "MSFT", "name": "Microsoft"}
  ],
  "last_refresh": "2025-10-31"
}
```

### Analysis Tool

#### `evaluate_stock_decision`
- **Purpose**: Generate comprehensive investment thesis
- **Input**: 
  - `ticker` (string)
  - `fundamentals` (object from get_stock_fundamentals)
  - `news` (array from get_stock_news)
- **Output**: Investment thesis with:
  - Recommendation (BUY/HOLD/TRIM/EXIT)
  - Conviction score (0-1)
  - Quantitative, qualitative, stability scores
  - Rationale with holding period info
  - Catalysts and risks
- **Example**:
```json
{
  "ticker": "AAPL",
  "recommendation": "buy",
  "conviction": 0.82,
  "quantitative_score": 0.75,
  "qualitative_score": 0.85,
  "rationale": "Long-term investment analysis...",
  "catalysts": ["New product launch", "Market expansion"],
  "risks": ["Regulatory concerns"]
}
```

### Execution Tool

#### `execute_trade`
- **Purpose**: Place buy/sell orders (MOCKED)
- **Input**: 
  - `ticker` (string)
  - `side` ("buy" or "sell")
  - `quantity` (integer)
  - `price` (number)
- **Output**: Order confirmation with ID and details
- **Note**: Currently mocked - no real trades executed
- **Example**:
```json
{
  "order_id": "MOCK-20251031120000-AAPL",
  "ticker": "AAPL",
  "side": "buy",
  "quantity": 10,
  "price": 175.20,
  "total_value": 1752.00,
  "status": "simulated"
}
```

## Agent Workflow

### Typical Agent Execution

1. **Portfolio Assessment**
   - Call `get_nordnet_positions` to see what's held
   - Call `get_available_funds` to check buying power

2. **Candidate Discovery**
   - Call `get_shortlist` to get screened stocks

3. **Stock Analysis** (for each candidate and held position)
   - Call `get_stock_fundamentals` for financial metrics
   - Call `get_stock_news` for recent developments
   - Call `evaluate_stock_decision` to generate thesis

4. **Decision Making**
   - Review conviction scores and recommendations
   - Consider portfolio balance and available funds
   - Apply investment principles (long-term, dividends, stability)

5. **Trade Execution** (if warranted)
   - For BUY recommendations with conviction >= 0.75
   - For EXIT recommendations on held positions (respecting 90-day minimum)
   - Call `execute_trade` with appropriate parameters

6. **Reporting**
   - Compile analysis and reasoning
   - Document all tool calls and decisions
   - Send email report to investor

### Agent System Prompt

The agent is instructed to:
- Focus on long-term value investing
- Prefer dividend-paying large caps
- Consider stability as important as growth
- Respect minimum holding periods (90 days)
- Use higher threshold for new positions (0.75) vs holds (0.45)
- Document reasoning clearly

## Tool Executor

The `MCPToolExecutor` class bridges MCP tool calls to actual implementations:

```python
executor = MCPToolExecutor(
    nordnet_client=nordnet,
    eodhd_client=eodhd,
    decision_engine=engine,
    shortlist_pipeline=shortlist,
)

result = executor.execute("get_stock_fundamentals", {"ticker": "AAPL"})
```

## Email Reports

Agent generates comprehensive reports including:
- Portfolio overview
- Analysis for each stock
- Reasoning behind decisions
- Tool execution summary
- Any errors or issues encountered

Format includes:
- Main content: Agent's reasoning and conclusions
- Tool summary: Count of each tool used
- Failed calls: Any errors during execution

## Testing

Tests verify:
- Tool schemas are correctly defined
- Tool executor can call each tool
- Agent orchestrator creates proper prompts
- Email reports format correctly

Run tests:
```bash
pytest tests/test_mcp_tools.py
pytest tests/test_agent_orchestrator.py
```

## Future Enhancements

1. **Streaming Tool Responses**: For large data sets
2. **Tool Result Caching**: Avoid redundant API calls
3. **Partial Tool Execution**: Allow agent to handle partial failures
4. **Real-time Updates**: WebSocket for live market data
5. **Multi-agent Collaboration**: Specialized agents for different analysis aspects
