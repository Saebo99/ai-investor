"""Claude helper utilities."""

from __future__ import annotations

import logging
import json
from typing import Iterable, List

from anthropic import Anthropic

from ai_investor.config import get_settings

logger = logging.getLogger(__name__)


class ClaudeAnalyst:
    """Wrap Claude Agent SDK interactions for research tasks."""

    def __init__(self) -> None:
        settings = get_settings()
        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._model = "claude-3-5-sonnet-latest"

    def summarize_news(self, ticker: str, articles: Iterable[dict]) -> List[dict]:
        """Ask Claude to cluster recent articles into narrative insights."""

        articles_payload = [
            {
                "headline": article.get("title"),
                "summary": article.get("summary"),
                "sentiment": article.get("sentiment", "neutral"),
                "url": article.get("link"),
            }
            for article in articles
        ]
        if not articles_payload:
            return []
        logger.debug("Requesting Claude summary for %s (%d articles)", ticker, len(articles_payload))
        message = self._client.messages.create(
            model=self._model,
            max_tokens=800,
            system="You are an equity analyst producing concise investment insights.",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Summarise the following recent stories about {ticker} into 3 bullet "+
                                "points with sentiment (positive/neutral/negative) and highlight "+
                                "implications for long-term investors. Respond as JSON with fields "+
                                "headline, sentiment, summary, catalyst, risk."
                            ).format(ticker=ticker),
                        },
                        {
                            "type": "json",
                            "json": {"articles": articles_payload},
                        },
                    ],
                }
            ],
        )
        try:
            if not message.content:
                return []
            first_block = message.content[0]
            response_text = getattr(first_block, "text", "")
            parsed = json.loads(response_text)
            insights = parsed if isinstance(parsed, list) else parsed.get("insights", [])
            filtered = []
            for item in insights:
                if not isinstance(item, dict):
                    continue
                filtered.append(
                    {
                        "headline": item.get("headline", ""),
                        "sentiment": item.get("sentiment", "neutral"),
                        "summary": item.get("summary", ""),
                        "catalyst": item.get("catalyst"),
                        "risk": item.get("risk"),
                    }
                )
            return filtered
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to parse Claude response for %s: %s", ticker, exc)
            return []
