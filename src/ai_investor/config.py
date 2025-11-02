"""Configuration helpers for the AI Investor server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final

from dotenv import load_dotenv


PACKAGE_ROOT: Final[Path] = Path(__file__).resolve().parent


def _infer_base_dir() -> Path:
    env_base = os.getenv("AI_INVESTOR_BASE_DIR")
    if env_base:
        candidate = Path(env_base).expanduser().resolve()
        if candidate.exists():
            return candidate

    # Try repository root (../../ from this file)
    repo_root = PACKAGE_ROOT.parent.parent
    if (repo_root / "data").exists() and (repo_root / "docs").exists():
        return repo_root

    # Fall back to package root (supports installs where data/docs are bundled alongside)
    if (PACKAGE_ROOT / "data").exists() and (PACKAGE_ROOT / "docs").exists():
        return PACKAGE_ROOT

    # Last resort: current working directory
    return Path.cwd()


BASE_DIR: Final[Path] = _infer_base_dir()
DATA_DIR: Final[Path] = Path(
    os.getenv("AI_INVESTOR_DATA_DIR", (BASE_DIR / "data"))
).expanduser()
DOCS_DIR: Final[Path] = Path(
    os.getenv("AI_INVESTOR_DOCS_DIR", (BASE_DIR / "docs"))
).expanduser()

# Load environment variables from an optional .env file near the detected base dir.
load_dotenv(BASE_DIR / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    fear_greed_endpoint: str = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
    http_timeout_seconds: float = 10.0
    tiingo_api_base: str = "https://api.tiingo.com"
    tiingo_api_token: str | None = None


DEFAULT_SETTINGS = Settings()


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings(
        fear_greed_endpoint=os.getenv(
            "FEAR_GREED_ENDPOINT", DEFAULT_SETTINGS.fear_greed_endpoint
        ),
        http_timeout_seconds=float(
            os.getenv("HTTP_TIMEOUT_SECONDS", DEFAULT_SETTINGS.http_timeout_seconds)
        ),
        tiingo_api_base=os.getenv("TIINGO_API_BASE", DEFAULT_SETTINGS.tiingo_api_base),
        tiingo_api_token=os.getenv("TIINGO_API_TOKEN", DEFAULT_SETTINGS.tiingo_api_token),
    )
