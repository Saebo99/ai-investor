"""Top-level orchestration and CLI entry points."""

from __future__ import annotations

import json
import logging
from typing import List

import typer
from rich.console import Console

from ai_investor.approvals.cli_gate import CliApprovalGateway
from ai_investor.broker.nordnet_client import NordnetClient
from ai_investor.config import get_settings
from ai_investor.data_providers.eodhd_client import EODHDClient
from ai_investor.decision.engine import DecisionEngine
from ai_investor.decision.models import Recommendation, Thesis
from ai_investor.logging.decision_log import thesis_logger
from ai_investor.shortlist.pipeline import ShortlistPipeline
from ai_investor.utils.emailer import send_email

console = Console()
logger = logging.getLogger(__name__)

app = typer.Typer(add_completion=False, help="AI Investor orchestration CLI")


class DailyOrchestrator:
    """Run shortlist, analysis, approval, and execution steps."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._shortlist = ShortlistPipeline()
        self._engine = DecisionEngine()
        self._approvals = CliApprovalGateway()
        self._thesis_log = thesis_logger()

    def _ticker_symbol(self, entry: dict) -> str:
        return entry.get("code") or entry.get("ticker") or entry.get("symbol")

    def _proposed_order(self, thesis: Thesis, snapshot: dict) -> dict | None:
        price = snapshot.get("close") or snapshot.get("previousClose")
        if price is None:
            return None
        side = "buy" if thesis.recommendation == Recommendation.BUY else None
        if thesis.recommendation == Recommendation.EXIT:
            side = "sell"
        if not side:
            return None
        quantity = max(1, int(1000 // float(price)))
        return {
            "ticker": thesis.ticker,
            "side": side,
            "quantity": quantity,
            "price": float(price),
        }

    def run(self) -> None:
        shortlist = self._shortlist.ensure_shortlist()
        tickers = shortlist.get("tickers", [])
        console.print(f"Evaluating {len(tickers)} shortlisted securities")

        theses: List[Thesis] = []
        with EODHDClient() as client:
            for entry in tickers:
                ticker = self._ticker_symbol(entry)
                if not ticker:
                    continue
                fundamentals = client.get_fundamentals(ticker)
                news = client.get_news(ticker)
                thesis = self._engine.evaluate(ticker, fundamentals, news)
                self._thesis_log.append(thesis.dict())
                theses.append(thesis)
                proposed_order = self._proposed_order(thesis, entry)
                if thesis.recommendation in {Recommendation.BUY, Recommendation.EXIT}:
                    result = self._approvals.request(thesis, proposed_order)
                    if result.approved and proposed_order:
                        try:
                            with NordnetClient() as broker:
                                broker.authenticate()
                                broker.place_order(
                                    ticker=proposed_order["ticker"],
                                    side=proposed_order["side"],
                                    quantity=proposed_order["quantity"],
                                    price=proposed_order["price"],
                                )
                        except NotImplementedError:
                            console.print("Nordnet integration not yet implemented; skipping order.")
                        except Exception as exc:  # noqa: BLE001
                            logger.exception("Failed to submit order for %s: %s", ticker, exc)

        self._send_summary_email(theses)

    def run_shortlist(self) -> None:
        data = self._shortlist.refresh()
        console.print(json.dumps(data, indent=2))

    def run_report(self) -> None:
        shortlist = self._shortlist.ensure_shortlist()
        console.print("Current shortlist:")
        console.print(json.dumps(shortlist, indent=2))

    def _send_summary_email(self, theses: List[Thesis]) -> None:
        if not theses:
            return
        lines = ["Daily AI Investor Summary", ""]
        for thesis in theses:
            lines.append(
                f"{thesis.ticker}: {thesis.recommendation.value.upper()} (conviction {thesis.conviction:.2f})"
            )
        send_email("AI Investor Daily Summary", "\n".join(lines))


@app.command(name="run-daily")
def run_daily() -> None:
    """Execute the full orchestration pipeline once."""

    orchestrator = DailyOrchestrator()
    orchestrator.run()


@app.command(name="run-shortlist")
def run_shortlist() -> None:
    """Force-refresh the shortlist and print results."""

    orchestrator = DailyOrchestrator()
    orchestrator.run_shortlist()


@app.command(name="run-report")
def run_report() -> None:
    """Print the current shortlist without trading."""

    orchestrator = DailyOrchestrator()
    orchestrator.run_report()


def run_cli() -> None:
    """Entrypoint for console script."""

    logging.basicConfig(level=logging.INFO)
    app()
