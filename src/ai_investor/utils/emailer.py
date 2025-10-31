"""Simple SMTP email helper."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Iterable

from ai_investor.config import get_settings

logger = logging.getLogger(__name__)


def send_email(subject: str, body: str) -> None:
    """Send email via SMTP with proper logging and error handling."""
    settings = get_settings()
    
    # Check if email is configured
    if not settings.email_smtp_server or not settings.email_from or not settings.email_recipients:
        logger.warning(
            "Email not configured (smtp_server=%s, from=%s, recipients=%s). Skipping email.",
            settings.email_smtp_server,
            settings.email_from,
            settings.email_recipients,
        )
        return
    
    recipients: Iterable[str] = [
        email.strip() for email in settings.email_recipients.split(",") if email.strip()
    ]
    if not recipients:
        logger.warning("No valid email recipients configured. Skipping email.")
        return
    
    try:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.email_from
        message["To"] = ", ".join(recipients)
        message.set_content(body)
        
        with smtplib.SMTP(settings.email_smtp_server) as server:
            server.send_message(message)
        
        logger.info(
            "Email sent successfully: subject='%s' to %d recipient(s)", 
            subject, 
            len(list(recipients))
        )
    except smtplib.SMTPException as exc:
        logger.error("SMTP error sending email: %s", exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error sending email: %s", exc)
        raise
