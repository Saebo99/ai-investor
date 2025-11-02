# Project Overview

The AI Investor MCP server exposes investment analysis capabilities to MCP-compatible clients such as Codex or Claude Code. It combines structured local data (current portfolio, approved tickers, investment strategy) with live market information from Yahoo Finance (via `yfinance`) for fundamentals and Tiingo for headlines/search.

## Components

- **MCP Server (`ai_investor.server`)**  
  FastMCP-based server that registers tools for portfolio inspection, market data retrieval, and action recommendations.

- **Data Layer (`ai_investor.data`)**  
  Utilities that load local JSON/Markdown assets in `data/` and `docs/`.

- **Integrations (`ai_investor.integrations`)**  
  Clients for external services (Yahoo Finance for fundamentals/estimates, Tiingo for news and ticker discovery, and the Fear & Greed Index).

- **Advisory Engine (`ai_investor.advice`)**  
  Rule-based analysis that consolidates strategy guidance, portfolio composition, and market signals into actionable recommendations.

## Local Assets

- `data/portfolio.json` — current holdings, position sizing targets, and available funds.
- `data/shortlist.json` — approved tickers for potential allocation.
- `docs/investment_strategy.md` — qualitative strategy definition used during advice generation.
- `docs/advice_investor.md` — detailed walkthrough of the orchestration logic behind the `advice_investor` tool.

These assets can be adapted to match the investor's actual profile without code changes.
