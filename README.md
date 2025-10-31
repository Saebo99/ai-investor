# AI Investor

**Short description:** The AI investor is an agentic investor that uses fundamental analysis in order to find the optimal long-term stocks to invest in.
It also keeps up with news, numbers, results, etc. in order to continuously update its portfolio. 
It uses Claude with MCP (Model Context Protocol) tools to perform research on stocks, follow latest news, keep track of its portfolio, and execute trades (mocked for testing).

These are its fundamental strategic points:
1. Never invest in risky assets. "Monopolies"/large companies that still have high upside long-term, are preferred in order to reduce risk.
2. The goal is always to find stocks that can be held for a several months to several years.
3. Stocks distributing dividends are preferred.
4. Diversification, in both number of companies and number of industries, is key without spreading too thin.

## Features

### Agent-Based Workflow (NEW)
The AI Investor now supports a Claude-powered agent that autonomously:
- Fetches current Nordnet portfolio positions and available funds
- Retrieves stock fundamentals and news from EODHD
- Evaluates investment decisions using quantitative + qualitative + stability analysis
- Executes trades based on high-conviction opportunities (mocked for testing)
- Sends comprehensive email reports with thought processes and decisions

Available MCP Tools:
- `get_nordnet_positions` - Fetch current holdings
- `get_available_funds` - Check available cash
- `get_stock_fundamentals` - Get financial metrics from EODHD
- `get_stock_news` - Fetch recent news articles
- `evaluate_stock_decision` - Generate investment thesis with conviction score
- `execute_trade` - Place buy/sell orders (mocked)
- `get_shortlist` - Get pre-screened dividend-paying large caps

### Traditional Workflow
The original orchestrated workflow is still available for direct control:
- Shortlist management with dividend-paying large cap screening
- Fundamental analysis and news sentiment evaluation
- CLI approval gates for trade execution
- Persistent thesis logging

## Getting Started

```bash
cp .env.example .env  # fill in Anthropic, EODHD, and Nordnet credentials
pip install -e .[dev]

# Run the agent-based workflow (recommended)
ai-investor run-agent

# Or run the traditional workflow
ai-investor run-daily

# Other commands
ai-investor run-shortlist  # Refresh shortlist only
ai-investor list-positions  # View current positions
```

## Commands

- **`ai-investor run-agent`** - NEW: Execute agent-based workflow with MCP tools. Claude autonomously analyzes stocks, makes decisions, and executes trades (mocked). Sends email report with reasoning.
- **`ai-investor run-daily`** - Execute the traditional orchestration pipeline with CLI approval gates.
- **`ai-investor run-shortlist`** - Force-refresh the shortlist and print results.
- **`ai-investor list-positions`** - View current Nordnet positions (mocked data).

## Configuration

Environment variables (`.env`):
```bash
# Required
ANTHROPIC_API_KEY=your-key
EODHD_API_KEY=your-key
NORDNET_USERNAME=your-username
NORDNET_PASSWORD=your-password
NORDNET_ACCOUNT_ID=your-account-id

# Optional - Email notifications
EMAIL_SMTP_SERVER=smtp.gmail.com:587
EMAIL_FROM=ai-investor@yourdomain.com
EMAIL_RECIPIENTS=you@email.com,partner@email.com

# Optional - Tuning
SHORTLIST_TARGET_SIZE=25
SHORTLIST_REFRESH_DAYS=7
```

## Architecture

### Agent-Based Flow (MCP Tools)
1. Claude agent receives initial task to analyze portfolio
2. Agent uses MCP tools to:
   - Fetch positions and available funds
   - Get shortlist of candidates
   - Retrieve fundamentals and news for each stock
   - Evaluate using decision engine
   - Execute trades for high-conviction opportunities
3. Agent generates comprehensive report with reasoning
4. Email sent with analysis and decisions

### Decision Engine
- **Quantitative Score** (50%): Dividend yield, payout ratio, profit margin, ROA, ROE
- **Qualitative Score** (35%): News sentiment analysis via Claude
- **Stability Score** (15%): Debt-to-equity, beta, earnings consistency
- **Position-Aware Thresholds**: Different buy/hold/exit thresholds for new vs existing positions
- **Minimum Holding Period**: 90-day protection against premature exits

### Trading (Mocked)
All trades are currently mocked for testing. The system simulates:
- Order placement with timestamp and order ID
- Position updates (buy adds shares, sell removes shares)
- No real money is exchanged

## Testing

```bash
pip install -e .[dev]
pytest tests/
```

## Development

Key modules:
- `agents/` - Claude agent with MCP tools, orchestrator
- `broker/` - Nordnet API client (mocked)
- `data_providers/` - EODHD API client
- `decision/` - Investment thesis engine
- `orchestration/` - Workflow orchestration
- `logging/` - JSONL thesis and trade logging
- `utils/` - Email notifications

## Roadmap

- [ ] Real Nordnet API integration (currently mocked)
- [ ] Portfolio-level optimization (correlation, sector exposure)
- [ ] Dynamic thresholds based on market conditions (VIX, yield curve)
- [ ] Tax-loss harvesting identification
- [ ] Risk-adjusted returns (Sharpe ratio) in conviction scoring
