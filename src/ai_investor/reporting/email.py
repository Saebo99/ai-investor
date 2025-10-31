"""
Generate and send email reports summarizing investment decisions.
"""

from __future__ import annotations

from typing import Iterable

from ..analysis import InvestmentDecision
from ..config import get_settings


class EmailReport:
    """
    Placeholder email reporting workflow.
    """

    def __init__(self) -> None:
        self.settings = get_settings()

    def render(self, decisions: Iterable[InvestmentDecision]) -> str:
        """
        Render a plain-text email body summarizing the decisions.
        """
        lines = [
            "AI Investor Report",
            "==================",
            "",
            "Decisions:",
        ]
        for decision in decisions:
            lines.append(
                f"- {decision.ticker}: {decision.action} ({decision.weight_delta:+.2%})"
            )
            lines.append(f"  Reason: {decision.rationale}")
        lines.append("")
        lines.append(f"Recipient: {self.settings.agent.report_recipient}")
        return "\n".join(lines)

    async def send(self, decisions: Iterable[InvestmentDecision]) -> None:
        """
        Stub for sending the report via email service.
        """
        # TODO: Integrate with email provider (e.g., SES, SendGrid).
        _ = self.render(decisions)
