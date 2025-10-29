"""Simple SMTP email helper."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage
from typing import Iterable

from ai_investor.config import get_settings


def send_email(subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.email_smtp_server or not settings.email_from or not settings.email_recipients:
        return
    recipients: Iterable[str] = [
        email.strip() for email in settings.email_recipients.split(",") if email.strip()
    ]
    if not recipients:
        return
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.email_from
    message["To"] = ", ".join(recipients)
    message.set_content(body)
    with smtplib.SMTP(settings.email_smtp_server) as server:
        server.send_message(message)
