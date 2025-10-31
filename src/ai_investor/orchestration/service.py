"""Top-level orchestration and CLI entry points."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
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
        self._engine = None  # Will initialize with positions in run()
        self._approvals = CliApprovalGateway()
        self._thesis_log = thesis_logger()
        self._thesis_log_path = self._settings.thesis_storage_path

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
        # Fetch current positions first
        positions = []
        try:
            with NordnetClient(mock_mode=True) as broker:
                broker.authenticate()
                positions = broker.list_positions()
                logger.info("Fetched %d current positions", len(positions))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to fetch positions (continuing with empty): %s", exc)
        
        # Initialize decision engine with positions and thesis log path
        self._engine = DecisionEngine(
            positions=positions, 
            thesis_log_path=Path(self._thesis_log_path)
        )
        
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
                            with NordnetClient(mock_mode=True) as broker:
                                broker.authenticate()
                                order_result = broker.place_order(
                                    ticker=proposed_order["ticker"],
                                    side=proposed_order["side"],
                                    quantity=proposed_order["quantity"],
                                    price=proposed_order["price"],
                                )
                                console.print(f"[yellow]Order submitted (MOCK): {order_result['order_id']}[/yellow]")
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
            logger.info("No theses to email")
            return
        
        lines = [
            "="*60,
            "AI INVESTOR - DAILY SUMMARY",
            "="*60,
            "",
            f"Analysis Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
            f"Total Securities Evaluated: {len(theses)}",
            "",
        ]
        
        # Group by recommendation
        buys = [t for t in theses if t.recommendation == Recommendation.BUY]
        holds = [t for t in theses if t.recommendation == Recommendation.HOLD]
        trims = [t for t in theses if t.recommendation == Recommendation.TRIM]
        exits = [t for t in theses if t.recommendation == Recommendation.EXIT]
        
        if buys:
            lines.extend([
                "BUY RECOMMENDATIONS:",
                "-" * 60,
            ])
            for thesis in sorted(buys, key=lambda t: t.conviction, reverse=True):
                lines.extend([
                    f"\n{thesis.ticker} - Conviction: {thesis.conviction:.2f}",
                    f"  Quantitative: {thesis.quantitative_score:.2f} | Qualitative: {thesis.qualitative_score:.2f}",
                    f"  Catalysts: {', '.join(thesis.catalysts) if thesis.catalysts else 'None'}",
                    f"  Risks: {', '.join(thesis.risks) if thesis.risks else 'None'}",
                ])
        
        if exits:
            lines.extend([
                "",
                "EXIT RECOMMENDATIONS:",
                "-" * 60,
            ])
            for thesis in sorted(exits, key=lambda t: t.conviction):
                lines.extend([
                    f"\n{thesis.ticker} - Conviction: {thesis.conviction:.2f}",
                    f"  Quantitative: {thesis.quantitative_score:.2f} | Qualitative: {thesis.qualitative_score:.2f}",
                    f"  Risks: {', '.join(thesis.risks) if thesis.risks else 'None'}",
                ])
        
        if holds:
            lines.extend([
                "",
                f"HOLD RECOMMENDATIONS: {len(holds)} positions",
                "-" * 60,
            ])
            for thesis in sorted(holds, key=lambda t: t.conviction, reverse=True)[:5]:  # Top 5 holds
                lines.append(
                    f"  {thesis.ticker}: {thesis.conviction:.2f} "
                    f"(Q:{thesis.quantitative_score:.2f} QL:{thesis.qualitative_score:.2f})"
                )
        
        if trims:
            lines.extend([
                "",
                f"TRIM RECOMMENDATIONS: {len(trims)} positions",
            ])
            for thesis in trims:
                lines.append(f"  {thesis.ticker}: {thesis.conviction:.2f}")
        
        lines.extend([
            "",
            "="*60,
            "This is an automated investment analysis report.",
            "All recommendations require manual approval before execution.",
            "="*60,
        ])
        
        try:
            send_email("AI Investor Daily Summary", "\n".join(lines))
            logger.info("Summary email sent successfully")
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to send summary email: %s", exc)


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


@app.command(name="list-positions")
def list_positions() -> None:
    """List current positions from Nordnet (mocked)."""

    from ai_investor.broker.nordnet_client import NordnetClient

    try:
        with NordnetClient(mock_mode=True) as broker:
            positions = broker.list_positions()
            if positions:
                console.print("[bold]Current Positions (MOCK DATA):[/bold]")
                for pos in positions:
                    console.print(
                        f"  {pos['ticker']}: {pos['quantity']} shares @ ${pos['average_price']:.2f} "
                        f"(Current: ${pos['current_price']:.2f}, P/L: ${pos['unrealized_pnl']:.2f} / {pos['unrealized_pnl_percent']:.2f}%)"
                    )
            else:
                console.print("No positions found.")
    except Exception as exc:
        logger.exception("Failed to fetch positions: %s", exc)
        console.print(f"[red]Error fetching positions: {exc}[/red]")


def run_cli() -> None:
    """Entrypoint for console script."""

    logging.basicConfig(level=logging.INFO)
    app()
