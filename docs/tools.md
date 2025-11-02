# MCP Tools

The AI Investor MCP server exposes the following tools through the Model Context Protocol. Each tool returns structured JSON-compatible data. Market data, fundamentals, and headlines are sourced from Tiingo's REST API using the configured API token.

- **portfolio**  
  Returns the current holdings and available funds from `data/portfolio.json`.

- **fetch_ticker_shortlist**  
  Provides the list of approved tickers loaded from `data/shortlist.json`.

- **fetch_investment_strategy**  
  Delivers the qualitative strategy description from `docs/investment_strategy.md`.

- **fetch_ticker_details** *(ticker, news_limit=5, news_timeframe="7d", include_growth_estimates=True)*  
  Combines yfinance fundamentals, analyst metrics, and growth projections with Tiingo-powered headlines for the requested ticker.

- **fetch_multiple_ticker_details** *(tickers, news_limit=5, news_timeframe="7d", include_growth_estimates=True, include_estimates=True)*  
  Runs the combined data-and-news retrieval for several tickers in parallel, returning a list of per-ticker payloads.

- **update_ticker_shortlist** *(candidates, min_market_cap=10_000_000_000, max_pe=35.0, max_forward_pe=35.0, max_beta=1.4, require_dividend=True, include_existing=True, max_companies=10)*  
  Uses Tiingo's ticker directory to locate matching U.S. and European companies (by symbol or name), ranks them by market capitalisation, applies the dividend/valuation filters, and persists the top `max_companies` entries to `data/shortlist.json`.

- **fetch_fear_greed_index**  
  Pulls the CNN Fear & Greed Index to gauge macro sentiment. No authentication required.

- **advice_investor** *(max_shortlist_tickers=5)*  
  Orchestrates strategy evaluation by loading the portfolio, shortlist, and strategy documents, fetching market data, computing analytic recommendations, and assembling a comprehensive advice report. The output contains both machine-readable details and human-readable summaries.

See `docs/overview.md` for module structure and `README.md` for runtime instructions.
