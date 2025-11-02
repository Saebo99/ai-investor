# AI Investor

**Description:** The AI investor is an MCP server that can be used by MCP clients such as Codex and Claude Code. The MCP server will be able to answer questions about single stock, or provide complete investment advice based on an investment strategy, a current portfolio, and available funds.

## Tech-stack
- Python
- MCP
- Yahoo Finance via `yfinance` (fundamentals, pricing, estimates)
- Tiingo REST API (news and ticker search)

## Available tools
- portfolio
    - Fetches the current user portfolio (this will, for now, just be a local file with current holdings and available funds)
- fetch_ticker_details
    - Fetches yfinance fundamentals, pricing, and growth data together with Tiingo news for a single ticker in one call.
- fetch_multiple_ticker_details
    - Fetches the combined Tiingo data-and-news payload for several tickers concurrently and returns an array of results.
- update_ticker_shortlist
    - Screens U.S. and European candidates against the low-risk, large-cap strategy filters using Tiingo fundamentals, ranks them by size, and persists the top `max_companies` tickers (default 10).
- fetch_fear_greed_index
    - Fetches the CNN Fear & Greed Index
- fetch_ticker_shortlist
    - Fetches the shortlist of tickers that can be invested in by the investor (this will, for now, simply be a local file with list of tickers)
- fetch_investment_strategy
    - Fetches the investment strategy (this is just a local markdown file describing the trading strategy)
- advice_investor
    - Uses its other tools to:
        1. Fetches the investment strategy
        2. Analyse the health of each ticker in the current portfolio
        3. Analyse the other tickers in the shortlist
        4. Determines, based on the strategy, current portfolio, and available funds, what is the best course of action for the investor.
        5. Provides a detailed and comprehensive report of the tickers in the current portfolio, the most notable tickers not currently owned, the best course of action for the investor, and the thoughtprocess and reasoning behind the decisions made.

## Investment strategy
- Long-term investing
- Avoid risks
- Look for very large companies, preferably with dividends, that have high potential upside in the long-term
- Do not invest in ethically questionable sectors (weapons, tobacco, etc.)
- Look for sectors with high potential upside in the future and aim for large players in these sectors
- Never invest in stocks that, based on statistics, might be overvalued

## Considerations
- Ensure good standards when coding
- Add documentation in a "docs" directory containing descriptions of code, functionality, etc.
- Ensure that the project environment is setup properly
- Use the most up-to-date documentation through context7
- Review `docs/advice_investor.md` for a deep dive into the portfolio advice pipeline.
- Provide a valid `TIINGO_API_TOKEN` in the environment to enable news retrieval.
