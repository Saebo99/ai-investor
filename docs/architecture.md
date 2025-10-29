# AI Investor Architecture

## Overview
The AI Investor system is a Claude Agent SDK–driven Python service that automates long-term equity research, thesis formation, and trade execution under human supervision. It uses MCP tools to gather data, relies on the EODHD API for fundamentals and news, and interfaces with the Nordnet API for order routing. All trade decisions require explicit human approval via a CLI prompt.

```
Claude Agent SDK ──> Research Agent ──┐
                                   │    ┌──> Decision Engine ──┐
MCP Tools (screeners, news) ──> Shortlist Builder ─────────────┤
EODHD API  ────────────────> Data Provider Layer ──────────────┤
                                   │                          ├──> Approval CLI Gate ──> Nordnet API
Portfolio State ───────────────────┘                          │
                                                              └──> Logging & Reporting (CLI, email, JSONL)
```

## Core Components

- **Shortlist Builder (`src/ai_investor/shortlist/pipeline.py`)**
  - Maintains a rolling shortlist of dividend-oriented large-cap equities using MCP-powered screeners and cached EODHD fundamentals.
  - Refresh cadence is configurable (default weekly) to focus downstream analysis on a tractable universe.

- **Data Provider Layer (`src/ai_investor/data_providers/eodhd_client.py`)**
  - Wraps EODHD REST endpoints for fundamentals, income statements, and curated news. Implements retry logic, request caching, and request shaping for Claude consumption.

- **Decision Engine (`src/ai_investor/decision/engine.py`)**
  - Blends quantitative metrics (dividend yield, payout ratio, growth, valuation) with qualitative narratives distilled via Claude from EODHD news.
  - Emits structured investment theses detailing buy/hold/sell recommendations, confidence scores, and exit triggers.

- **Claude Agents (`src/ai_investor/agents/`)**
  - Research Agent orchestrates MCP queries, data summarisation, and thesis drafting.
  - Portfolio Agent reviews holdings versus shortlist, proposes rebalances, and flags exits.
  - Execution Agent prepares Nordnet orders once human approval is granted.

- **Approval Gate (`src/ai_investor/approvals/cli_gate.py`)**
  - Presents pending trades and rationales in the terminal, collects yes/no confirmation, and logs the decision.

- **Broker Integration (`src/ai_investor/broker/nordnet_client.py`)**
  - Handles authentication with Nordnet, order placement, portfolio queries, and telemetry capturing responses for auditing.

- **Orchestration Service (`src/ai_investor/orchestration/service.py`)**
  - Schedules daily evaluations via APScheduler, coordinates Claude workflows, enforces approvals, and triggers reporting.

- **Logging & Reporting (`src/ai_investor/logging/decision_log.py`, `docs/runbook.md`)**
  - Persists thesis JSONL records, trade logs, and dispatches optional email summaries after each run.

## Data Flow
1. Scheduler triggers orchestration service.
2. Shortlist builder refreshes candidate list if stale.
3. Data provider loads fundamentals and news for shortlist symbols.
4. Research and decision agents assemble investment theses.
5. Recommendations feed into approval CLI for human validation.
6. Approved trades are submitted to Nordnet via execution agent.
7. Logs, theses, and email summaries are produced for auditability.

## MCP Tooling
- **Screeners:** Identify dividend-paying large-cap tickers per exchange.
- **News Monitor:** Fetch latest earnings, strategic initiatives, and risks.
- **Portfolio Tracker:** Pull Nordnet holdings snapshots for Claude context.

MCP tools are invoked by Claude agents to gather structured JSON inputs used by the decision engine.

## Hosting Strategy
- Package the service as a container image (Docker) with entrypoint invoking `ai-investor` CLI.
- Deploy to a cost-efficient scheduler (e.g., AWS Fargate with EventBridge, Azure Container Apps jobs, or Fly.io Machines) running daily.
- Persist state via mounted volume or managed object storage for JSONL logs.
- Configure alerts on job failures and email delivery errors.

## Security Considerations
- Store secrets in `.env` for local development; promote to managed secrets in production deployments.
- Encrypt trade logs or restrict access because they contain account identifiers.
- Rate-limit EODHD and Nordnet requests and log anomalies for manual review.
