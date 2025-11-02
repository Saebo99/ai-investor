# Setup Guide

## Prerequisites

- Python 3.11 or newer.
- `uv` package manager (recommended) or `pip`.
- Tiingo account with API access (set `TIINGO_API_TOKEN` in your environment) for news headlines.

## Installation

```bash
uv sync
# or
pip install -e .
```

This installs the project package along with its runtime dependencies (`httpx`, `mcp`, `pydantic`, `python-dotenv`, `yfinance`).

## Environment configuration

Create a `.env` file alongside `pyproject.toml` if you need to configure optional settings (e.g., overriding data/document directories, providing the Fear & Greed endpoint, or setting `TIINGO_API_TOKEN`).

## Running the MCP server

```bash
uv run ai-investor-server
```

This starts the FastMCP server over stdio so MCP-compatible clients (e.g., Claude Desktop, Codex CLI) can interact with the tools defined in `src/ai_investor/tooling/tools.py`.

For development, you can also run:

```bash
uv run mcp dev src/ai_investor/server.py
```

which integrates with the MCP Inspector for interactive testing.

## Codex CLI integration

Add the server to `~/.codex/config.toml` (see official Codex docs for details):

```toml
[mcp_servers.ai_investor]
command = "/Users/your-user/Dev/ai-investor/.venv/bin/python"
args = ["-m", "ai_investor.server"]
cwd = "/Users/your-user/Dev/ai-investor"
startup_timeout_sec = 20
tool_timeout_sec = 90
```

Replace the paths with your local checkout. Codex will launch the MCP server via stdio, and the `cwd` ensures local `data/` and `docs/` assets resolve correctly. Optional environment variables:

- `AI_INVESTOR_BASE_DIR` — override the base directory used to locate data/docs.
- `AI_INVESTOR_DATA_DIR` / `AI_INVESTOR_DOCS_DIR` — point directly to custom resource folders.
