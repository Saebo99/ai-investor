# Getting Started

## Prerequisites
- Python 3.11+
- An Anthropic API key with Claude access
- EODHD API key and Nordnet credentials (or stub replacements for testing)

## Setup
1. Create a virtual environment.
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies.
   ```bash
   pip install -e ".[dev]"
   ```
3. Copy the environment template and fill in credentials.
   ```bash
   cp .env.example .env
   ```
4. Adjust the strategy document under `strategy/minimise_risk_long_term.md` if needed.

## Running the Workflow
- Execute the sample runner to fetch data and produce recommendations.
  ```bash
  python -m ai_investor.runner
  ```
- Expect placeholder behaviour until the data integrations are completed.

## Next Steps
- Integrate the Claude Agent SDK to evaluate `InvestmentDecision` outputs before execution.
- Expand tests under `tests/` (to be created) to lock in screening logic.
- Introduce CLI arguments for ticker selection and output formatting.
