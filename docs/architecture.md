# AI Investor Architecture

## Overview
- **Goal:** Automate conservative portfolio management aligned with the provided investment strategy.
- **Approach:** Combine deterministic financial screening with Claude-driven analysis and reporting.

## Components
- **Configuration (`ai_investor.config`):** Loads environment variables, strategy documents, and report recipients.
- **Data Layer (`ai_investor.data`):** Provides async clients for EODHD market data and Nordnet holdings. Replace stubs with real integrations.
- **Analysis (`ai_investor.analysis`):** Normalises raw data into `CompanySnapshot` objects, filters candidates, and produces `InvestmentDecision` instances.
- **Portfolio (`ai_investor.portfolio`):** Orchestrates data retrieval, applies the analyzer, and prepares actions for execution or review.
- **Reporting (`ai_investor.reporting`):** Generates email summaries to keep stakeholders informed.
- **Entry Point (`ai_investor.runner`):** Wires everything together. Future versions will integrate directly with the Claude Agent SDK for iterative reasoning.

## Future Enhancements
- Replace stubbed Nordnet integration with authenticated API calls or scraping.
- Use Claude Agent SDK to critique and refine the `InvestmentDecision` list.
- Expand risk modelling (volatility, beta, drawdown simulations).
- Persist historical analyses for longitudinal tracking.
- Deliver HTML/PDF reports with richer analytics.
