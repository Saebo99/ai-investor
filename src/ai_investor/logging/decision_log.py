"""Persistent logging utilities."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from ai_investor.config import get_settings


class JsonlLogger:
    """Append structured records to JSONL files."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict[str, Any]) -> None:
        enriched = {**record, "ts": datetime.utcnow().isoformat()}
        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(enriched) + "\n")


def thesis_logger() -> JsonlLogger:
    settings = get_settings()
    return JsonlLogger(Path(settings.thesis_storage_path))


def trade_logger() -> JsonlLogger:
    settings = get_settings()
    return JsonlLogger(Path(settings.trade_log_path))


def bulk_export(records: Iterable[dict[str, Any]], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
