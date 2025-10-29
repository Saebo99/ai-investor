"""Human-in-the-loop approval via CLI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from rich.console import Console
from rich.table import Table

from ai_investor.decision.models import Thesis
from ai_investor.logging.decision_log import trade_logger

console = Console()


@dataclass
class ApprovalResult:
    thesis: Thesis
    approved: bool
    decision: str


class CliApprovalGateway:
    """Render thesis detail and request confirmation."""

    def __init__(self, input_fn: Callable[[str], str] | None = None) -> None:
        self._input = input_fn or input
        self._logger = trade_logger()

    def _render_thesis(self, thesis: Thesis) -> None:
        table = Table(title=f"Proposal for {thesis.ticker}")
        table.add_column("Metric")
        table.add_column("Value")
        table.add_row("Recommendation", thesis.recommendation.value)
        table.add_row("Conviction", f"{thesis.conviction:.2f}")
        table.add_row("Quantitative Score", f"{thesis.quantitative_score:.2f}")
        table.add_row("Qualitative Score", f"{thesis.qualitative_score:.2f}")
        table.add_row("Catalysts", "\n".join(thesis.catalysts) or "N/A")
        table.add_row("Risks", "\n".join(thesis.risks) or "N/A")
        console.print(table)
        console.print("Rationale:\n" + thesis.rationale)

        if thesis.insights:
            insights_table = Table(title="News Insights")
            insights_table.add_column("Headline")
            insights_table.add_column("Sentiment")
            insights_table.add_column("Summary")
            for item in thesis.insights:
                insights_table.add_row(item.headline, item.sentiment, item.summary)
            console.print(insights_table)

    def request(self, thesis: Thesis, proposed_order: Optional[dict] = None) -> ApprovalResult:
        self._render_thesis(thesis)
        if proposed_order:
            console.print(f"Proposed order: {proposed_order}")
        while True:
            response = self._input("Approve trade? (y/n/s): ").strip().lower()
            if response not in {"y", "n", "s"}:
                console.print("Enter y (approve), n (reject), or s (skip).")
                continue
            approved = response == "y"
            decision_label = {"y": "approved", "n": "rejected", "s": "skipped"}[response]
            self._logger.append(
                {
                    "ticker": thesis.ticker,
                    "recommendation": thesis.recommendation.value,
                    "conviction": thesis.conviction,
                    "decision": decision_label,
                    "proposed_order": proposed_order,
                }
            )
            return ApprovalResult(thesis=thesis, approved=approved, decision=decision_label)
