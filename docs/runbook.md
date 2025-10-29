# AI Investor Runbook

## Daily Orchestration
- Entry command: `ai-investor run-daily` (see CLI usage below).
- Default schedule: 06:00 UTC via APScheduler cron expression `0 6 * * *`.
- Recommended deployment: containerised job triggered by the hosting platform (e.g., AWS Fargate scheduled task).

## Prerequisites
- Python 3.10+
- Valid API credentials exported in `.env` or environment variables:
  - `ANTHROPIC_API_KEY`
  - `EODHD_API_KEY`
  - `NORDNET_USERNAME`, `NORDNET_PASSWORD`, `NORDNET_ACCOUNT_ID`
- Outbound HTTPS access to EODHD and Nordnet endpoints.

## CLI Commands
```
ai-investor run-daily
    Executes shortlist refresh, analysis, approvals, trade submission, and summary email.

ai-investor run-shortlist
    Forces shortlist regeneration and prints resulting candidates.

ai-investor run-report
    Generates portfolio performance snapshot and email summary without trading.
```

## Operational Flow
1. Scheduler starts the service.
2. Shortlist refresh executes if `SHORTLIST_REFRESH_DAYS` elapsed.
3. Agents fetch fundamentals/news; decision engine outputs theses.
4. CLI approval gate prompts operator for each proposed trade.
5. Approved orders execute against Nordnet.
6. Trade and thesis logs append to JSONL artifacts under `data/`.
7. Email summary dispatches via configured SMTP credentials.

## Human Approval Process
- Operator reviews CLI-rendered thesis argument, risk flags, and proposed order size.
- Respond `y` to queue order, `n` to cancel, or `s` to skip for later review.
- All responses persisted with timestamps for audit.

## Email Summaries
- Configure `EMAIL_SMTP_SERVER`, `EMAIL_FROM`, `EMAIL_RECIPIENTS`.
- Service sends post-run digest including shortlist changes, executed trades, and open watchlist items.

## Monitoring & Alerts
- Log files: `data/thesis_log.jsonl`, `data/trade_log.jsonl`.
- Enable container platform health checks; escalate on non-zero exit codes.
- Integrate SMTP failure handling to raise warnings in logs.

## Disaster Recovery
- Re-run latest job once connectivity restored; idempotent design ensures Nordnet orders are not resent without new approval tokens.
- Maintain off-site backup of log files for compliance.

## Maintenance Tasks
- Rotate API keys quarterly.
- Review shortlist rules monthly to adjust filters and diversification targets.
- Update dependency versions via `uv`/`pip` or hatch build process.
