"""Entry point for the AI Investor MCP server."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ai_investor.tooling.tools import mcp


def get_server() -> FastMCP:
    """Return the configured FastMCP server instance."""

    return mcp


def run() -> None:
    """Run the MCP server using stdio transport."""

    get_server().run()


if __name__ == "__main__":
    run()
