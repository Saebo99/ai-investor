# `advice_investor` Tool Walkthrough

The `advice_investor` tool is the orchestration layer that combines local configuration, live market data, and a rule-based analysis engine to produce an actionable portfolio update. This document explains the data flow and the supporting modules so you can customise or extend the behaviour with confidence.

## High-level workflow

1. **Load static context**  
   The tool pulls the current portfolio (`data/portfolio.json`), the shortlist of eligible tickers (`data/shortlist.json`), and the investment strategy notes (`docs/investment_strategy.md`) using helpers in `ai_investor.data_access`.

2. **Consolidate tickers**  
   It builds a unique set of tickers consisting of current holdings and the top `max_shortlist_tickers` candidates from the shortlist. This keeps downstream data fetches bounded while still covering both existing positions and potential opportunities.

3. **Fetch market fundamentals**  
   Through `EODHDClient` the tool requests Yahoo Finance (`yfinance`) fundamentals and pricing while Tiingo supplies the news headlines. The `_gather_metrics` helper runs these calls concurrently, surfaces soft failures as MCP warnings, and falls back gracefully when data is missing.

4. **Analyse holdings and shortlist**  
   The `PortfolioAnalyzer` evaluates each holding’s weight, cost basis, and live metrics. The `AdviceComposer` combines those insights with strategy rules, the fear & greed reading, and available cash to decide whether to buy, trim, hold, or watch.

5. **Assemble a report**  
   Results are captured in an `AdviceReport` Pydantic model—this encapsulates the reasoning, headline recommendations, and supporting data (e.g., fear & greed snapshot). The tool finally serialises that model via `.model_dump()` for the MCP response.

## Key modules

| Module | Responsibility | Relevant APIs |
| ------ | -------------- | ------------- |
| `ai_investor.tooling.tools` | MCP tool definitions and request handling | `advice_investor`, `_gather_metrics` |
| `ai_investor.data_access` | Loading JSON/Markdown assets from disk | `load_portfolio`, `load_ticker_shortlist`, `load_investment_strategy` |
| `ai_investor.integrations.eodhd` | Yahoo Finance fundamentals + Tiingo news | `EODHDClient.get_fundamentals`, `EODHDClient.get_growth_estimates` |
| `ai_investor.services.portfolio` | Portfolio analytics (position sizing, allocation deltas) | `PortfolioAnalyzer` |
| `ai_investor.services.advice` | Recommendation synthesis & narrative output | `AdviceComposer`, `format_recommendation_summary` |
| `ai_investor.integrations.fear_greed` | Macro sentiment feed | `FearGreedClient.fetch_index` |

## Execution details (code references)

- **Tool entry point** – `src/ai_investor/tooling/tools.py:166`. Handles MCP context logging, pulls local assets, and prepares the ticker set.
- **Metric gathering** – `src/ai_investor/tooling/tools.py:36`. Uses `asyncio.as_completed` to fetch fundamentals concurrently and warn (rather than fail) when a ticker cannot be retrieved.
- **Market data client** – `src/ai_investor/integrations/eodhd.py`. Pulls fundamentals, pricing, and estimates from yfinance while using Tiingo for headlines and ticker search.
- **Advice engine** – `src/ai_investor/services/advice.py`. Combines portfolio analytics, the investment strategy, and the fear & greed reading into structured actions.
- **Report shape** – `src/ai_investor/models.py:44`. The `AdviceReport` model defines the JSON schema the MCP tool returns to clients.

## Customisation tips

- **Strategy tuning**: adjust `docs/investment_strategy.md` for qualitative guidance or extend `AdviceComposer` rules for quantitative tweaks.
- **Ticker scope**: alter `max_shortlist_tickers` when calling the MCP tool to include more (or fewer) shortlist candidates in the analysis.
- **Market data provider**: `EODHDClient` is the abstraction point—swap or extend this class if you prefer another free data source.
- **Macro signals**: `FearGreedClient` currently reads CNN's index; you can plug in alternative sentiment indicators by adapting this client and updating the advice composer.

## Error handling & logging

- The tool uses MCP context logging (`ctx.debug`, `ctx.warning`) to keep clients informed without aborting the run.
- Missing market data downgrades the affected ticker rather than failing the entire request. The output still includes available analysis plus notes about missing data.
- Any unexpected exception propagates as an MCP error response, so clients see a deterministic failure instead of silent truncation.

Use this guide as a starting point for deeper customisation or for onboarding contributors who need to understand the advice pipeline end to end.
